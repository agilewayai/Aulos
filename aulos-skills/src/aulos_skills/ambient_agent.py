"""Adaptive ambient-music agent — curated → related → default rotation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from aulos_skills.ambient_playlist import resolve_ambient_audio


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
    resolved["selection_source"] = str(entry.get("_source") or "related")
    if entry.get("why"):
        resolved["why"] = entry["why"]
    if entry.get("why_zh"):
        resolved["why_zh"] = entry["why_zh"]
    return resolved


def _score_related(entry: dict[str, Any], *, blob: str, composer: str, peers_blob: str) -> int:
    score = 0
    composers = [str(x).lower() for x in (entry.get("composers") or [])]
    eras = [str(x).lower() for x in (entry.get("eras") or [])]
    forms = [str(x).lower() for x in (entry.get("forms") or [])]
    peers = [str(x).lower() for x in (entry.get("peers") or [])]
    instruments = [str(x).lower() for x in (entry.get("instruments") or [])]
    weight = int(entry.get("weight") or 5)

    composer_hit = any(c and c in composer for c in composers) or any(c and c in blob for c in composers)
    if composer_hit:
        score += 40
    era_hit = any(e and e in blob for e in eras)
    if era_hit:
        score += 12
    form_hit = any(f and f in blob for f in forms)
    if form_hit:
        score += 14
    # Instrument tokens (cello, piano…) — critical for duo / solo-timbre matching
    instrument_hit = any(i and i in blob for i in instruments) or any(
        i and i in blob for i in forms if i in {"cello", "violoncello", "大提琴", "violin", "钢琴", "piano", "keyboard"}
    )
    if instrument_hit:
        score += 22
    peer_hit = any(p and p in peers_blob for p in peers) or any(p and p in blob for p in peers)
    if peer_hit and not composer_hit:
        score += 18
    if score <= 0:
        return 0
    return score + weight


def select_ambient(
    *,
    work_title: str = "",
    composer: str = "",
    era: str = "",
    form: str = "",
    family_hints: list[str] | None = None,
    existing: dict[str, Any] | None = None,
    corpus_dir: Path | None = None,
) -> dict[str, Any]:
    """Pick ambient audio: curated work pack → related → default rotation."""
    existing_resolved = resolve_ambient_audio(dict(existing or {}), corpus_dir=corpus_dir)
    if existing_resolved.get("tracks") or existing_resolved.get("url"):
        out = dict(existing_resolved)
        out.setdefault("selection_source", "curated")
        if not out.get("why"):
            out["why"] = "Curated open recording packaged with this listening guide."
            out["why_zh"] = "本导赏附带的公开授权录音／曲目列表。"
        return out

    lib = load_ambient_library(corpus_dir)
    base_url = str(lib.get("base_url") or "")
    hints = list(family_hints or [])
    blob = " ".join(
        str(x) for x in [composer, work_title, era, form, *hints] if x
    ).lower()
    peers_blob = blob
    composer_l = (composer or "").lower()

    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in lib.get("related") or []:
        if not isinstance(entry, dict):
            continue
        score = _score_related(entry, blob=blob, composer=composer_l, peers_blob=peers_blob)
        if score > 0:
            scored.append((score, entry))
    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        best = dict(scored[0][1])
        best["_source"] = "related"
        return _entry_to_ambient(best, base_url=base_url, corpus_dir=corpus_dir)

    defaults = [e for e in (lib.get("defaults") or []) if isinstance(e, dict)]
    if not defaults:
        return {}
    digest = hashlib.sha256(f"{composer}|{work_title}".encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(defaults)
    pick = dict(defaults[idx])
    pick["_source"] = "default"
    return _entry_to_ambient(pick, base_url=base_url, corpus_dir=corpus_dir)
