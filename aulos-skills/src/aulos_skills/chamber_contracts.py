"""Chamber contracts — craft floors + ZH parity (SPEC-024)."""

from __future__ import annotations

from typing import Any

from aulos_skills.prose_hygiene import is_mostly_cjk, partition_dossier_languages
from aulos_skills.salon_codex import SALON_LIST_KEYS, _coerce_list, _merge_list, coerce_dict


REQUIRED_EN = (
    ("listening_thesis", 40),
    ("listening_map", 3),
    ("width_points", 3),
    ("depth_points", 3),
)


def _lenish(val: Any) -> int:
    if isinstance(val, list):
        return len(val)
    if isinstance(val, dict):
        return len(val)
    if isinstance(val, str):
        return len(val.strip())
    return 0


def audit_chamber_contracts(
    dossier: dict[str, Any] | None,
    *,
    identity_resolved: bool = False,
) -> list[dict[str, str]]:
    """Return gap findings. High severity when identity_resolved and floors fail."""
    d = dict(dossier or {})
    zh = coerce_dict(d.get("zh") or d.get("zh_hans"))
    gaps: list[dict[str, str]] = []
    sev = "high" if identity_resolved else "medium"

    thesis = str(d.get("listening_thesis") or "").strip()
    if thesis and is_mostly_cjk(thesis):
        gaps.append(
            {
                "severity": "high",
                "code": "contract_en_cjk",
                "note": "EN listening_thesis is mostly CJK",
            }
        )
    if _lenish(thesis) < 40:
        gaps.append(
            {
                "severity": sev,
                "code": "contract_thesis",
                "note": "listening_thesis below craft floor (40 chars)",
            }
        )
    if _lenish(d.get("listening_map")) < 3:
        gaps.append(
            {
                "severity": sev,
                "code": "contract_map",
                "note": "listening_map below craft floor (3 cues)",
            }
        )
    if _lenish(d.get("width_points")) < 3:
        gaps.append(
            {
                "severity": sev,
                "code": "contract_width",
                "note": "width_points below craft floor (3)",
            }
        )
    if _lenish(d.get("depth_points")) < 3:
        gaps.append(
            {
                "severity": sev,
                "code": "contract_depth",
                "note": "depth_points below craft floor (3)",
            }
        )
    if not coerce_dict(d.get("genesis")):
        gaps.append(
            {
                "severity": "medium" if identity_resolved else "low",
                "code": "contract_genesis",
                "note": "genesis chamber empty",
            }
        )
    if not coerce_dict(d.get("sound_world")):
        gaps.append(
            {
                "severity": "medium" if identity_resolved else "low",
                "code": "contract_sound",
                "note": "sound_world chamber empty",
            }
        )
    # ZH parity when EN craft exists
    if identity_resolved and _lenish(thesis) >= 40:
        if _lenish(zh.get("listening_thesis")) < 12:
            gaps.append(
                {
                    "severity": "high",
                    "code": "contract_zh_thesis",
                    "note": "ZH listening_thesis missing while EN craft present",
                }
            )
        if _lenish(d.get("listening_map")) >= 3 and _lenish(zh.get("listening_map")) < 2:
            gaps.append(
                {
                    "severity": "medium",
                    "code": "contract_zh_map",
                    "note": "ZH listening_map thin vs EN map",
                }
            )
        if _lenish(d.get("width_points")) >= 3 and _lenish(zh.get("width_points")) < 2:
            gaps.append(
                {
                    "severity": "medium",
                    "code": "contract_zh_width",
                    "note": "ZH width_points thin vs EN width",
                }
            )
    return gaps


def ensure_chamber_floor(
    dossier: dict[str, Any],
    family: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fill empty craft chambers from family floor; then mirror ZH parity stubs."""
    out = dict(dossier or {})
    fam = dict(family or {})
    if fam:
        for key in SALON_LIST_KEYS:
            fam_list = _coerce_list(fam.get(key))
            cur = _coerce_list(out.get(key))
            if not fam_list:
                continue
            if len(cur) < 3:
                out[key] = _merge_list(fam_list, cur) if cur else fam_list
        for key in ("genesis", "historical_stature", "sound_world", "composer_profile"):
            fam_val = fam.get(key)
            if fam_val and out.get(key) in (None, "", {}, []):
                out[key] = dict(fam_val) if isinstance(fam_val, dict) else fam_val
        for key in ("era", "form", "catalog", "listening_thesis", "work_introduction"):
            fam_val = fam.get(key)
            if not fam_val:
                continue
            cur = str(out.get(key) or "").strip()
            floor = 40 if key in {"listening_thesis", "work_introduction"} else 1
            if len(cur) < floor:
                out[key] = fam_val
        if isinstance(fam.get("interpretations"), list) and not out.get("interpretations"):
            out["interpretations"] = list(fam["interpretations"])
        if fam.get("zh"):
            zh_out = coerce_dict(out.get("zh") or out.get("zh_hans"))
            zh_fam = coerce_dict(fam.get("zh") or fam.get("zh_hans"))
            for key in ("listening_thesis", "work_introduction", "era", "form"):
                if zh_fam.get(key) and not str(zh_out.get(key) or "").strip():
                    zh_out[key] = zh_fam[key]
            for key in SALON_LIST_KEYS:
                fam_list = _coerce_list(zh_fam.get(key))
                cur = _coerce_list(zh_out.get(key))
                if fam_list and len(cur) < 2:
                    zh_out[key] = _merge_list(fam_list, cur) if cur else fam_list
            out["zh"] = zh_out
            out["zh_hans"] = dict(zh_out)
    out = mirror_zh_parity(out)
    out = partition_dossier_languages(out)
    # If partition moved CJK off EN and left thesis empty, restore family EN floor
    if fam and not str(out.get("listening_thesis") or "").strip() and fam.get("listening_thesis"):
        out["listening_thesis"] = fam["listening_thesis"]
    if fam and not str(out.get("work_introduction") or "").strip() and fam.get("work_introduction"):
        out["work_introduction"] = fam["work_introduction"]
    return out


def mirror_zh_parity(dossier: dict[str, Any]) -> dict[str, Any]:
    """When ZH craft is empty, mirror EN lists/thesis as temporary parity stubs."""
    out = dict(dossier or {})
    zh = coerce_dict(out.get("zh") or out.get("zh_hans"))
    en_thesis = str(out.get("listening_thesis") or "").strip()
    if en_thesis and not is_mostly_cjk(en_thesis) and not str(zh.get("listening_thesis") or "").strip():
        # Do not copy English into ZH thesis — leave for family zh or later LLM.
        # Only mirror structural lists so panes are not empty shells.
        pass
    for key in ("listening_map", "width_points", "depth_points", "practice_notes", "myths_and_caveats"):
        if out.get(key) and not zh.get(key):
            zh[key] = out.get(key)
    if zh:
        out["zh"] = zh
        out["zh_hans"] = dict(zh)
    return out
