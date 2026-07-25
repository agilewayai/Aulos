"""Ambient media cache + reverse-proxy (SSRF-guarded allowlist).

Two delivery modes for clients behind blocked upstream CDNs:
- cache: serve a local disk copy (warmed on first fetch / prefetch)
- proxy: stream bytes through this API while optionally filling the cache
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
from pathlib import Path
from urllib.parse import urlparse

import httpx

from aulos_api.config import get_settings

logger = logging.getLogger("aulos_api.media")

ALLOWED_HOST_SUFFIXES = (
    "upload.wikimedia.org",
    "commons.wikimedia.org",
    "wikimedia.org",
    "archive.org",
    "purezen.ai",
)

_AUDIO_EXT = {".ogg", ".oga", ".opus", ".mp3", ".m4a", ".aac", ".wav", ".flac", ".webm"}
_MAX_BYTES = 45 * 1024 * 1024
_FETCH_TIMEOUT = 60.0
_prefetch_lock = threading.Lock()
_prefetched: set[str] = set()


def media_cache_dir() -> Path:
    settings = get_settings()
    raw = getattr(settings, "media_cache_dir", "") or ""
    path = Path(raw) if raw else Path("data/media-cache")
    if not path.is_absolute():
        # Prefer next to API package data/
        path = Path.cwd() / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def host_allowed(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:  # noqa: BLE001
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        return False
    if re.match(r"^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)", host):
        return False
    return any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_HOST_SUFFIXES)


def _ext_for(url: str, content_type: str = "") -> str:
    path = urlparse(url).path.lower()
    for ext in _AUDIO_EXT:
        if path.endswith(ext):
            return ext
    ct = (content_type or "").lower()
    if "ogg" in ct or "opus" in ct:
        return ".ogg"
    if "mpeg" in ct or "mp3" in ct:
        return ".mp3"
    if "mp4" in ct or "m4a" in ct or "aac" in ct:
        return ".m4a"
    if "wav" in ct:
        return ".wav"
    if "flac" in ct:
        return ".flac"
    return ".bin"


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:40]


def cache_path_for(url: str, *, ext: str | None = None) -> Path:
    key = cache_key(url)
    suffix = ext or _ext_for(url)
    return media_cache_dir() / f"{key}{suffix}"


def find_cached(url: str) -> Path | None:
    key = cache_key(url)
    root = media_cache_dir()
    matches = list(root.glob(f"{key}.*"))
    for path in matches:
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def content_type_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".ogg": "audio/ogg",
        ".oga": "audio/ogg",
        ".opus": "audio/ogg",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
    }.get(ext, "application/octet-stream")


def validate_source_url(url: str) -> str:
    url = (url or "").strip()
    if not url or len(url) > 2000:
        raise ValueError("invalid media url")
    if not host_allowed(url):
        raise ValueError("media host not allowlisted")
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        raise ValueError("credentials in url not allowed")
    return url


def fetch_into_cache(url: str) -> Path:
    """Download remote audio into local cache (idempotent)."""
    url = validate_source_url(url)
    existing = find_cached(url)
    if existing is not None:
        return existing

    headers = {"User-Agent": "AulosMediaCache/0.1 (+https://aulos.purezen.ai)"}
    with httpx.Client(timeout=_FETCH_TIMEOUT, follow_redirects=True, headers=headers) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "")
            ext = _ext_for(url, ctype)
            dest = cache_path_for(url, ext=ext)
            tmp = dest.with_suffix(dest.suffix + ".part")
            total = 0
            with tmp.open("wb") as fh:
                for chunk in resp.iter_bytes(64 * 1024):
                    total += len(chunk)
                    if total > _MAX_BYTES:
                        fh.close()
                        tmp.unlink(missing_ok=True)
                        raise ValueError("media too large")
                    fh.write(chunk)
            tmp.replace(dest)
            logger.info("media_cached url=%s bytes=%s path=%s", url, total, dest.name)
            return dest


def ensure_cached(url: str) -> Path | None:
    try:
        return fetch_into_cache(url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("media_cache_failed url=%s err=%s", url, exc)
        return None


def prefetch_urls(urls: list[str]) -> int:
    """Best-effort warm cache for known ambient assets."""
    ok = 0
    for url in urls:
        url = (url or "").strip()
        if not url:
            continue
        with _prefetch_lock:
            if url in _prefetched and find_cached(url) is not None:
                continue
            _prefetched.add(url)
        path = ensure_cached(url)
        if path is not None:
            ok += 1
    return ok


_CORPUS_AUDIO_RE = re.compile(
    r"https://(?:upload\.wikimedia\.org/[^\s\"']+\.(?:ogg|oga|opus|mp3|m4a|wav|flac)"
    r"|commons\.wikimedia\.org/wiki/Special:FilePath/[^\s\"']+"
    r"|archive\.org/[^\s\"']+\.(?:ogg|oga|opus|mp3|m4a|wav|flac))"
    r"(?:\?[^\s\"']*)?",
    re.I,
)


def discover_corpus_audio_urls() -> list[str]:
    roots = [
        Path(__file__).resolve().parents[4] / "aulos-skills" / "skills" / "aulos-listening-corpus" / "assets" / "corpus",
        Path.cwd().parent / "aulos-skills" / "skills" / "aulos-listening-corpus" / "assets" / "corpus",
    ]
    found: list[str] = []
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".yaml", ".yml", ".md"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for match in _CORPUS_AUDIO_RE.findall(text):
                if match not in seen and host_allowed(match):
                    seen.add(match)
                    found.append(match)
    return found


def proxy_url_for(origin: str, *, mode: str = "cache") -> str:
    from urllib.parse import quote

    mode = mode if mode in {"cache", "proxy"} else "cache"
    return f"/v1/media/audio?src={quote(origin, safe='')}&mode={mode}"
