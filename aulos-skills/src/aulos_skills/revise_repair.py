"""Revise repair + dual-draft scoring (SPEC-022Δ) — proofread against expert review."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from aulos_skills.external_review import (
    _expert_hard_flaw_findings,
    _findings_from_hygiene,
    _parse_json_obj,
)
from aulos_skills.identity_hygiene import apply_identity_hygiene, scrub_markers_for_family
from aulos_skills.identity_lock import identity_lock_alien_markers
from aulos_skills.process_scorecard import score_node

LlmComplete = Callable[[str], str | None]

def scan_hard_flaws(
    *,
    html: str,
    context: dict[str, Any],
    dossier: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    dossier = dict(dossier or context.get("corpus_dossier") or {})
    work_title = str(context.get("work_title") or dossier.get("work_title") or "")
    composer = str(
        context.get("composer")
        or context.get("composer_guess")
        or dossier.get("composer")
        or ""
    )
    findings = _findings_from_hygiene(
        dossier,
        composer=composer,
        work_title=work_title,
        raw_message=str(context.get("raw_message") or ""),
        html=html,
    )
    findings.extend(
        _expert_hard_flaw_findings(
            work_title=work_title, composer=composer, html=html, dossier=dossier
        )
    )
    # Product prose must never leak process tags into the guide body / H1 path.
    blob = f"{html}\n{dossier.get('listening_thesis') or ''}\n{dossier.get('work_introduction') or ''}"
    if re.search(r"(?i)\b(CRITIQUE\s*LOCK|REVIEW\s*REPAIR)\b", blob):
        findings.append(
            {
                "severity": "high",
                "code": "process_lock_in_product_prose",
                "note": "Product guide/dossier still contains CRITIQUE LOCK or REVIEW REPAIR process tags",
                "evidence": "process_lock",
                "kind": "hard_flaw",
            }
        )
    title_l = (work_title or "").lower()
    if ("=" in (work_title or "") and title_l.count("/") >= 1) or re.search(
        r"(?i)/\s*(ges|rom)\s*$", work_title or ""
    ):
        findings.append(
            {
                "severity": "high",
                "code": "packaging_title_pollution",
                "note": "work_title still looks like a Discogs multi-language packaging dump",
                "evidence": (work_title or "")[:120],
                "kind": "hard_flaw",
            }
        )
    return findings


def _scrub_text(value: str, markers: list[str]) -> str:
    out = value
    for m in markers:
        if not m:
            continue
        out = re.sub(re.escape(m), "", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out).strip(" —,-;")
    return out


def _scrub_structure(obj: Any, markers: list[str]) -> Any:
    if isinstance(obj, str):
        return _scrub_text(obj, markers)
    if isinstance(obj, list):
        cleaned = []
        for item in obj:
            if isinstance(item, str):
                text = _scrub_text(item, markers)
                if text and not any(m.lower() in text.lower() for m in markers if len(m) >= 4):
                    # drop lines still dominated by foreign rhetoric
                    low = text.lower()
                    if sum(1 for m in markers if m.lower() in low) >= 2:
                        continue
                    cleaned.append(text)
                elif text:
                    cleaned.append(text)
            elif isinstance(item, dict):
                cleaned.append(_scrub_structure(item, markers))
            else:
                cleaned.append(item)
        return cleaned
    if isinstance(obj, dict):
        return {k: _scrub_structure(v, markers) for k, v in obj.items()}
    return obj


def apply_review_repairs(context: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Deterministic proofread/repair of dossiers from expert review findings."""
    log: list[str] = []
    findings = [f for f in (report.get("findings") or []) if isinstance(f, dict)]
    codes = {str(f.get("code") or "") for f in findings}
    corrections = [str(c) for c in (report.get("required_corrections") or []) if c]
    for c in corrections:
        if c not in list(context.get("critique_corrections") or []):
            context.setdefault("critique_corrections", []).append(c)

    work_title = str(context.get("work_title") or "")
    composer = str(context.get("composer") or context.get("composer_guess") or "")

    dossier = dict(context.get("corpus_dossier") or {})
    dossier, hygiene = apply_identity_hygiene(
        dossier, composer=composer, work_title=work_title, raw_message=str(context.get("raw_message") or "")
    )
    if hygiene.findings:
        log.append("identity_hygiene:" + ",".join(f.code for f in hygiene.findings))

    markers = list(
        identity_lock_alien_markers(
            work_title=work_title,
            work_hint=str(context.get("work_hint") or ""),
            raw_message=str(context.get("raw_message") or ""),
        )
    )
    for f in findings:
        if f.get("code") in {
            "foreign_family_dossier",
            "foreign_chamber_in_guide",
            "h1_title_drift",
        }:
            evid = str(f.get("evidence") or "")
            markers.extend([x.strip() for x in evid.split(",") if x.strip()])
            did = str(dossier.get("dossier_id") or "")
            if did.startswith("family:"):
                markers.extend(scrub_markers_for_family(did.split(":", 1)[-1]))
                dossier["dossier_id"] = ""
                log.append("cleared_foreign_family")

    if codes & {
        "foreign_chamber_in_guide",
        "foreign_family_dossier",
        "intent_betrayal",
        "portrait_composer_mismatch",
        "h1_title_drift",
        "h1_celebrity_pollution",
        "form_title_mismatch",
    }:
        dossier = _scrub_structure(dossier, markers)
        log.append("scrubbed_dossier_markers")

    if "portrait_composer_mismatch" in codes or not (
        isinstance(dossier.get("composer_portrait"), dict)
        and (dossier.get("composer_portrait") or {}).get("image_url")
    ):
        if "portrait_composer_mismatch" in codes:
            dossier["composer_portrait"] = {}
            log.append("cleared_portrait")

    # Ensure listening map / anatomy scaffolds when review flagged them missing
    depth = dict(context.get("depth_dossier") or {})
    width = dict(context.get("width_dossier") or {})
    listening_map = list(depth.get("listening_map") or dossier.get("listening_map") or [])
    depth_points = list(depth.get("depth_points") or dossier.get("depth_points") or [])

    if "missing_listening_map" in codes or not listening_map:
        listening_map = [
            {"label": "Opening", "cue": f"Lock the primary motive of {work_title or 'the work'}."},
            {"label": "Development / middle", "cue": "Track contrast, intensification, and the turning point."},
            {"label": "Close", "cue": "Hear how the return remembers the opening — altered."},
        ]
        depth["listening_map"] = listening_map
        dossier["listening_map"] = listening_map
        log.append("injected_listening_map")

    if "missing_anatomy" in codes or len(depth_points) < 3:
        depth_points = [
            f"Form landmarks for {work_title or 'this work'}: establish the unit the ear should lock onto first.",
            "Map structural turns with concrete ear cues (texture, harmony, register).",
            "Notice how the close transforms the opening material.",
        ]
        depth["depth_points"] = depth_points
        dossier["depth_points"] = depth_points
        log.append("injected_anatomy_points")

    # Pin refuse topics so synthesize/compose scrubbers stay honest
    refuse = list(context.get("refuse_topics") or [])
    for m in markers:
        if m and m not in refuse:
            refuse.append(m)
    context["refuse_topics"] = refuse[:24]

    # Park review corrections in caveats only — never inject REVIEW REPAIR into product thesis.
    if corrections:
        caveats = list(dossier.get("myths_and_caveats") or [])
        for c in corrections[:5]:
            if c not in caveats:
                caveats.insert(0, c)
        dossier["myths_and_caveats"] = caveats
        log.append("parked_review_corrections_in_caveats")
    from aulos_skills.prose_hygiene import (
        clean_packaging_work_title,
        partition_dossier_languages,
        scrub_dossier_process_locks,
    )

    if work_title:
        work_title = clean_packaging_work_title(work_title, composer=composer)
        context["work_title"] = work_title
        dossier["work_title"] = work_title
    dossier = scrub_dossier_process_locks(partition_dossier_languages(dossier))

    context["corpus_dossier"] = dossier
    if width:
        width["salon_dossier"] = dict(width.get("salon_dossier") or dossier)
        width["listening_map"] = listening_map
        context["width_dossier"] = width
    depth["listening_map"] = listening_map
    depth["depth_points"] = depth_points
    context["depth_dossier"] = depth
    context["revise_repair_log"] = log
    context["revise_mode"] = True
    return {"log": log, "markers": markers[:20], "corrections": corrections[:8]}


