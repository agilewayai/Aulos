"""Search-link helpers for listening-room media (YouTube / 哔哩哔哩 / Discogs).

No composer/work hardcoding — callers pass dynamic query text from dossier fields.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, quote, urlparse


def bilibili_search_url(query: str) -> str:
    q = " ".join((query or "").split())
    if not q:
        return ""
    return f"https://search.bilibili.com/all?keyword={quote(q)}"


def youtube_search_url(query: str) -> str:
    q = " ".join((query or "").split())
    if not q:
        return ""
    return f"https://www.youtube.com/results?search_query={quote(q)}"


def query_from_youtube_search_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
        host = (parsed.netloc or "").lower()
        if "youtube.com" not in host and "youtu.be" not in host:
            return ""
        qs = parse_qs(parsed.query)
        values = qs.get("search_query") or []
        if values and str(values[0]).strip():
            return str(values[0]).strip()
    except Exception:  # noqa: BLE001
        return ""
    return ""


def _fallback_query(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p and str(p).strip())


def enrich_appreciation_video(
    video: dict[str, Any],
    *,
    work_title: str = "",
    composer: str = "",
) -> dict[str, Any]:
    """Ensure a video row has a Bilibili search link (and keep existing YouTube url)."""
    out = dict(video)
    title = str(out.get("title") or "").strip()
    url = str(out.get("url") or "").strip()
    bili = str(out.get("bilibili_url") or "").strip()
    if not bili:
        q = query_from_youtube_search_url(url) or title or _fallback_query(composer, work_title)
        bili = bilibili_search_url(q)
        if bili:
            out["bilibili_url"] = bili
    if not url:
        q = title or _fallback_query(composer, work_title)
        yt = youtube_search_url(q)
        if yt:
            out["url"] = yt
    return out


def enrich_interpretation_links(
    item: dict[str, Any],
    *,
    work_title: str = "",
    composer: str = "",
) -> dict[str, Any]:
    """Add bilibili_url next to youtube when missing."""
    out = dict(item)
    if str(out.get("bilibili_url") or "").strip():
        return out
    artist = str(out.get("artist") or "").strip()
    year = str(out.get("year") or "").strip()
    yt = str(out.get("youtube_url") or "").strip()
    q = (
        query_from_youtube_search_url(yt)
        or _fallback_query(artist, work_title, year)
        or _fallback_query(composer, work_title, artist)
    )
    bili = bilibili_search_url(q)
    if bili:
        out["bilibili_url"] = bili
    return out
