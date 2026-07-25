"""Salon Codex merge helpers for synthesize / corpus dossiers."""

from __future__ import annotations

import json
import re
from typing import Any


SALON_LIST_KEYS = (
    "width_points",
    "depth_points",
    "myths_and_caveats",
    "practice_notes",
    "listening_map",
    "variation_deepdives",
    "related_works",
    "interpretations",
    "appreciation_videos",
    "vinyl_and_discography",
)

SALON_DICT_KEYS = (
    "composer_portrait",
    "composer_profile",
    "genesis",
    "historical_stature",
    "sound_world",
    "ambient_audio",
    "zh",
)

SALON_SCALAR_KEYS = (
    "dossier_id",
    "work_title",
    "composer",
    "catalog",
    "era",
    "form",
    "listening_thesis",
    "work_introduction",
)


def empty_dossier() -> dict[str, Any]:
    return {
        "dossier_id": "",
        "work_title": "",
        "composer": "",
        "catalog": "",
        "era": "",
        "form": "",
        "listening_thesis": "",
        "work_introduction": "",
        "composer_portrait": {},
        "composer_profile": {},
        "genesis": {},
        "historical_stature": {"reasons": [], "reception_arc": ""},
        "width_points": [],
        "depth_points": [],
        "myths_and_caveats": [],
        "listening_map": [],
        "variation_deepdives": [],
        "sound_world": {},
        "ambient_audio": {},
        "related_works": [],
        "interpretations": [],
        "appreciation_videos": [],
        "vinyl_and_discography": [],
        "practice_notes": [],
    }


def _merge_dict(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = dict(a or {})
    for k, v in (b or {}).items():
        if v in (None, "", [], {}):
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dict(out[k], v)
        else:
            out[k] = v
    return out


def _coerce_list(val: Any) -> list[Any]:
    """LLM / YAML sometimes emit a string or dict where a list is required."""
    if val is None or val == "":
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, tuple):
        return list(val)
    if isinstance(val, dict):
        return [val]
    if isinstance(val, str):
        text = val.strip()
        return [text] if text else []
    return []


def _merge_list(a: list[Any], b: list[Any]) -> list[Any]:
    a = _coerce_list(a)
    b = _coerce_list(b)
    if not a:
        return list(b)
    if not b:
        return list(a)
    out = list(a)
    seen = {json.dumps(x, sort_keys=True, default=str) for x in a}
    for item in b:
        key = json.dumps(item, sort_keys=True, default=str)
        if key not in seen:
            out.append(item)
            seen.add(key)
    return out


def merge_dossiers(*layers: dict[str, Any] | None) -> dict[str, Any]:
    """Merge Salon Codex layers; later layers override scalars and nested dict values."""
    out = empty_dossier()
    for layer in layers:
        if not layer:
            continue
        for key in SALON_SCALAR_KEYS:
            val = layer.get(key)
            if isinstance(val, str) and val.strip():
                out[key] = val.strip()
            elif val not in (None, ""):
                out[key] = val
        for key in SALON_DICT_KEYS:
            if key == "zh":
                continue
            if layer.get(key):
                if key == "historical_stature":
                    cur = dict(out.get("historical_stature") or {})
                    nxt = dict(layer.get("historical_stature") or {})
                    reasons = _merge_list(list(cur.get("reasons") or []), list(nxt.get("reasons") or []))
                    merged = _merge_dict(cur, nxt)
                    merged["reasons"] = reasons
                    out["historical_stature"] = merged
                else:
                    out[key] = _merge_dict(dict(out.get(key) or {}), dict(layer.get(key) or {}))
        if layer.get("zh"):
            # Nested Chinese dossier — merge as a dossier, never nest zh inside zh
            zh_layer = dict(layer.get("zh") or {})
            zh_layer.pop("zh", None)
            out["zh"] = merge_dossiers(dict(out.get("zh") or {}), zh_layer)
        for key in SALON_LIST_KEYS:
            if layer.get(key):
                out[key] = _merge_list(_coerce_list(out.get(key)), _coerce_list(layer.get(key)))
        # pass through misc flags
        for key in ("raw_format", "dossier_id"):
            if layer.get(key):
                out[key] = layer[key]
    return out


def dossier_richness(dossier: dict[str, Any] | None) -> int:
    """Rough chamber coverage score for pass-through decisions."""
    d = dossier or {}
    score = 0
    if d.get("composer_portrait", {}).get("image_url"):
        score += 2
    if d.get("composer_profile"):
        score += 1
    if d.get("genesis"):
        score += 1
    if (d.get("historical_stature") or {}).get("reasons"):
        score += 1
    if d.get("sound_world"):
        score += 1
    if len(d.get("listening_map") or []) >= 2:
        score += 1
    if d.get("interpretations") or d.get("appreciation_videos"):
        score += 1
    if len(d.get("depth_points") or []) >= 3:
        score += 1
    if d.get("listening_thesis") or d.get("work_introduction"):
        score += 1
    return score


def parse_llm_dossier_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from model output (raw or fenced)."""
    raw = (text or "").strip()
    if not raw:
        return {}
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.S)
    if fence:
        raw = fence.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    for key in SALON_LIST_KEYS:
        if key in data:
            data[key] = _coerce_list(data.get(key))
    if isinstance(data.get("zh"), dict):
        for key in SALON_LIST_KEYS:
            if key in data["zh"]:
                data["zh"][key] = _coerce_list(data["zh"].get(key))
    return data


def family_to_dossier(family: dict[str, Any], *, composer: str, work_title: str) -> dict[str, Any]:
    d = empty_dossier()
    template = str(family.get("work_title_template") or "{composer} — Chamber work")
    title = work_title or template.format(composer=composer or "Composer")
    d["work_title"] = title
    d["composer"] = composer or str(family.get("composer") or "")
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
        "vinyl_and_discography",
        "practice_notes",
        "genesis",
        "historical_stature",
        "sound_world",
        "ambient_audio",
        "zh",
    ):
        if family.get(key) is not None:
            d[key] = family[key]
    d["dossier_id"] = f"family:{family.get('family_id') or 'unknown'}"
    d["raw_format"] = "synthesize"
    return d


def composer_to_dossier(card: dict[str, Any]) -> dict[str, Any]:
    d = empty_dossier()
    d["composer"] = str(card.get("composer") or "")
    d["composer_portrait"] = dict(card.get("composer_portrait") or {})
    d["composer_profile"] = dict(card.get("composer_profile") or {})
    if card.get("zh"):
        d["zh"] = dict(card["zh"])
    d["raw_format"] = "synthesize"
    return d
