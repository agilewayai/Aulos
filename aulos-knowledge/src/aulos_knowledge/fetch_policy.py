"""Fetch URL allowlist + rate helpers (REQ-008 / ADR-006)."""

from __future__ import annotations

import json
import time
from urllib.parse import urlparse

from aulos_knowledge.db import SourceAuthority


class FetchPolicyError(ValueError):
    """URL or source policy violation."""


def registered_base_urls(source: SourceAuthority) -> list[str]:
    try:
        bases = json.loads(source.base_urls_json or "[]")
    except json.JSONDecodeError:
        bases = []
    try:
        paths = json.loads(source.allowed_path_prefixes_json or "[]")
    except json.JSONDecodeError:
        paths = []
    out: list[str] = []
    for b in list(bases or []) + list(paths or []):
        s = str(b).strip()
        if s:
            out.append(s)
    return out


def url_allowed(source: SourceAuthority, url: str) -> bool:
    bases = registered_base_urls(source)
    if not bases:
        return False
    raw = (url or "").strip()
    if not raw:
        return False
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        return False
    for base in bases:
        norm = base if "://" in base else f"https://{base}"
        b = urlparse(norm)
        if not b.netloc:
            continue
        if parsed.netloc.lower() != b.netloc.lower():
            continue
        base_path = b.path or "/"
        if base_path in {"", "/"}:
            return True
        path = parsed.path or "/"
        if path == base_path.rstrip("/") or path.startswith(
            base_path if base_path.endswith("/") else base_path + "/"
        ):
            return True
        if raw.startswith(norm.rstrip("/")):
            return True
    return False


def assert_url_allowed(source: SourceAuthority, url: str) -> None:
    if not url_allowed(source, url):
        raise FetchPolicyError(
            f"url not allowed for source {source.id}: {url} (bases={registered_base_urls(source)})"
        )


def throttle(source: SourceAuthority) -> None:
    qps = float(source.rate_limit_qps or 1.0)
    if qps <= 0:
        return
    time.sleep(max(0.0, 1.0 / qps))
