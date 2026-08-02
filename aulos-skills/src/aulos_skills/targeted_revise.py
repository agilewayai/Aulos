"""Targeted chamber patch + re-render (SPEC-022Δ) — no default full compose."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from typing import Any, Callable

from aulos_skills.guide_render import render_bilingual_guide_html
from aulos_skills.i18n import dossier_has_zh, ensure_chinese_variants, re_has_cjk
from aulos_skills.review_targets import (
    human_report_view,
    intents_from_expert_report,
    intents_from_human_notes,
    merge_intents,
    resolve_scope,
    union_targets,
)
from aulos_skills.revise_repair import (
    apply_review_repairs,
    proofread_with_llm,
    scan_hard_flaws,
    score_draft_with_hard_flaws,
)

ROUNDS_SCHEMA_V2 = "aulos.generation_rounds/v2"

LlmComplete = Callable[[str], str | None]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _score_snapshot(html: str, context: dict[str, Any], *, phase: str = "revise") -> dict[str, Any]:
    card = score_draft_with_hard_flaws(html=html, context=context, phase=phase)
    rollup = dict(card.get("rollup") or {})
    return {
        "pct": float(rollup.get("pct") or 0),
        "hard_flaws": int(rollup.get("hard_flaws_remaining") or 0),
        "band": str(rollup.get("band") or ""),
        "process_scorecard": card,
    }


def _append_history(context: dict[str, Any], entry: dict[str, Any]) -> None:
    rounds = dict(context.get("generation_rounds") or {})
    history = list(rounds.get("revision_history") or [])
    history.append(entry)
    rounds["revision_history"] = history[-40:]
    rounds["schema"] = ROUNDS_SCHEMA_V2
    context["generation_rounds"] = rounds


def _dossier_from_context(context: dict[str, Any]) -> dict[str, Any]:
    dossier = dict(context.get("corpus_dossier") or {})
    if not dossier:
        width = dict(context.get("width_dossier") or {})
        dossier = dict(width.get("salon_dossier") or {})
    return dossier


def _patch_chamber_deterministic(
    dossier: dict[str, Any],
    *,
    target: str,
    instruction: str,
    work_title: str,
    composer: str,
) -> str:
    """Apply a minimal scaffold rewrite for a single chamber; return diff note."""
    if target == "composer_portrait":
        dossier["composer_portrait"] = {}
        return "composer_portrait: cleared"
    if target == "listening_map":
        dossier["listening_map"] = [
            {"label": "Opening", "cue": f"Lock the primary motive of {work_title or 'the work'}."},
            {"label": "Development / middle", "cue": "Track contrast and the turning point."},
            {"label": "Close", "cue": "Hear how the return remembers the opening — altered."},
        ]
        return "listening_map: rewritten scaffold"
    if target == "depth_points":
        dossier["depth_points"] = [
            f"Form landmarks for {work_title or 'this work'}.",
            "Map structural turns with concrete ear cues.",
            "Notice how the close transforms the opening material.",
        ]
        return "depth_points: rewritten scaffold"
    if target == "listening_thesis":
        base = str(dossier.get("listening_thesis") or "")
        pin = f"REVIEW: {instruction[:180]}"
        if pin not in base:
            dossier["listening_thesis"] = f"{pin} — {base}".strip(" —")
        return "listening_thesis: pinned instruction"
    if target == "work_introduction":
        intro = str(dossier.get("work_introduction") or "")
        dossier["work_introduction"] = (
            f"{instruction[:220]} {intro}".strip() if instruction else intro
        )
        return "work_introduction: refreshed"
    if target == "work_title" and work_title:
        dossier["work_title"] = work_title
        return "work_title: restored from lock"
    if target == "myths_and_caveats":
        caveats = list(dossier.get("myths_and_caveats") or [])
        if instruction and instruction not in caveats:
            caveats.insert(0, instruction[:240])
        dossier["myths_and_caveats"] = caveats[:10]
        return "myths_and_caveats: appended note"
    if target == "genesis":
        genesis = dict(dossier.get("genesis") or {})
        note = instruction[:400] if instruction else ""
        if note:
            genesis["summary"] = note
            genesis["context"] = note
        dossier["genesis"] = genesis
        return "genesis: refreshed from notes"
    if target == "historical_stature":
        stature = dict(dossier.get("historical_stature") or {})
        reasons = list(stature.get("reasons") or [])
        if instruction and instruction not in reasons:
            reasons.insert(0, instruction[:240])
        stature["reasons"] = reasons[:8]
        dossier["historical_stature"] = stature
        return "historical_stature: reasons updated"
    if target == "dossier_id":
        dossier["dossier_id"] = ""
        return "dossier_id: cleared foreign family"
    if target in {"width_points", "practice_notes"}:
        items = list(dossier.get(target) or [])
        if instruction:
            items = [x for x in items if instruction[:40].lower() not in str(x).lower()]
            items.insert(0, instruction[:240])
        dossier[target] = items[:10]
        return f"{target}: adjusted"
    if target in {"sound_world", "composer_profile"}:
        blob = dict(dossier.get(target) or {})
        if instruction:
            blob["note"] = instruction[:400]
        dossier[target] = blob
        return f"{target}: note set"
    if target == "form" and "concerto" in (work_title or "").lower():
        dossier["form"] = "piano concerto"
        return "form: aligned"
    # Soft touch: stash instruction in myths so render surfaces the ask
    if instruction:
        caveats = list(dossier.get("myths_and_caveats") or [])
        tag = f"[{target}] {instruction[:200]}"
        if tag not in caveats:
            caveats.insert(0, tag)
        dossier["myths_and_caveats"] = caveats[:10]
        return f"{target}: instruction stashed"
    return f"{target}: no-op"


def _patch_chambers_llm(
    dossier: dict[str, Any],
    *,
    targets: list[str],
    intents: list[dict[str, Any]],
    work_title: str,
    composer: str,
    llm_complete: LlmComplete,
) -> list[str]:
    if not targets or targets == ["*"]:
        return []
    subset = {t: copy.deepcopy(dossier.get(t)) for t in targets if t != "*"}
    prompt = (
        "你是音乐导赏定点校对编辑。只改写指定 dossier chambers，输出 JSON：\n"
        '{"patches":{"chamber_key": <new value>}, "notes":["…"]}\n'
        "未列出的字段不要输出。禁止引入无关作品。\n"
        f"work={work_title!r} composer={composer!r}\n"
        f"targets={json.dumps(targets, ensure_ascii=False)}\n"
        f"intents={json.dumps(intents, ensure_ascii=False)[:2500]}\n"
        f"current={json.dumps(subset, ensure_ascii=False)[:3500]}\n"
    )
    try:
        raw = llm_complete(prompt) or ""
    except Exception:  # noqa: BLE001
        return []
    from aulos_skills.external_review import _parse_json_obj

    data = _parse_json_obj(raw)
    if not data or not isinstance(data.get("patches"), dict):
        return []
    notes: list[str] = []
    for key, value in data["patches"].items():
        if key not in targets or key == "*":
            continue
        dossier[key] = value
        notes.append(f"{key}: llm patch")
    for n in data.get("notes") or []:
        if n:
            notes.append(str(n)[:120])
    return notes[:12]


def render_from_dossier(context: dict[str, Any], dossier: dict[str, Any]) -> tuple[str, str]:
    dossier = ensure_chinese_variants(dict(dossier))
    work_title = str(context.get("work_title") or dossier.get("work_title") or "")
    composer = str(context.get("composer") or dossier.get("composer") or "")
    thesis_en = str(dossier.get("listening_thesis") or context.get("summary") or "")
    zh = dict(dossier.get("zh") or dossier.get("zh_hans") or {})
    thesis_zh = str(zh.get("listening_thesis") or "")
    prefer_zh = bool(context.get("prefer_zh")) or re_has_cjk(str(context.get("raw_message") or ""))
    default_lang = "zh-Hans" if (prefer_zh and dossier_has_zh(dossier)) else "en"
    html = render_bilingual_guide_html(
        dossier=dossier,
        work_title=work_title,
        composer=composer,
        summary_en=thesis_en,
        summary_zh=thesis_zh,
        default_lang=default_lang,
    )
    summary = thesis_zh if prefer_zh and thesis_zh else thesis_en
    return html, summary


def run_targeted_revise(
    context: dict[str, Any],
    *,
    report: dict[str, Any] | None = None,
    human_notes: str | None = None,
    llm_complete: LlmComplete | None = None,
    allow_full_compose: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Patch targeted chambers and re-render. Full compose only when scope=full."""
    from aulos_skills.identity_lock import scrub_dossier_if_identity_polluted

    # Regen class: never patch on top of a foreign-work dossier masked by lock labels.
    dossier0 = _dossier_from_context(context)
    scrubbed, was_polluted = scrub_dossier_if_identity_polluted(
        dossier0,
        work_title=str(context.get("work_title") or ""),
        work_hint=str(context.get("work_hint") or ""),
        raw_message=str(context.get("raw_message") or ""),
        composer=str(context.get("composer") or ""),
    )
    if was_polluted:
        context["corpus_dossier"] = scrubbed
        context["identity_pollution_scrubbed"] = True
        context["refuse_families"] = True
        # Prefer full rebuild when available — targeted patches cannot unpoison.
        if allow_full_compose is not None:
            context["revise_scope"] = "full"
            context["force_full_compose_identity_pollution"] = True

    expert_report = dict(report or context.get("external_review_report") or {})
    notes = (human_notes if human_notes is not None else str(context.get("review_notes") or "")).strip()

    expert_intents = intents_from_expert_report(expert_report) if expert_report.get("findings") or expert_report.get("required_corrections") else []
    human_intents = intents_from_human_notes(notes) if notes else []
    intents = merge_intents(expert_intents, human_intents)
    scope = resolve_scope(intents)
    if context.get("force_full_compose_identity_pollution"):
        scope = "full"
    targets = union_targets(intents)

    before_html = str(context.get("guide_html") or "")
    if not before_html:
        before_html = str(
            ((context.get("generation_rounds") or {}).get("draft_v2") or {}).get("guide_html")
            or ((context.get("generation_rounds") or {}).get("draft_v1") or {}).get("guide_html")
            or ""
        )
    score_before = _score_snapshot(before_html, context, phase="compose")

    # Latest review slot
    rounds = dict(context.get("generation_rounds") or {})
    rounds.setdefault("schema", ROUNDS_SCHEMA_V2)
    if notes and human_intents:
        review_view = human_report_view(notes=notes, intents=human_intents)
        if expert_report:
            review_view["prior_expert"] = {
                "verdict": expert_report.get("verdict"),
                "summary": expert_report.get("summary"),
            }
        rounds["review_report"] = review_view
        context["external_review_report"] = review_view
        _append_history(
            context,
            {
                "id": f"rev-notes-{_utcnow_iso()}",
                "at": _utcnow_iso(),
                "source": "human",
                "summary": notes[:200],
                "targets": targets,
                "scope": "locate",
                "score_before": {"pct": score_before["pct"], "hard_flaws": score_before["hard_flaws"]},
                "score_after": {"pct": score_before["pct"], "hard_flaws": score_before["hard_flaws"]},
                "diff_summary": ["review_report: human notes"],
                "intent_ids": [str(i.get("id")) for i in human_intents],
            },
        )
        rounds = dict(context.get("generation_rounds") or {})
    elif expert_report:
        rounds["review_report"] = expert_report
        context["external_review_report"] = expert_report

    context["generation_rounds"] = rounds
    context["review_intents"] = intents
    context["revise_scope"] = scope

    diff_summary: list[str] = []
    repair_log: list[str] = []

    if scope == "full" and allow_full_compose is not None:
        if expert_report:
            repair_meta = apply_review_repairs(context, expert_report)
            repair_log.extend(repair_meta.get("log") or [])
            if llm_complete and (
                expert_report.get("verdict") in {"REVISE", "FAIL"}
                or context.get("critique_corrections")
            ):
                proof = proofread_with_llm(context, expert_report, llm_complete=llm_complete)
                if proof.get("applied"):
                    repair_log.append("llm_proofread")
        composed = allow_full_compose(context)
        html = str(composed.get("guide_html") or "")
        summary = str(composed.get("summary") or "")
        diff_summary.append("scope=full: recompose")
        repair_log.append("full_compose")
    else:
        # Targeted path
        if expert_report and expert_intents:
            repair_meta = apply_review_repairs(context, expert_report)
            repair_log.extend(repair_meta.get("log") or [])
            for item in repair_meta.get("log") or []:
                diff_summary.append(str(item))

        dossier = _dossier_from_context(context)
        work_title = str(context.get("work_title") or dossier.get("work_title") or "")
        composer = str(context.get("composer") or dossier.get("composer") or "")

        patch_targets = [t for t in targets if t != "*"]
        if llm_complete and patch_targets:
            llm_notes = _patch_chambers_llm(
                dossier,
                targets=patch_targets,
                intents=intents,
                work_title=work_title,
                composer=composer,
                llm_complete=llm_complete,
            )
            diff_summary.extend(llm_notes)
            if llm_notes:
                repair_log.append("llm_chamber_patch")

        for intent in intents:
            for target in intent.get("targets") or []:
                if target == "*":
                    continue
                note = _patch_chamber_deterministic(
                    dossier,
                    target=str(target),
                    instruction=str(intent.get("instruction") or ""),
                    work_title=work_title,
                    composer=composer,
                )
                if note and note not in diff_summary:
                    diff_summary.append(note)

        # Sync depth/width mirrors
        depth = dict(context.get("depth_dossier") or {})
        if "listening_map" in dossier:
            depth["listening_map"] = list(dossier.get("listening_map") or [])
        if "depth_points" in dossier:
            depth["depth_points"] = list(dossier.get("depth_points") or [])
        context["depth_dossier"] = depth
        width = dict(context.get("width_dossier") or {})
        width["salon_dossier"] = dict(dossier)
        context["width_dossier"] = width
        context["corpus_dossier"] = dossier

        html, summary = render_from_dossier(context, dossier)
        repair_log.append("targeted_render")

    context["guide_html"] = html
    context["summary"] = summary
    context["revise_repair_log"] = repair_log

    remaining = scan_hard_flaws(html=html, context=context)
    score_after = _score_snapshot(html, context, phase="revise")

    # Freeze draft_v1 if present; never overwrite here
    rounds = dict(context.get("generation_rounds") or {})
    rounds["schema"] = ROUNDS_SCHEMA_V2
    v2 = {
        "guide_html": html,
        "summary": summary,
        "process_scorecard": score_after["process_scorecard"],
        "hard_flaws": list(score_after["process_scorecard"].get("hard_flaws") or [])[:20],
        "hard_flaws_remaining": remaining[:20],
        "repair_log": repair_log,
        "patched_targets": targets,
        "scope": scope,
    }
    rounds["draft_v2"] = v2
    context["generation_rounds"] = rounds

    from aulos_skills.external_review import build_rounds_comparison

    build_rounds_comparison(context)

    source = "human" if human_intents and not expert_intents else ("expert" if expert_intents else "mixed")
    if expert_intents and human_intents:
        source = "mixed"
    _append_history(
        context,
        {
            "id": f"rev-patch-{_utcnow_iso()}",
            "at": _utcnow_iso(),
            "source": source,
            "summary": (notes or str(expert_report.get("summary") or "") or "targeted revise")[:200],
            "targets": targets,
            "scope": scope,
            "score_before": {"pct": score_before["pct"], "hard_flaws": score_before["hard_flaws"]},
            "score_after": {"pct": score_after["pct"], "hard_flaws": score_after["hard_flaws"]},
            "diff_summary": diff_summary[:16] or repair_log[:8],
            "intent_ids": [str(i.get("id")) for i in intents],
        },
    )

    return {
        "guide_html": html,
        "summary": summary,
        "composer": context.get("composer"),
        "work_title": context.get("work_title"),
        "generation_rounds": dict(context.get("generation_rounds") or {}),
        "revised_after_review": True,
        "revise_repair_log": repair_log,
        "revise_scope": scope,
        "patched_targets": targets,
        "hard_flaws_remaining": remaining[:12],
        "review_intents": intents,
    }
