"""Adaptive ambient-music agent — curated → related → default rotation.

Identity-aware: conflict_markers + facet instrument gates (SPEC-008).
No work-proper-name special cases.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from aulos_skills.ambient_playlist import resolve_ambient_audio

_INSTRUMENT_TOKENS = (
    "cello",
    "violoncello",
    "大提琴",
    "piano",
    "键盘",
    "harpsichord",
    "羽管键琴",
    "keyboard",
    "organ",
    "管风琴",
    "violin",
    "orchestra",
    "交响",
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
    resolved["selection_source"] = str(entry.get("_source") or "related")
    if entry.get("why"):
        resolved["why"] = entry["why"]
    if entry.get("why_zh"):
        resolved["why_zh"] = entry["why_zh"]
    return resolved


def _has_any(blob: str, tokens: tuple[str, ...] | list[str]) -> bool:
    return any(t and t in blob for t in tokens)


def ambient_conflicts_markers(*, ambient: dict[str, Any], conflict_markers: list[str]) -> bool:
    """True when ambient blob contains any catalog-derived conflict marker."""
    if not ambient or not conflict_markers:
        return False
    amb_blob = json.dumps(ambient, ensure_ascii=False).lower()
    return any(len(m) >= 3 and m.lower() in amb_blob for m in conflict_markers)


def _facet_instruments(facets: dict[str, Any] | None, blob: str) -> set[str]:
    out: set[str] = set()
    for v in (facets or {}).get("instruments") or []:
        out.add(str(v).lower())
    for tok in _INSTRUMENT_TOKENS:
        if tok in blob:
            out.add(tok)
    return out


def _score_related(
    entry: dict[str, Any],
    *,
    blob: str,
    composer: str,
    peers_blob: str,
    work_instruments: set[str],
) -> int:
    score = 0
    composers = [str(x).lower() for x in (entry.get("composers") or [])]
    eras = [str(x).lower() for x in (entry.get("eras") or [])]
    forms = [str(x).lower() for x in (entry.get("forms") or [])]
    peers = [str(x).lower() for x in (entry.get("peers") or [])]
    instruments = [str(x).lower() for x in (entry.get("instruments") or [])]
    weight = int(entry.get("weight") or 5)

    entry_instruments = set(instruments) | {
        f for f in forms if f in _INSTRUMENT_TOKENS
    }

    # Generic timbre gate: instrument-specific packs require intersection
    if entry_instruments and work_instruments and entry_instruments.isdisjoint(work_instruments):
        return 0
    if entry_instruments and not work_instruments:
        # Prefer not attaching cello-only packs to non-cello works without instrument signal
        if any(i in entry_instruments for i in ("cello", "violoncello", "大提琴")) and "cello" not in blob and "大提琴" not in blob:
            return 0

    composer_hit = any(c and c in composer for c in composers) or any(c and c in blob for c in composers)
    peer_hit = any(p and p in peers_blob for p in peers) or any(p and p in blob for p in peers)
    era_hit = any(e and e in blob for e in eras)
    form_hit = any(f and f in blob for f in forms)
    instrument_hit = bool(entry_instruments & work_instruments) or any(i and i in blob for i in instruments)

    # Composer-scoped packs must not unlock on bare form/era (Mozart piano ≠ Beethoven Für Elise).
    if composers and not composer_hit:
        # Intentional cross-composer peer (e.g. Bach cello suite for Beethoven duo) needs peer + timbre
        if not (peer_hit and (instrument_hit or form_hit)):
            return 0

    # Era/form "classical peer" packs with empty composers[] must name the shelf composer in peers[]
    if peers and not composers and not peer_hit:
        return 0

    if composer_hit:
        score += 40
    if era_hit:
        score += 12
    if form_hit:
        score += 14
    if instrument_hit:
        score += 22
    if peer_hit and not composer_hit:
        score += 18
    if score <= 0:
        return 0
    return score + weight


def _entry_names_foreign_composer(entry: dict[str, Any], composer_l: str) -> bool:
    """True when entry is clearly another composer's recording and shelf composer is known."""
    if not composer_l or len(composer_l) < 4:
        return False
    composers = [str(x).lower() for x in (entry.get("composers") or []) if x]
    if composers and not any(c and c in composer_l for c in composers):
        return True
    title = str(entry.get("title") or "").lower()
    # Bare title prefixes used in defaults / peers
    foreign_prefixes = (
        "beethoven",
        "bach",
        "chopin",
        "mozart",
        "goldberg",
        "贝多芬",
        "巴赫",
        "肖邦",
        "莫扎特",
    )
    for pref in foreign_prefixes:
        if pref in title and pref not in composer_l:
            # Allow when composers list explicitly includes shelf composer
            if composers and any(c in composer_l for c in composers):
                return False
            return True
    return False


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
) -> dict[str, Any]:
    """Pick ambient audio: ambient_ref → curated → related → default."""
    hints = list(family_hints or [])
    markers = [str(m).lower() for m in (conflict_markers or []) if m]
    work_blob = " ".join(str(x) for x in [composer, work_title, era, form, *hints] if x).lower()
    work_instruments = _facet_instruments(facets, work_blob)

    lib = load_ambient_library(corpus_dir)
    base_url = str(lib.get("base_url") or "")

    # 1) Explicit catalog ambient_ref — catalog authority wins (may be an honest
    # same-composer peer when no work-specific CC0 track exists).
    if ambient_ref:
        for entry in list(lib.get("related") or []) + list(lib.get("defaults") or []):
            if not isinstance(entry, dict):
                continue
            if str(entry.get("id") or "") == ambient_ref:
                pick = dict(entry)
                pick["_source"] = "catalog-ref"
                return _entry_to_ambient(pick, base_url=base_url, corpus_dir=corpus_dir)

    # 2) Curated on dossier — keep honest peer stand-ins; scrub alien flagships only
    existing_resolved = resolve_ambient_audio(dict(existing or {}), corpus_dir=corpus_dir)
    if existing_resolved.get("tracks") or existing_resolved.get("url"):
        why_blob = f"{existing_resolved.get('why') or ''} {existing_resolved.get('why_zh') or ''}".lower()
        peerish = any(
            w in why_blob
            for w in (
                "peer",
                "stand-in",
                "stand in",
                "atmosphere",
                "关联",
                "尚无",
                "open library",
                "公开授权库",
            )
        )
        if peerish or not ambient_conflicts_markers(ambient=existing_resolved, conflict_markers=markers):
            out = dict(existing_resolved)
            out.setdefault("selection_source", "curated")
            if not out.get("why"):
                out["why"] = "Curated open recording packaged with this listening guide."
                out["why_zh"] = "本导赏附带的公开授权录音／曲目列表。"
            return out

    # 3) Related by facets / composer
    blob = work_blob
    peers_blob = blob
    composer_l = (composer or "").lower()
    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in lib.get("related") or []:
        if not isinstance(entry, dict):
            continue
        if ambient_conflicts_markers(ambient=entry, conflict_markers=markers):
            continue
        score = _score_related(
            entry,
            blob=blob,
            composer=composer_l,
            peers_blob=peers_blob,
            work_instruments=work_instruments,
        )
        if score > 0:
            scored.append((score, entry))
    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        best = dict(scored[0][1])
        best["_source"] = "related"
        return _entry_to_ambient(best, base_url=base_url, corpus_dir=corpus_dir)

    # 4) Defaults — skip conflict-marked and foreign-composer entries when shelf is known
    defaults = [e for e in (lib.get("defaults") or []) if isinstance(e, dict)]
    safe = [
        e
        for e in defaults
        if not ambient_conflicts_markers(ambient=e, conflict_markers=markers)
        and not _entry_names_foreign_composer(e, composer_l)
    ]
    pool = safe or [
        e
        for e in defaults
        if not ambient_conflicts_markers(ambient=e, conflict_markers=markers)
    ] or defaults
    if not pool:
        return {}
    digest = hashlib.sha256(f"{composer}|{work_title}".encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(pool)
    pick = dict(pool[idx])
    pick["_source"] = "default"
    return _entry_to_ambient(pick, base_url=base_url, corpus_dir=corpus_dir)
