"""Resolve ambient playlist packs into playable track lists."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml


def playlist_dir(corpus_dir: Path) -> Path:
    return corpus_dir / "playlists"


def load_playlist_pack(corpus_dir: Path, playlist_id: str) -> dict[str, Any]:
    path = playlist_dir(corpus_dir) / f"{playlist_id}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def resolve_ambient_audio(ambient: dict[str, Any], *, corpus_dir: Path | None = None) -> dict[str, Any]:
    """Expand playlist_id / tracks into a normalized ambient_audio dict."""
    out = dict(ambient or {})
    tracks_in = list(out.get("tracks") or [])
    pack: dict[str, Any] = {}
    playlist_id = str(out.get("playlist_id") or "").strip()
    if playlist_id and corpus_dir is not None:
        pack = load_playlist_pack(corpus_dir, playlist_id)
        if pack:
            if not out.get("credit") and pack.get("credit"):
                out["credit"] = pack.get("credit")
            if not out.get("credit_zh") and pack.get("credit_zh"):
                out["credit_zh"] = pack.get("credit_zh")
            if "loop_playlist" not in out and "loop_playlist" in pack:
                out["loop_playlist"] = pack.get("loop_playlist")
            if not tracks_in:
                tracks_in = list(pack.get("tracks") or [])

    base = str(pack.get("base_url") or out.get("base_url") or "").rstrip("/")
    if base and not base.endswith("/"):
        base = base + "/"

    tracks: list[dict[str, Any]] = []
    for raw in tracks_in:
        if not isinstance(raw, dict):
            continue
        url = str(raw.get("url") or "").strip()
        file_name = str(raw.get("file") or "").strip()
        if not url and file_name and base:
            url = f"{base}{file_name}"
        if not url:
            continue
        title = str(raw.get("title") or file_name or f"Track {len(tracks) + 1}")
        title_zh = str(raw.get("title_zh") or title)
        n = raw.get("n")
        try:
            index = int(n) if n is not None else len(tracks) + 1
        except (TypeError, ValueError):
            index = len(tracks) + 1
        encoded = quote(url, safe="")
        tracks.append(
            {
                "n": index,
                "id": str(raw.get("id") or f"t{index}"),
                "title": title,
                "title_zh": title_zh,
                "url": url,
                "cache_src": f"/v1/media/audio?src={encoded}&mode=cache",
                "proxy_src": f"/v1/media/audio?src={encoded}&mode=proxy",
            }
        )

    if tracks:
        out["tracks"] = tracks
        out["mode"] = "playlist"
        out["loop_playlist"] = bool(out.get("loop_playlist", True))
        # Single-track loop off when playlist advances on ended
        out["loop"] = False
        first = tracks[0]
        out.setdefault("url", first["url"])
        out.setdefault("title", first["title"])
        out.setdefault("title_zh", first["title_zh"])
    else:
        out.setdefault("mode", "single")
        url = str(out.get("url") or "").strip()
        file_name = str(out.get("file") or "").strip()
        if not url and file_name:
            file_base = base or "https://commons.wikimedia.org/wiki/Special:FilePath/"
            if not file_base.endswith("/"):
                file_base += "/"
            url = f"{file_base}{file_name}"
            out["url"] = url
        if url:
            encoded = quote(url, safe="")
            out.setdefault("cache_src", f"/v1/media/audio?src={encoded}&mode=cache")
            out.setdefault("proxy_src", f"/v1/media/audio?src={encoded}&mode=proxy")
    return out