def proofread_with_llm(
    context: dict[str, Any],
    report: dict[str, Any],
    *,
    llm_complete: LlmComplete,
) -> dict[str, Any]:
    """LLM proofread: rewrite dossier craft fields to address hard-flaw corrections."""
    dossier = dict(context.get("corpus_dossier") or {})
    work_title = str(context.get("work_title") or "")
    composer = str(context.get("composer") or "")
    findings = list(report.get("findings") or [])[:12]
    corrections = list(report.get("required_corrections") or context.get("critique_corrections") or [])[:8]
    v1_html = str(
        ((context.get("generation_rounds") or {}).get("draft_v1") or {}).get("guide_html") or ""
    )[:3500]
    prompt = (
        "你是音乐导赏校对编辑。根据专家硬伤报告，修缮 dossier 字段（不要写整页 HTML）。\n"
        "只输出 JSON：\n"
        '{"listening_thesis":"…","work_introduction":"…",'
        '"width_points":["…"],"depth_points":["…"],'
        '"listening_map":[{"label":"…","cue":"…"}],'
        '"myths_and_caveats":["…"],"repair_notes":["已修…"]}\n'
        "必须消除报告中的硬伤；禁止引入无关作品/错误肖像描述。\n"
        "listening_thesis / work_introduction 必须是读者可读的产品文案："
        "禁止写入 CRITIQUE LOCK、REVIEW REPAIR、richness_empty 等过程标签。\n"
        "英文层字段用英文；中文内容放到 zh 层，不要把中文塞进 EN listening_thesis。\n"
        f"work={work_title!r} composer={composer!r}\n"
        f"findings={json.dumps(findings, ensure_ascii=False)[:2000]}\n"
        f"corrections={json.dumps(corrections, ensure_ascii=False)[:1200]}\n"
        f"current_thesis={str(dossier.get('listening_thesis') or '')[:400]!r}\n"
        f"draft_v1_excerpt:\n{v1_html}\n"
    )
    raw = ""
    try:
        raw = llm_complete(prompt) or ""
    except Exception:  # noqa: BLE001
        return {"applied": False, "reason": "llm_error"}
    data = _parse_json_obj(raw)
    if not data:
        return {"applied": False, "reason": "parse_fail"}

    if data.get("listening_thesis"):
        dossier["listening_thesis"] = str(data["listening_thesis"])
    if data.get("work_introduction"):
        dossier["work_introduction"] = str(data["work_introduction"])
    if isinstance(data.get("width_points"), list) and data["width_points"]:
        dossier["width_points"] = [str(x) for x in data["width_points"][:8]]
    if isinstance(data.get("depth_points"), list) and data["depth_points"]:
        dossier["depth_points"] = [str(x) for x in data["depth_points"][:8]]
        depth = dict(context.get("depth_dossier") or {})
        depth["depth_points"] = list(dossier["depth_points"])
        context["depth_dossier"] = depth
    if isinstance(data.get("listening_map"), list) and data["listening_map"]:
        listening_map = []
        for row in data["listening_map"][:6]:
            if isinstance(row, dict):
                listening_map.append(
                    {"label": str(row.get("label") or ""), "cue": str(row.get("cue") or "")}
                )
        if listening_map:
            dossier["listening_map"] = listening_map
            depth = dict(context.get("depth_dossier") or {})
            depth["listening_map"] = listening_map
            context["depth_dossier"] = depth
    if isinstance(data.get("myths_and_caveats"), list):
        dossier["myths_and_caveats"] = [str(x) for x in data["myths_and_caveats"][:8]]

    from aulos_skills.prose_hygiene import partition_dossier_languages

    dossier = partition_dossier_languages(dossier)
    context["corpus_dossier"] = dossier
    notes = [str(x) for x in (data.get("repair_notes") or []) if x][:6]
    log = list(context.get("revise_repair_log") or [])
    log.append("llm_proofread")
    context["revise_repair_log"] = log
    return {"applied": True, "repair_notes": notes}


