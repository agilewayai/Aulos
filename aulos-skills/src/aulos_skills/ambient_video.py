"""Video-platform ambient fallback — official embed or optional yt-dlp stream.

OPS `listening.ambient_fallback_mode`: embed (default) | stream.
Never blind-embeds search-result pages; concrete video ids only.
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

FALLBACK_EMBED = "embed"
FALLBACK_STREAM = "stream"
VALID_FALLBACK_MODES = frozenset({FALLBACK_EMBED, FALLBACK_STREAM})

_YT_HOSTS = ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be")
_BILI_HOSTS = ("bilibili.com", "www.bilibili.com", "m.bilibili.com", "player.bilibili.com")

# Short-lived stream URL cache (yt-dlp results expire).
_STREAM_CACHE: dict[str, tuple[float, str]] = {}
_STREAM_TTL_SEC = 25 * 60

ExtractFn = Callable[[str], dict[str, Any] | None]


def normalize_fallback_mode(raw: str | None) -> str:
    mode = str(raw or FALLBACK_EMBED).strip().lower()
    return mode if mode in VALID_FALLBACK_MODES else FALLBACK_EMBED


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def parse_video_ref(url: str) -> dict[str, str] | None:
    """Return {platform, video_id, watch_url} for concrete watch/embed URLs; else None."""
    raw = str(url or "").strip()
    if not raw or "results?search_query=" in raw or "search.bilibili.com" in raw:
        return None
    host = _host(raw)
    parsed = urlparse(raw)

    if host in _YT_HOSTS or "youtube.com" in host:
        vid = ""
        if host in ("youtu.be", "www.youtu.be"):
            vid = parsed.path.strip("/").split("/")[0]
        elif "/embed/" in parsed.path:
            vid = parsed.path.split("/embed/")[-1].split("/")[0]
        else:
            vid = (parse_qs(parsed.query).get("v") or [""])[0]
        vid = re.sub(r"[^A-Za-z0-9_-]", "", vid)[:11]
        if len(vid) == 11:
            return {
                "platform": "youtube",
                "video_id": vid,
                "watch_url": f"https://www.youtube.com/watch?v={vid}",
            }
        return None

    if host in _BILI_HOSTS or "bilibili.com" in host:
        qs = parse_qs(parsed.query)
        bvid = (qs.get("bvid") or [""])[0]
        if not bvid:
            m = re.search(r"(BV[\w]+)", raw, re.I)
            if m:
                bvid = m.group(1)
        if bvid and re.match(r"^BV[\w]+$", bvid, re.I):
            return {
                "platform": "bilibili",
                "video_id": bvid,
                "watch_url": f"https://www.bilibili.com/video/{bvid}",
            }
        av = re.search(r"/video/av(\d+)", raw, re.I)
        if av:
            avid = av.group(1)
            return {
                "platform": "bilibili",
                "video_id": f"av{avid}",
                "watch_url": f"https://www.bilibili.com/video/av{avid}",
            }
        return None

    return None


def embed_src_for(*, platform: str, video_id: str) -> str:
    if platform == "youtube":
        return f"https://www.youtube.com/embed/{video_id}"
    if platform == "bilibili":
        if video_id.lower().startswith("av"):
            aid = video_id[2:]
            return f"https://player.bilibili.com/player.html?aid={aid}&autoplay=0"
        return f"https://player.bilibili.com/player.html?bvid={video_id}&autoplay=0"
    return ""


def collect_video_candidates(
    *lists: list[Any] | None,
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for blob in lists:
        for item in blob or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("name") or "").strip()
            for key in ("url", "youtube_url", "bilibili_url", "watch_url", "href"):
                ref = parse_video_ref(str(item.get(key) or ""))
                if not ref:
                    continue
                token = f"{ref['platform']}:{ref['video_id']}"
                if token in seen:
                    continue
                seen.add(token)
                row = dict(ref)
                if title:
                    row["title"] = title
                out.append(row)
    return out


def _prefer_order(candidates: list[dict[str, str]], *, prefer_zh: bool) -> list[dict[str, str]]:
    if not candidates:
        return []
    primary = "bilibili" if prefer_zh else "youtube"
    secondary = "youtube" if prefer_zh else "bilibili"
    first = [c for c in candidates if c.get("platform") == primary]
    second = [c for c in candidates if c.get("platform") == secondary]
    rest = [c for c in candidates if c.get("platform") not in {primary, secondary}]
    return first + second + rest


def _cache_get(key: str) -> str | None:
    row = _STREAM_CACHE.get(key)
    if not row:
        return None
    ts, url = row
    if time.time() - ts > _STREAM_TTL_SEC:
        _STREAM_CACHE.pop(key, None)
        return None
    return url


def _cache_put(key: str, url: str) -> None:
    _STREAM_CACHE[key] = (time.time(), url)


def default_yt_dlp_extract(url_or_query: str) -> dict[str, Any] | None:
    """Optional dependency — returns {id, title, webpage_url, url, extractor}."""
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        return None
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "bestaudio/best",
        "noplaylist": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url_or_query, download=False)
    except Exception:
        return None
    if not isinstance(info, dict):
        return None
    # ytsearch returns playlist entries
    if info.get("entries"):
        entries = [e for e in info["entries"] if isinstance(e, dict)]
        info = entries[0] if entries else None
        if not info:
            return None
    audio = str(info.get("url") or "").strip()
    vid = str(info.get("id") or "").strip()
    webpage = str(info.get("webpage_url") or info.get("original_url") or "").strip()
    title = str(info.get("title") or "").strip()
    extractor = str(info.get("extractor_key") or info.get("extractor") or "").lower()
    platform = "bilibili" if "bili" in extractor else "youtube"
    if not vid and webpage:
        parsed = parse_video_ref(webpage)
        if parsed:
            vid = parsed["video_id"]
            platform = parsed["platform"]
            webpage = parsed["watch_url"]
    if not vid:
        return None
    return {
        "platform": platform,
        "video_id": vid,
        "watch_url": webpage or "",
        "title": title,
        "audio_stream_url": audio,
    }


def _search_query(composer: str, work_title: str) -> str:
    parts = [p for p in (composer.strip(), work_title.strip()) if p]
    return " ".join(parts) if parts else work_title or composer


def resolve_ambient_video(
    *,
    composer: str = "",
    work_title: str = "",
    appreciation_videos: list[Any] | None = None,
    interpretations: list[Any] | None = None,
    fallback_mode: str = FALLBACK_EMBED,
    prefer_zh: bool = False,
    extract_fn: ExtractFn | None = None,
    allow_search: bool = True,
) -> dict[str, Any]:
    """Resolve embed or stream ambient payload; {} when nothing usable."""
    mode = normalize_fallback_mode(fallback_mode)
    extract = extract_fn if extract_fn is not None else default_yt_dlp_extract

    candidates = _prefer_order(
        collect_video_candidates(appreciation_videos, interpretations),
        prefer_zh=prefer_zh,
    )
    pick = dict(candidates[0]) if candidates else None

    if pick is None and allow_search:
        q = _search_query(composer, work_title)
        if q:
            # Prefer platform-native search when stream/embed needs a concrete id.
            if prefer_zh:
                queries = [f"ytsearch1:{q}", f"bilisearch1:{q}"]
            else:
                queries = [f"ytsearch1:{q}", f"bilisearch1:{q}"]
            for query in queries:
                found = extract(query)
                if found and found.get("video_id"):
                    pick = {
                        "platform": str(found.get("platform") or "youtube"),
                        "video_id": str(found["video_id"]),
                        "watch_url": str(found.get("watch_url") or ""),
                        "title": str(found.get("title") or ""),
                    }
                    if found.get("audio_stream_url"):
                        pick["_audio_stream_url"] = str(found["audio_stream_url"])
                    break

    if not pick or not pick.get("video_id"):
        return {}

    platform = str(pick["platform"])
    video_id = str(pick["video_id"])
    watch_url = str(pick.get("watch_url") or "")
    title = str(pick.get("title") or f"{composer} — {work_title}".strip(" —"))
    embed_src = embed_src_for(platform=platform, video_id=video_id)
    if not embed_src:
        return {}

    platform_label = "Bilibili" if platform == "bilibili" else "YouTube"
    why = (
        f"No work-matched openly licensed recording; using {platform_label} "
        f"{'audio stream' if mode == FALLBACK_STREAM else 'official embed'}."
    )
    why_zh = (
        f"本作品无匹配公开授权录音；使用{platform_label}"
        f"{'服务端抽流' if mode == FALLBACK_STREAM else '官方 Embed'}。"
    )

    if mode == FALLBACK_STREAM:
        cache_key = f"{platform}:{video_id}"
        audio_url = str(pick.get("_audio_stream_url") or "") or _cache_get(cache_key) or ""
        if not audio_url:
            target = watch_url or (
                f"https://www.youtube.com/watch?v={video_id}"
                if platform == "youtube"
                else f"https://www.bilibili.com/video/{video_id}"
            )
            extracted = extract(target)
            if extracted and extracted.get("audio_stream_url"):
                audio_url = str(extracted["audio_stream_url"])
                _cache_put(cache_key, audio_url)
                if extracted.get("title"):
                    title = str(extracted["title"])
        if audio_url:
            return {
                "mode": "audio",
                "url": audio_url,
                "title": title,
                "title_zh": title,
                "credit": f"{platform_label} stream (ops)",
                "credit_zh": f"{platform_label} 抽流（运维开关）",
                "why": why,
                "why_zh": why_zh,
                "volume": 0.28,
                "autoplay": True,
                "loop": True,
                "selection_source": "video-stream",
                "selection_id": f"{platform}:{video_id}",
                "platform": platform,
                "video_id": video_id,
                "watch_url": watch_url,
                "embed_src": embed_src,
            }
        # Degrade to embed when extract fails but id is known.
        mode = FALLBACK_EMBED
        why = (
            f"No work-matched openly licensed recording; stream extract failed — "
            f"falling back to {platform_label} official embed."
        )
        why_zh = f"本作品无匹配公开授权录音；抽流失败，回退{platform_label}官方 Embed。"

    return {
        "mode": "embed",
        "embed_src": embed_src,
        "title": title,
        "title_zh": title,
        "credit": f"{platform_label} embed",
        "credit_zh": f"{platform_label} Embed",
        "why": why,
        "why_zh": why_zh,
        "volume": 0.28,
        "selection_source": "video-embed",
        "selection_id": f"{platform}:{video_id}",
        "platform": platform,
        "video_id": video_id,
        "watch_url": watch_url,
    }
