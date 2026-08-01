"""Semantic locate: expert findings + human notes → ReviewIntent / chamber targets.

SPEC-022Δ / REQ-012 — shared by auto external_review and diary review_notes.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from aulos_skills.salon_codex import SALON_DICT_KEYS, SALON_LIST_KEYS, SALON_SCALAR_KEYS

CHAMBER_WHITELIST: frozenset[str] = frozenset(
    {
        *SALON_LIST_KEYS,
        *SALON_DICT_KEYS,
        *SALON_SCALAR_KEYS,
        "work_title",  # H1 / chrome
        "*",  # full-scope sentinel
    }
)

# Expert finding codes → dossier / chrome chambers
CODE_TO_TARGETS: dict[str, tuple[str, ...]] = {
    "portrait_composer_mismatch": ("composer_portrait",),
    "foreign_family_dossier": (
        "dossier_id",
        "width_points",
        "depth_points",
        "listening_map",
        "myths_and_caveats",
        "sound_world",
        "interpretations",
    ),
    "foreign_chamber_in_guide": (
        "width_points",
        "depth_points",
        "listening_map",
        "practice_notes",
        "myths_and_caveats",
        "sound_world",
    ),
    "rival_composer_dominance": (
        "composer_profile",
        "composer_portrait",
        "listening_thesis",
        "work_introduction",
    ),
    "intent_betrayal": (
        "listening_thesis",
        "work_introduction",
        "width_points",
        "depth_points",
        "form",
    ),
    "h1_title_drift": ("work_title", "appreciation_videos", "listening_thesis"),
    "h1_celebrity_pollution": ("work_title", "appreciation_videos", "listening_thesis"),
    "html_title_drift": ("work_title",),
    "incorrect_work_title": ("work_title",),
    "INCORRECT_WORK_TITLE": ("work_title",),
    "packaging_title_pollution": ("work_title",),
    "process_lock_in_product_prose": ("listening_thesis", "work_introduction", "myths_and_caveats"),
    "en_layer_cjk_pollution": ("listening_thesis", "work_introduction", "zh"),
    "form_title_mismatch": ("form", "listening_thesis", "depth_points"),
    "form_scale_mismatch": ("form", "depth_points", "listening_map"),
    "missing_listening_map": ("listening_map",),
    "missing_anatomy": ("depth_points", "listening_map"),
    "movement_error": ("listening_map", "depth_points", "variation_deepdives"),
    "expert_correction": ("listening_thesis", "depth_points", "listening_map"),
    "richness_empty": ("width_points", "depth_points", "listening_map", "genesis"),
}

# Human note keywords (zh/en) → chambers
_NOTE_KEYWORD_TARGETS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("portrait", "肖像", "头像", "composer image", "作曲家像"), ("composer_portrait",)),
    (("genesis", "创作背景", "时代", "历史背景", "创作史"), ("genesis", "historical_stature")),
    (("stature", "何以传世", "传世", "reception"), ("historical_stature",)),
    (("listening map", "聆听地图", "地图", "map"), ("listening_map",)),
    (("anatomy", "作品解剖", "解剖", "depth", "结构"), ("depth_points",)),
    (("thesis", "导赏论点", "论点", "thesis"), ("listening_thesis",)),
    (("introduction", "作品介绍", "导语"), ("work_introduction",)),
    (("sound", "声响", "音色", "sound world"), ("sound_world",)),
    (("interpretation", "名家演绎", "演绎"), ("interpretations",)),
    (("video", "视频", "欣赏视频"), ("appreciation_videos",)),
    (("ambient", "背景音乐", "氛围"), ("ambient_audio",)),
    (("myth", "误区", "caveat", "注意"), ("myths_and_caveats",)),
    (("practice", "练习", "练习聆听"), ("practice_notes",)),
    (("h1", "标题", "title"), ("work_title",)),
    (("cello", "大提琴", "foreign", "污染", "串台"), ("width_points", "depth_points", "listening_map")),
    (("profile", "作曲家简介", "生平"), ("composer_profile",)),
)


def _intent_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:10]
    return f"ri-{digest}"


def normalize_targets(raw: list[str] | tuple[str, ...] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for t in raw or []:
        key = str(t or "").strip()
        if not key or key not in CHAMBER_WHITELIST or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def targets_for_finding_code(code: str) -> list[str]:
    mapped = CODE_TO_TARGETS.get(str(code or "").strip())
    if mapped:
        return normalize_targets(list(mapped))
    return []


def locate_targets_from_notes(notes: str) -> list[str]:
    """Rule-based chamber locate from human review notes."""
    text = (notes or "").strip().lower()
    if not text:
        return []
    hits: list[str] = []
    seen: set[str] = set()
    # Direct chamber key mentions
    for key in sorted(CHAMBER_WHITELIST):
        if key == "*":
            continue
        if key.replace("_", " ") in text or key in text:
            if key not in seen:
                seen.add(key)
                hits.append(key)
    for keywords, targets in _NOTE_KEYWORD_TARGETS:
        if any(k.lower() in text for k in keywords):
            for t in targets:
                if t not in seen and t in CHAMBER_WHITELIST:
                    seen.add(t)
                    hits.append(t)
    return hits


def intents_from_expert_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    intents: list[dict[str, Any]] = []
    findings = [f for f in (report.get("findings") or []) if isinstance(f, dict)]
    corrections = [str(c) for c in (report.get("required_corrections") or []) if c]

    for i, f in enumerate(findings):
        code = str(f.get("code") or "")
        targets = targets_for_finding_code(code)
        severity = str(f.get("severity") or "medium")
        note = str(f.get("note") or code or "finding")
        instruction = note
        if i < len(corrections):
            instruction = corrections[i]
        elif corrections:
            instruction = f"{note} — {corrections[0]}"
        if not targets and severity == "high":
            targets = ["*"]
        if not targets:
            # medium/low without map: soft-skip (no full scope)
            continue
        intents.append(
            {
                "id": _intent_id("expert", code, note),
                "source": "expert",
                "severity": severity,
                "summary": note[:240],
                "targets": targets,
                "instruction": instruction[:800],
                "evidence": str(f.get("evidence") or "")[:400],
                "code": code,
            }
        )

    # Corrections without findings still need a home
    if not intents and corrections:
        intents.append(
            {
                "id": _intent_id("expert", "corrections", corrections[0]),
                "source": "expert",
                "severity": "high",
                "summary": corrections[0][:240],
                "targets": ["*"],
                "instruction": "; ".join(corrections[:5])[:800],
                "evidence": "",
                "code": "required_corrections",
            }
        )
    return intents


def intents_from_human_notes(
    notes: str,
    *,
    llm_locate: Any | None = None,
) -> list[dict[str, Any]]:
    text = (notes or "").strip()
    if not text:
        return []
    targets = locate_targets_from_notes(text)
    if not targets and callable(llm_locate):
        try:
            raw = llm_locate(text)
            if isinstance(raw, list):
                targets = normalize_targets([str(x) for x in raw])
            elif isinstance(raw, dict):
                targets = normalize_targets([str(x) for x in (raw.get("targets") or [])])
        except Exception:  # noqa: BLE001
            targets = []
    severity = "high"
    if not targets:
        # Unlocatable human notes → full scope (operator asked for a refresh)
        targets = ["*"]
    return [
        {
            "id": _intent_id("human", text[:80]),
            "source": "human",
            "severity": severity,
            "summary": text[:240],
            "targets": targets,
            "instruction": text[:2000],
            "evidence": "",
            "code": "human_review_notes",
        }
    ]


def merge_intents(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in groups:
        for intent in group:
            iid = str(intent.get("id") or "")
            if iid and iid in seen:
                continue
            if iid:
                seen.add(iid)
            out.append(intent)
    return out


def resolve_scope(intents: list[dict[str, Any]]) -> str:
    for intent in intents:
        if "*" in (intent.get("targets") or []):
            return "full"
    return "targeted" if intents else "noop"


def union_targets(intents: list[dict[str, Any]]) -> list[str]:
    if resolve_scope(intents) == "full":
        return ["*"]
    out: list[str] = []
    seen: set[str] = set()
    for intent in intents:
        for t in intent.get("targets") or []:
            if t == "*" or t in seen:
                continue
            if t not in CHAMBER_WHITELIST:
                continue
            seen.add(t)
            out.append(t)
    return out


def human_report_view(*, notes: str, intents: list[dict[str, Any]]) -> dict[str, Any]:
    """Normalize human notes into the review_report slot shape."""
    targets = union_targets(intents)
    return {
        "schema": "aulos.external_review/v1",
        "perspective": "human_review_notes",
        "verdict": "REVISE",
        "summary": (notes or "").strip()[:500] or "Human review notes",
        "findings": [
            {
                "severity": str(i.get("severity") or "high"),
                "code": str(i.get("code") or "human_review_notes"),
                "note": str(i.get("summary") or ""),
                "evidence": ",".join(i.get("targets") or []),
                "kind": "human",
            }
            for i in intents
        ],
        "required_corrections": [str(i.get("instruction") or "") for i in intents if i.get("instruction")],
        "sources_used": [],
        "layer": "human",
        "targets": targets,
    }


_SPLIT_SENT = re.compile(r"[。.!?\n]+")