def score_draft_with_hard_flaws(
    *,
    html: str,
    context: dict[str, Any],
    phase: str = "compose",
    findings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Process scorecard + hard-flaw penalty so v1/v2 can diverge substantively."""
    trigger = "listening.revise" if phase == "revise" else "listening.compose"
    card = score_node(
        trigger,
        context,
        {"guide_html": html, "corpus_dossier": context.get("corpus_dossier") or {}},
    )
    flaws = list(findings) if findings is not None else scan_hard_flaws(html=html, context=context)
    high = sum(1 for f in flaws if f.get("severity") == "high")
    medium = sum(1 for f in flaws if f.get("severity") == "medium")

    earned = int(card.earned) if card else 0
    max_possible = int(card.max_possible) if card else 18
    # Explicit hard-flaw budget (6 pts) — cleared only when flaws are gone
    flaw_budget = 6
    flaw_earned = max(0, flaw_budget - (high * 3 + medium * 1))
    earned_adj = earned + flaw_earned
    max_adj = max_possible + flaw_budget
    pct = round(100.0 * earned_adj / max_adj, 1) if max_adj else 0.0
    if high:
        band = "weak" if pct < 70 else "fair"
    elif pct >= 90:
        band = "strong"
    elif pct >= 75:
        band = "fair"
    else:
        band = "weak"

    nodes = [card.to_dict()] if card else []
    return {
        "schema": "aulos.process_scorecard/v1",
        "nodes": nodes,
        "rollup": {
            "earned": earned_adj,
            "max_possible": max_adj,
            "pct": pct,
            "band": band,
            "hard_fail": bool(card.hard_fail) if card else bool(high),
            "hard_flaws_high": high,
            "hard_flaws_medium": medium,
            "hard_flaws_remaining": len(flaws),
            "flaw_budget_earned": flaw_earned,
            "flaw_budget_max": flaw_budget,
        },
        "hard_flaws": flaws[:20],
    }


def rescore_draft_v1_with_report(context: dict[str, Any], report: dict[str, Any]) -> None:
    rounds = dict(context.get("generation_rounds") or {})
    v1 = dict(rounds.get("draft_v1") or {})
    html = str(v1.get("guide_html") or context.get("guide_html") or "")
    if not html:
        return
    findings = [f for f in (report.get("findings") or []) if isinstance(f, dict)]
    v1["process_scorecard"] = score_draft_with_hard_flaws(
        html=html, context=context, phase="compose", findings=findings
    )
    v1["review_findings"] = findings[:20]
    rounds["draft_v1"] = v1
    context["generation_rounds"] = rounds
