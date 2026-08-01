"""Adaptive ambient-music agent — work-matched curated/catalog-ref → video fallback.

Identity-aware: conflict_markers scrub alien curated (SPEC-006 / REQ-005).
No related/defaults library rotation. No work-proper-name special cases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from aulos_skills.ambient_playlist import resolve_ambient_audio
from aulos_skills.ambient_video import normalize_fallback_mode, resolve_ambient_video

_STANDIN_WHY_MARKERS = (
    "peer",
    "stand-in",
    "stand in",
    "atmosphere",
    "关联",
    "尚无",
    "open library",
    "公开授权库",
    "library rotation",
    "备用库",
    "defaults",
    "related pack",
)


def _library_path(corpus_dir: Path | None) -> Path | None:
    if corpus_dir is None:
        return None
    path = corpus_dir / "ambient-library.yaml"
    return path if path.is_file() else None


def load_ambient_library(corpus_dir: Path | None) -> dict[str, Any]:
    path = _library_path(corpus_dir)
    if path is None:
        return {"base_url": "", "related": [], "defaults": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {"related": [], "defaults": []}


def _entry_to_ambient(entry: dict[str, Any], *, base_url: str, corpus_dir: Path | None) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "title": entry.get("title"),
        "title_zh": entry.get("title_zh"),
        "credit": entry.get("credit"),
        "credit_zh": entry.get("credit_zh"),
        "why": entry.get("why"),
        "why_zh": entry.get("why_zh"),
        "volume": entry.get("volume", 0.28),
        "autoplay": True,
        "loop": True,
    }
    if entry.get("playlist_id"):
        raw["playlist_id"] = entry["playlist_id"]
        raw["loop_playlist"] = True
        raw["loop"] = False
    if entry.get("url"):
        raw["url"] = entry["url"]
    elif entry.get("file") and base_url:
        base = base_url if base_url.endswith("/") else base_url + "/"
        raw["url"] = f"{base}{entry['file']}"
    if entry.get("tracks"):
        raw["tracks"] = list(entry["tracks"])
    resolved = resolve_ambient_audio(raw, corpus_dir=corpus_dir)
    resolved["selection_id"] = str(entry.get("id") or "")
    resolved["selection_source"] = str(entry.get("_source") or "catalog-ref")
    # Preserve playlist mode when tracks expanded (SPEC-006 / catalog ambient_ref).
    if resolved.get("tracks"):
        resolved["mode"] = "playlist"
    else:
        resolved["mode"] = str(resolved.get("mode") or "audio")
    if entry.get("why"):
        resolved["why"] = entry["why"]
    if entry.get("why_zh"):
        resolved["why_zh"] = entry["why_zh"]
    return resolved


def ambient_conflicts_markers(*, ambient: dict[str, Any], conflict_markers: list[str]) -> bool:
    """True when ambient blob contains any catalog-derived conflict marker."""
    if not ambient or not conflict_markers:
        return False
    amb_blob = json.dumps(ambient, ensure_ascii=False).lower()
    return any(len(m) >= 3 and m.lower() in amb_blob for m in conflict_markers)


def _is_standin_curated(ambient: dict[str, Any]) -> bool:
    why_blob = f"{ambient.get('why') or ''} {ambient.get('why_zh') or ''}".lower()
    src = str(ambient.get("selection_source") or "").lower()
    if src in {"related", "default", "video-embed", "video-stream"}:
        return src in {"related", "default"}
    return any(w in why_blob for w in _STANDIN_WHY_MARKERS)


def select_ambient(
    *,
    work_title: str = "",
    composer: str = "",
    era: str = "",
    form: str = "",
    family_hints: list[str] | None = None,
    facets: dict[str, Any] | None = None,
    ambient_ref: str | None = None,
    conflict_markers: list[str] | None = None,
    existing: dict[str, Any] | None = None,
    corpus_dir: Path | None = None,
    fallback_mode: str | None = None,
    appreciation_videos: list[Any] | None = None,
    interpretations: list[Any] | None = None,
    prefer_zh: bool = False,
    video_extract_fn: Any | None = None,
    allow_video_search: bool = True,
) -> dict[str, Any]:
    """Pick ambient: catalog-ref → work-matched curated → video fallback → {}."""
    del era, form, family_hints, facets  # retained for call-site compatibility
    markers = [str(m).lower() for m in (conflict_markers or []) if m]
    mode = normalize_fallback_mode(fallback_mode)

    lib = load_ambient_library(corpus_dir)
    base_url = str(lib.get("base_url") or "")

    # 1) Explicit catalog ambient_ref — work-bound catalog authority only.
    if ambient_ref:
        for entry in list(lib.get("related") or []) + list(lib.get("defaults") or []):
            if not isinstance(entry, dict):
                continue
            if str(entry.get("id") or "") == ambient_ref:
                if ambient_conflicts_markers(ambient=entry, conflict_markers=markers):
                    break
                pick = dict(entry)
                pick["_source"] = "catalog-ref"
                return _entry_to_ambient(pick, base_url=base_url, corpus_dir=corpus_dir)

    # 2) Curated on dossier — keep work-matched open recordings; scrub stand-ins.
    existing_resolved = resolve_ambient_audio(dict(existing or {}), corpus_dir=corpus_dir)
    has_audio = bool(existing_resolved.get("tracks") or existing_resolved.get("url"))
    has_embed = bool(existing_resolved.get("embed_src") or (existing or {}).get("embed_src"))
    if has_audio or has_embed:
        candidate = dict(existing_resolved)
        if has_embed and not has_audio:
            candidate.setdefault("embed_src", (existing or {}).get("embed_src"))
            candidate.setdefault("mode", (existing or {}).get("mode") or "embed")
        if _is_standin_curated(candidate) or ambient_conflicts_markers(
            ambient=candidate, conflict_markers=markers
        ):
            pass  # discard → video fallback
        else:
            out = dict(candidate)
            out.setdefault("selection_source", "curated")
            if out.get("tracks"):
                out["mode"] = "playlist"
            else:
                out.setdefault(
                    "mode",
                    "embed" if out.get("embed_src") and not out.get("url") else "audio",
                )
            if not out.get("why"):
                out["why"] = "Curated open recording packaged with this listening guide."
                out["why_zh"] = "本导赏附带的公开授权录音／曲目列表。"
            return out

    # 3) related / defaults library rotation — disabled (REQ-005).

    # 4) Video-platform fallback (OPS mode).
    video = resolve_ambient_video(
        composer=composer,
        work_title=work_title,
        appreciation_videos=appreciation_videos,
        interpretations=interpretations,
        fallback_mode=mode,
        prefer_zh=prefer_zh,
        extract_fn=video_extract_fn,
        allow_search=allow_video_search,
    )
    if not video:
        return {}
    if video.get("mode") == "audio" and video.get("url"):
        resolved = resolve_ambient_audio(dict(video), corpus_dir=corpus_dir)
        for key in (
            "selection_source",
            "selection_id",
            "platform",
            "video_id",
            "watch_url",
            "embed_src",
            "mode",
            "why",
            "why_zh",
        ):
            if video.get(key) is not None:
                resolved[key] = video[key]
        return resolved
    return video
