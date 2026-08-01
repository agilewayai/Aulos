"""Craft packs — optional accelerator cache written by promote-production (SPEC-031).

Hand-authored per-work craft YAML is NOT required. Catalog floor + dimension
templates thicken unknown and Catalog shelves. Craft files appear only when an
operator graduates a promote_candidate.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from aulos_skills.identity import default_catalog_root


def craft_packs_root() -> Path:
    return default_catalog_root().parent / "craft"


@lru_cache(maxsize=64)
def load_craft_pack(work_id: str) -> dict[str, Any]:
    wid = (work_id or "").strip()
    if not wid:
        return {}
    path = craft_packs_root() / f"{wid}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def list_craft_work_ids() -> list[str]:
    """Production craft ids only (excludes staging/)."""
    root = craft_packs_root()
    if not root.is_dir():
        return []
    return sorted(
        p.stem
        for p in root.glob("*.yaml")
        if p.is_file() and p.parent.resolve() == root.resolve()
    )


def craft_pack_to_dossier(pack: dict[str, Any], *, composer: str, work_title: str) -> dict[str, Any]:
    from aulos_skills.salon_codex import empty_dossier

    d = empty_dossier()
    d["work_title"] = work_title or str(pack.get("work_title") or "")
    d["composer"] = composer or str(pack.get("composer") or "")
    for key in (
        "catalog",
        "era",
        "form",
        "listening_thesis",
        "work_introduction",
        "width_points",
        "depth_points",
        "myths_and_caveats",
        "listening_map",
        "variation_deepdives",
        "related_works",
        "interpretations",
        "appreciation_videos",
        "practice_notes",
        "genesis",
        "historical_stature",
        "sound_world",
        "composer_profile",
        "composer_portrait",
        "zh",
    ):
        if pack.get(key) is not None:
            d[key] = pack[key]
    d["dossier_id"] = f"craft:{pack.get('work_id') or 'unknown'}"
    d["raw_format"] = "craft-pack"
    prov = dict(d.get("_provenance") or {}) if isinstance(d.get("_provenance"), dict) else {}
    prov["craft_pack"] = True
    prov["work_id"] = pack.get("work_id")
    d["_provenance"] = prov
    return d


def reassert_craft_leads(dossier: dict[str, Any], work_id: str | None) -> dict[str, Any]:
    """Pin craft-pack EN/ZH listening theses over later LLM poetic drift when craft exists."""
    from aulos_skills.salon_codex import coerce_dict

    pack = load_craft_pack(str(work_id or ""))
    if not pack:
        return dossier
    out = dict(dossier or {})
    if pack.get("listening_thesis"):
        out["listening_thesis"] = str(pack["listening_thesis"]).strip()
    if pack.get("work_introduction"):
        out["work_introduction"] = str(pack["work_introduction"]).strip()
    zh_pack = coerce_dict(pack.get("zh"))
    if zh_pack:
        zh = coerce_dict(out.get("zh") or out.get("zh_hans"))
        for key in ("listening_thesis", "work_introduction"):
            if zh_pack.get(key):
                zh[key] = str(zh_pack[key]).strip()
        if zh:
            out["zh"] = zh
            out["zh_hans"] = dict(zh)
    return out
