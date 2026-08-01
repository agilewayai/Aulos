"""Adversarial process review — IntentLock + hybrid Critic (SPEC-018 / ADR-005)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from aulos_skills.decontam import (
    DECONTAM_TRIGGERS,
    resolve_scrub_markers,
    validate_node_outputs,
)
from aulos_skills.identity_lock import (
    build_identity_lock,
    dossier_betrays_identity_lock,
)

LLM_CRITIC_TRIGGERS = frozenset(
    {"listening.synthesize", "listening.compose", "listening.revise"}
)

# Sync optional completer: prompt -> reply text (tests / in-process inject)
LlmCriticComplete = Callable[[str], str | None]


@dataclass
class ReviewDeviation:
    code: str
    summary: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "summary": self.summary}


@dataclass
class ReviewReport:
    ok: bool
    layer: str  # deterministic | intent_critic | llm_critic
    trigger: str
    verdict: str  # PASS | FAIL
    deviations: list[ReviewDeviation] = field(default_factory=list)
    required_corrections: list[str] = field(default_factory=list)
    markers_used: list[str] = field(default_factory=list)
    repaired: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "layer": self.layer,
            "trigger": self.trigger,
            "verdict": self.verdict,
            "deviations": [d.to_dict() for d in self.deviations],
            "required_corrections": list(self.required_corrections),
            "markers_used": list(self.markers_used),
            "repaired": self.repaired,
        }


def freeze_intent_lock_dict(
    *,
    work_title: str,
    composer: str,
    work_hint: str = "",
    raw_message: str = "",
    work_id: str | None = None,
    conflict_markers: list[str] | None = None,
    source: str = "intake",
) -> dict[str, Any]:
    """Build the frozen IntentLock payload for chain context (SPEC-018)."""
    lock = build_identity_lock(
        work_title=work_title,
        work_hint=work_hint,
        raw_message=raw_message,
    )
    markers = list(conflict_markers or [])
    for m in lock.alien_markers:
        if m not in markers:
            markers.append(m)
    return {
        "work_title": work_title,
        "composer": composer,
        "catalog_numbers": sorted(lock.catalog_numbers),
        "form_families": sorted(lock.form_families),
        "alien_markers": list(lock.alien_markers),
        "work_id": work_id or None,
        "conflict_markers": markers,
        "source": source,
    }


def intent_lock_from_context(context: dict[str, Any]) -> dict[str, Any]:
    frozen = dict(context.get("intent_lock") or {})
    if frozen.get("work_title"):
        return frozen
    # Fallback rebuild (should be rare after intake)
    return freeze_intent_lock_dict(
        work_title=str(context.get("work_title") or ""),
        composer=str(context.get("composer") or context.get("composer_guess") or ""),
        work_hint=str(context.get("work_hint") or ""),
        raw_message=str(context.get("raw_message") or ""),
        work_id=str(context.get("work_id") or "") or None,
        conflict_markers=list(context.get("conflict_markers") or []),
        source="rebuilt",
    )


def record_review_event(context: dict[str, Any], report: ReviewReport) -> None:
    events = list(context.get("review_events") or [])
    events.append(report.to_dict())
    context["review_events"] = events
    if not report.ok and not report.repaired:
        context["review_failed"] = True


def _dossier_from_outputs(trigger: str, outputs: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if trigger == "listening.synthesize":
        return dict(outputs.get("corpus_dossier") or context.get("corpus_dossier") or {})
    if trigger == "listening.width":
        width = dict(outputs.get("width_dossier") or {})
        return dict(width.get("salon_dossier") or outputs.get("corpus_dossier") or context.get("corpus_dossier") or {})
    if trigger == "listening.compose" or trigger == "listening.revise":
        return dict(context.get("corpus_dossier") or {})
    if trigger == "listening.depth":
        return {
            "depth_points": list((outputs.get("depth_dossier") or {}).get("depth_points") or []),
            "form": str((outputs.get("depth_dossier") or {}).get("form") or ""),
            "listening_map": list((outputs.get("depth_dossier") or {}).get("listening_map") or []),
        }
    return {}


def deterministic_review(
    trigger: str,
    context: dict[str, Any],
    outputs: dict[str, Any],
    *,
    family: dict[str, Any] | None = None,
) -> ReviewReport:
    """SPEC-009 decontam + IntentLock betrayal as one deterministic ReviewReport."""
    deviations: list[ReviewDeviation] = []
    corrections: list[str] = []
    markers = resolve_scrub_markers(context)

    if trigger in DECONTAM_TRIGGERS:
        deco = validate_node_outputs(trigger, context, outputs, family=family)
        if not deco.ok:
            for f in deco.findings:
                deviations.append(
                    ReviewDeviation(code=f"decontam:{f.marker}", summary=f"Alien marker in {f.where}")
                )
            corrections.append("Remove foreign chambers / markers that are not the locked work.")
            if deco.foreign_family:
                corrections.append(f"Refuse family pack {deco.foreign_family}.")

    intent = intent_lock_from_context(context)
    dossier = _dossier_from_outputs(trigger, outputs, context)
    html = str(outputs.get("guide_html") or context.get("guide_html") or "")
    betrays = dossier_betrays_identity_lock(
        dossier,
        work_title=str(intent.get("work_title") or ""),
        work_hint=str(context.get("work_hint") or ""),
        raw_message=str(context.get("raw_message") or ""),
    )
    if not betrays and html and intent.get("alien_markers"):
        from aulos_skills.decontam import marker_in_text

        hits = [
            m
            for m in intent["alien_markers"]
            if m and marker_in_text(str(m), html)
        ]
        if hits and intent.get("catalog_numbers"):
            # HTML still carries opposing-family aliens
            betrays = True
            deviations.append(
                ReviewDeviation(
                    code="html_alien",
                    summary=f"Guide HTML contains lock aliens: {', '.join(hits[:4])}",
                )
            )

    if betrays:
        deviations.append(
            ReviewDeviation(
                code="intent_betrayal",
                summary=(
                    f"Output drifted from IntentLock "
                    f"({intent.get('work_title') or 'locked work'})"
                ),
            )
        )
        title = str(intent.get("work_title") or "the locked work")
        corrections.append(f"Narrative must stay on: {title}")
        if intent.get("catalog_numbers"):
            corrections.append(
                "Preserve catalog numbers: " + ", ".join(intent["catalog_numbers"])
            )
        if intent.get("alien_markers"):
            corrections.append(
                "Forbidden as work body: " + ", ".join(list(intent["alien_markers"])[:8])
            )

    ok = not deviations
    return ReviewReport(
        ok=ok,
        layer="deterministic",
        trigger=trigger,
        verdict="PASS" if ok else "FAIL",
        deviations=deviations,
        required_corrections=corrections,
        markers_used=markers,
    )


def _parse_critic_json(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def build_critic_prompt(context: dict[str, Any], outputs: dict[str, Any], trigger: str) -> str:
    intent = intent_lock_from_context(context)
    dossier = _dossier_from_outputs(trigger, outputs, context)
    slice_doc = {
        "work_title": dossier.get("work_title"),
        "listening_thesis": dossier.get("listening_thesis"),
        "work_introduction": dossier.get("work_introduction"),
        "form": dossier.get("form"),
        "zh_thesis": (dossier.get("zh") or dossier.get("zh_hans") or {}).get("listening_thesis")
        if isinstance(dossier.get("zh") or dossier.get("zh_hans"), dict)
        else None,
    }
    html = str(outputs.get("guide_html") or "")[:1200]
    return (
        "You are Aulos Intent Critic — adversarial reviewer. Review ONLY; never write a guide.\n"
        "Judge whether the node output stayed on IntentLock. "
        "Do NOT prefer a more famous work by the same composer or performer.\n"
        f"IntentLock JSON:\n{json.dumps(intent, ensure_ascii=False)}\n\n"
        f"Trigger: {trigger}\n"
        f"Output slice JSON:\n{json.dumps(slice_doc, ensure_ascii=False)}\n"
        f"HTML excerpt:\n{html}\n\n"
        "Return ONLY JSON: "
        '{"verdict":"PASS"|"FAIL","deviations":[{"code":"","summary":""}],'
        '"required_corrections":["..."],"preserved_lock_check":"..."}\n'
        "FAIL if narrative swaps form family, drops locked catalog numbers for foreign ones, "
        "or elevates performer meme over the locked work."
    )


def intent_critic_review(
    trigger: str,
    context: dict[str, Any],
    outputs: dict[str, Any],
    *,
    llm_complete: LlmCriticComplete | None = None,
) -> ReviewReport:
    """Hybrid Critic: optional LLM JSON, else deterministic IntentLock betrayal (SPEC-018)."""
    if trigger not in LLM_CRITIC_TRIGGERS:
        return ReviewReport(
            ok=True, layer="intent_critic", trigger=trigger, verdict="PASS"
        )

    # Always compute deterministic betrayal baseline
    base = deterministic_review(trigger, context, outputs)
    intent_only = ReviewReport(
        ok=base.ok,
        layer="intent_critic",
        trigger=trigger,
        verdict=base.verdict,
        deviations=[d for d in base.deviations if d.code.startswith("intent") or d.code == "html_alien"],
        required_corrections=list(base.required_corrections),
        markers_used=list(base.markers_used),
    )
    # If no intent-specific issues, still keep PASS unless LLM says FAIL
    if not intent_only.deviations:
        intent_only.ok = True
        intent_only.verdict = "PASS"
        intent_only.required_corrections = []

    complete = llm_complete or context.get("llm_critic_complete")
    if not callable(complete):
        return intent_only

    prompt = build_critic_prompt(context, outputs, trigger)
    try:
        reply = complete(prompt)
    except Exception:  # noqa: BLE001
        return intent_only
    data = _parse_critic_json(str(reply or ""))
    if not data:
        return intent_only

    verdict = str(data.get("verdict") or "PASS").upper()
    deviations: list[ReviewDeviation] = list(intent_only.deviations)
    for item in data.get("deviations") or []:
        if isinstance(item, dict) and item.get("summary"):
            deviations.append(
                ReviewDeviation(
                    code=str(item.get("code") or "llm_critic"),
                    summary=str(item.get("summary")),
                )
            )
    corrections = list(intent_only.required_corrections)
    for c in data.get("required_corrections") or []:
        if c and str(c) not in corrections:
            corrections.append(str(c))
    ok = verdict == "PASS" and not any(d.code.startswith("intent") for d in deviations)
    if verdict == "FAIL":
        ok = False
    return ReviewReport(
        ok=ok,
        layer="llm_critic",
        trigger=trigger,
        verdict="PASS" if ok else "FAIL",
        deviations=deviations,
        required_corrections=corrections,
        markers_used=list(intent_only.markers_used),
    )


def apply_critique_to_context(context: dict[str, Any], report: ReviewReport) -> None:
    if report.ok:
        return
    corrections = list(context.get("critique_corrections") or [])
    for c in report.required_corrections:
        if c not in corrections:
            corrections.append(c)
    context["critique_corrections"] = corrections
    intent = intent_lock_from_context(context)
    refuse = list(context.get("refuse_topics") or [])
    for m in intent.get("alien_markers") or []:
        if m not in refuse:
            refuse.append(m)
    context["refuse_topics"] = refuse
    # Also expand conflict markers for scrub path
    markers = list(context.get("conflict_markers") or [])
    for m in intent.get("alien_markers") or []:
        if m not in markers:
            markers.append(m)
    context["conflict_markers"] = markers


def review_llm_enabled(context: dict[str, Any]) -> bool:
    if "review_llm_enabled" in context:
        return bool(context.get("review_llm_enabled"))
    return True  # default on; deterministic critic always runs; LLM only if callable
