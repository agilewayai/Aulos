"""Operator-approved staging craft write from promote_candidate (SPEC-030)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from aulos_skills.craft_packs import craft_packs_root
from aulos_skills.salon_codex import coerce_dict

_WORK_ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)+$")


def staging_craft_root() -> Path:
    return craft_packs_root() / "staging"


def validate_work_id(work_id: str) -> bool:
    wid = (work_id or "").strip()
    if not wid or ".." in wid or "/" in wid or "\\" in wid:
        return False
    return bool(_WORK_ID_RE.match(wid))


def materialize_craft_pack(
    candidate: dict[str, Any],
    *,
    dossier: dict[str, Any] | None = None,
    composer: str = "",
    work_title: str = "",
) -> dict[str, Any]:
    """Build a craft-pack shaped dict from promote_candidate (+ optional dossier)."""
    cand = dict(candidate or {})
    d = dict(dossier or {})
    draft = coerce_dict(cand.get("craft_draft"))
    facets = coerce_dict(cand.get("facets"))
    wid = str(cand.get("suggested_work_id") or "").strip()
    name = (composer or str(d.get("composer") or "")).strip()
    title = (work_title or str(d.get("work_title") or "")).strip()
    family_id = str(cand.get("family_id") or d.get("family_id") or "chamber-generic")

    thesis = str(draft.get("listening_thesis") or d.get("listening_thesis") or "").strip()
    listening_map = list(draft.get("listening_map") or d.get("listening_map") or [])
    zh_draft = coerce_dict(draft.get("zh"))
    zh_doc = coerce_dict(d.get("zh") or d.get("zh_hans"))
    zh_thesis = str(zh_draft.get("listening_thesis") or zh_doc.get("listening_thesis") or "").strip()
    zh_map = list(zh_draft.get("listening_map") or zh_doc.get("listening_map") or [])

    pack: dict[str, Any] = {
        "work_id": wid,
        "composer": name,
        "work_title": title,
        "family_id": family_id,
        "era": str(d.get("era") or facets.get("era") or ""),
        "form": str(d.get("form") or ""),
        "listening_thesis": thesis,
        "work_introduction": str(d.get("work_introduction") or "").strip(),
        "width_points": list(d.get("width_points") or []),
        "depth_points": list(d.get("depth_points") or []),
        "listening_map": listening_map,
        "practice_notes": list(d.get("practice_notes") or []),
        "myths_and_caveats": list(d.get("myths_and_caveats") or [])
        + [
            "Staged from unknown-case promote_candidate — verify before production craft."
        ],
        "zh": {
            "listening_thesis": zh_thesis,
            "work_introduction": str(zh_doc.get("work_introduction") or "").strip(),
            "listening_map": zh_map,
            "width_points": list(zh_doc.get("width_points") or []),
            "depth_points": list(zh_doc.get("depth_points") or []),
        },
        "_provenance": {
            "promote_staged": True,
            "schema": "aulos.promote_candidate/v1",
            "family_id": family_id,
            "facets": {
                "instruments": list(facets.get("instruments") or []),
                "forms": list(facets.get("forms") or []),
                "era": str(facets.get("era") or ""),
            },
        },
    }
    return pack


def write_staging_craft(
    work_id: str,
    pack: dict[str, Any],
    *,
    overwrite: bool = False,
) -> Path:
    """Write craft YAML under craft/staging/. Never touches production craft/."""
    wid = (work_id or "").strip()
    if not validate_work_id(wid):
        raise ValueError(f"invalid suggested_work_id for staging: {work_id!r}")
    root = staging_craft_root()
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{wid}.yaml"
    # Resolve + ensure still under staging root (no symlink escape)
    resolved = path.resolve()
    if root.resolve() not in resolved.parents and resolved.parent != root.resolve():
        raise ValueError("staging path escaped craft/staging")
    if path.is_file() and not overwrite:
        raise FileExistsError(f"staging craft already exists: {wid}")

    out = dict(pack or {})
    out["work_id"] = wid
    prov = coerce_dict(out.get("_provenance"))
    prov["promote_staged"] = True
    prov["staged_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out["_provenance"] = prov
    path.write_text(
        yaml.safe_dump(out, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def load_staging_craft(work_id: str) -> dict[str, Any]:
    wid = (work_id or "").strip()
    if not validate_work_id(wid):
        return {}
    path = staging_craft_root() / f"{wid}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
