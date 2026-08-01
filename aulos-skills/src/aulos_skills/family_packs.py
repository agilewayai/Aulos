"""Load synthesize family packs by id (SPEC-027)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


def synthesize_families_root() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "aulos-listening-synthesize"
        / "assets"
        / "families"
    )


@lru_cache(maxsize=64)
def load_family_pack(family_id: str) -> dict[str, Any]:
    fid = (family_id or "").strip()
    if not fid:
        return {}
    path = synthesize_families_root() / f"{fid}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def catalog_family_id(work_id: str) -> str:
    from aulos_skills.identity import load_catalog

    wid = (work_id or "").strip()
    if not wid:
        return ""
    work = load_catalog().works.get(wid)
    if work is None or not work.family_id:
        return ""
    return str(work.family_id)
