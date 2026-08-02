"""SkillRuntime — execute domain-runtime listening skills with observability."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from aulos_skills.adversarial_review import (
    LLM_CRITIC_TRIGGERS,
    apply_critique_to_context,
    deterministic_review,
    freeze_intent_lock_dict,
    intent_critic_review,
    record_review_event,
    review_llm_enabled,
)
from aulos_skills.ambient_agent import select_ambient
from aulos_skills.ambient_playlist import resolve_ambient_audio
from aulos_skills.config import get_settings
from aulos_skills.decontam import (
    DECONTAM_TRIGGERS,
    apply_rework_hints,
    record_decontam_event,
    resolve_scrub_markers,
    validate_node_outputs,
)
from aulos_skills.identity import resolve_identity
from aulos_skills.registry import SkillManifest, discover_skills, skill_body
from aulos_skills.salon_codex import (
    coerce_dict,
    composer_to_dossier,
    dossier_richness,
    empty_dossier,
    family_to_dossier,
    merge_dossiers,
    parse_llm_dossier_json,
)
from aulos_skills.html_bits import point_text, point_texts
from aulos_skills.process_scorecard import record_node_scorecard, rollup_process

_DECONTAM_MAX_REWORK = 1
_CRITIC_MAX_REWORK = 1


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _package_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass
class SkillStepResult:
    id: str
    title: str
    status: str
    thinking: str
    detail: str
    skill_id: str
    skill_version: str
    started_at: str | None = None
    finished_at: str | None = None
    outputs: dict[str, Any] = field(default_factory=dict)

    def to_workflow_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "thinking": self.thinking,
            "detail": self.detail,
            "skill_id": self.skill_id,
            "skill_version": self.skill_version,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


@dataclass
class SkillRunReport:
    steps: list[SkillStepResult]
    context: dict[str, Any]
    skill_versions: dict[str, str]
    guide_html: str = ""
    summary: str = ""
    work_title: str = ""
    composer: str = ""
    eval_pass: bool = True
    eval_score: int = 0
    source: str = "skills"


class SkillRuntime:
    """Discover and run Aulos domain-runtime skills."""

    def __init__(self, roots: list[Path] | None = None) -> None:
        settings = get_settings()
        self.roots = roots or settings.resolved_roots(_package_root())
        self.skills = {s.skill_id: s for s in discover_skills(self.roots)}
        self.by_trigger: dict[str, SkillManifest] = {}
        for skill in self.skills.values():
            for trigger in skill.triggers:
                self.by_trigger[trigger] = skill

    def list_skills(self, *, layer: str | None = None) -> list[dict[str, Any]]:
        rows = []
        for s in sorted(self.skills.values(), key=lambda x: x.skill_id):
            if layer and s.layer != layer:
                continue
            rows.append(
                {
                    "id": s.skill_id,
                    "name": s.name,
                    "layer": s.layer,
                    "runtime": s.runtime,
                    "version": s.version,
                    "summary": s.summary,
                    "triggers": list(s.triggers),
                    "observability_title": s.observability_title,
                    "enabled": True,
                }
            )
        return rows

    def get_by_trigger(self, trigger: str) -> SkillManifest | None:
        return self.by_trigger.get(trigger)

    def run_trigger(
        self,
        trigger: str,
        context: dict[str, Any],
        *,
        disabled_skill_ids: set[str] | None = None,
    ) -> SkillStepResult:
        skill = self.get_by_trigger(trigger)
        if skill is None:
            raise KeyError(f"No skill registered for trigger: {trigger}")
        step_id = trigger.split(".", 1)[-1]
        title = skill.observability_title or skill.name
        started = _utcnow()
        disabled = disabled_skill_ids or set()
        if skill.skill_id in disabled:
            return SkillStepResult(
                id=step_id,
                title=title,
                status="skipped",
                thinking=f"Skill {skill.skill_id} disabled in ops — step skipped",
                detail="skipped by operator policy",
                skill_id=skill.skill_id,
                skill_version=skill.version,
                started_at=started,
                finished_at=_utcnow(),
                outputs={},
            )
        thinking = self._thinking_from_skill(skill)
        outputs = self._dispatch(trigger, skill, context)
        detail = self._detail_from_outputs(trigger, outputs)
        if trigger == "listening.intake":
            # Freeze IntentLock immediately so later nodes cannot rewrite truth.
            self._freeze_intent_lock(context, outputs)
        if trigger in DECONTAM_TRIGGERS or trigger in LLM_CRITIC_TRIGGERS:
            outputs, detail = self._adversarial_review_gate(trigger, skill, context, outputs, detail)
        context.update(outputs)
        # SPEC-019 process scorecard — after gate so fidelity sees review_events
        card = record_node_scorecard(context, trigger, outputs)
        if card is not None and card.findings:
            detail = f"{detail} | score {card.pct}% {card.band}"
        return SkillStepResult(
            id=step_id,
            title=title,
            status="completed",
            thinking=thinking,
            detail=detail,
            skill_id=skill.skill_id,
            skill_version=skill.version,
            started_at=started,
            finished_at=_utcnow(),
            outputs=outputs,
        )

    def _freeze_intent_lock(self, context: dict[str, Any], outputs: dict[str, Any]) -> None:
        existing = dict(context.get("intent_lock") or {})
        if existing.get("work_title"):
            # Already frozen (e.g. API Discogs pre-lock) — keep truth; sync scrub mirrors.
            from aulos_skills.release_structure import enrich_lock_catalogs, structure_from_context

            lock = enrich_lock_catalogs(existing, structure_from_context({**context, **outputs}))
            outputs["intent_lock"] = lock
            context["intent_lock"] = lock
            if lock.get("conflict_markers"):
                markers = list(outputs.get("conflict_markers") or context.get("conflict_markers") or [])
                for m in lock["conflict_markers"]:
                    if m not in markers:
                        markers.append(m)
                outputs["conflict_markers"] = markers
                context["conflict_markers"] = markers
            return
        work_title = str(outputs.get("work_title") or context.get("work_title") or "")
        composer = str(
            outputs.get("composer")
            or outputs.get("composer_guess")
            or context.get("composer")
            or ""
        )
        prov = dict((context.get("kb_dossier") or {}).get("_provenance") or {})
        source = "intake"
        if prov.get("source") == "discogs" or prov.get("discogs"):
            source = "discogs"
        elif outputs.get("work_id") or context.get("work_id"):
            source = "catalog"
        lock = freeze_intent_lock_dict(
            work_title=work_title,
            composer=composer,
            work_hint=str(context.get("work_hint") or ""),
            raw_message=str(context.get("raw_message") or ""),
            work_id=str(outputs.get("work_id") or context.get("work_id") or "") or None,
            conflict_markers=list(outputs.get("conflict_markers") or context.get("conflict_markers") or []),
            source=source,
        )
        from aulos_skills.release_structure import enrich_lock_catalogs, structure_from_context

        lock = enrich_lock_catalogs(lock, structure_from_context({**context, **outputs}))
        # Prefer intake-collected catalog numbers when richer
        intake_nums = list(outputs.get("identity_lock_numbers") or [])
        if intake_nums:
            lock["catalog_numbers"] = sorted(
                {*list(lock.get("catalog_numbers") or []), *intake_nums}
            )
        outputs["intent_lock"] = lock
        context["intent_lock"] = lock
        # Keep flat mirrors for scrubbers
        if lock.get("conflict_markers"):
            outputs["conflict_markers"] = list(lock["conflict_markers"])
            context["conflict_markers"] = list(lock["conflict_markers"])

    def _review_milestone_step(
        self, trigger: str, context: dict[str, Any]
    ) -> SkillStepResult | None:
        """Atelier-visible review milestone after synthesize/compose."""
        if trigger not in LLM_CRITIC_TRIGGERS:
            return None
        events = list(context.get("review_events") or [])
        relevant = [e for e in events if e.get("trigger") == trigger]
        if not relevant:
            return None
        last = relevant[-1]
        verdict = str(last.get("verdict") or "PASS")
        repaired = bool(last.get("repaired"))
        if not last.get("ok") and not repaired:
            status = "failed"
            detail = "本意偏离已拦截 — " + "; ".join(
                str(d.get("summary") or d.get("code") or "")
                for d in (last.get("deviations") or [])[:3]
            )
        elif repaired:
            status = "completed"
            detail = f"Review rework ok ({last.get('layer')})"
        else:
            status = "completed"
            detail = f"Review PASS ({last.get('layer')})"
        corrections = list(context.get("critique_corrections") or [])
        thinking = (
            "Intent Critic — review only; lock is truth."
            if not corrections
            else "Intent Critic corrections: " + "; ".join(corrections[:3])
        )
        short = trigger.rsplit(".", 1)[-1]
        return SkillStepResult(
            id=f"review-{short}",
            title=f"Review ({short})",
            status=status,
            thinking=thinking,
            detail=detail[:480],
            skill_id="listening.review",
            skill_version="1",
            started_at=_utcnow(),
            finished_at=_utcnow(),
            outputs={"verdict": verdict, "layer": last.get("layer"), "ok": last.get("ok")},
        )

    def _adversarial_review_gate(
        self,
        trigger: str,
        skill: SkillManifest,
        context: dict[str, Any],
        outputs: dict[str, Any],
        detail: str,
    ) -> tuple[dict[str, Any], str]:
        """Deterministic review every enrich node; LLM/intent Critic on synthesize+compose."""
        family_snap = dict(context.get("_last_matched_family") or {})

        # --- Deterministic layer (SPEC-009 + IntentLock) ---
        if trigger in DECONTAM_TRIGGERS:
            for attempt in range(_DECONTAM_MAX_REWORK + 1):
                report = deterministic_review(
                    trigger, context, outputs, family=family_snap or None
                )
                # Map to decontam for back-compat events when alien markers only
                deco = validate_node_outputs(
                    trigger, context, outputs, family=family_snap or None
                )
                if report.ok:
                    if attempt > 0:
                        record_decontam_event(
                            context,
                            trigger=trigger,
                            attempt=attempt,
                            report=deco,
                            repaired=True,
                        )
                        report.repaired = True
                        record_review_event(context, report)
                        detail = f"{detail} | review-rework ok"
                    else:
                        record_review_event(context, report)
                    break

                if attempt >= _DECONTAM_MAX_REWORK:
                    record_decontam_event(
                        context,
                        trigger=trigger,
                        attempt=attempt,
                        report=deco,
                        repaired=False,
                    )
                    self._apply_decontam_scrub(trigger, context, outputs, report.markers_used)
                    if trigger == "listening.compose":
                        outputs = self._dispatch(trigger, skill, context)
                        report2 = deterministic_review(
                            trigger, context, outputs, family=family_snap or None
                        )
                        if not report2.ok:
                            html = str(outputs.get("guide_html") or "")
                            outputs["guide_html"] = self._scrub_html_markers(
                                html, list(context.get("conflict_markers") or [])
                            )
                            context["guide_html"] = outputs["guide_html"]
                    apply_critique_to_context(context, report)
                    record_review_event(context, report)
                    detail = (
                        f"{detail} | review-fail "
                        f"({', '.join(d.code for d in report.deviations[:4])})"
                    )
                    break

                apply_critique_to_context(context, report)
                apply_rework_hints(context, deco)
                self._apply_decontam_scrub(trigger, context, outputs, report.markers_used)
                outputs = self._dispatch(trigger, skill, context)
                family_snap = dict(context.get("_last_matched_family") or {})
                detail = self._detail_from_outputs(trigger, outputs)

        # --- Intent / LLM Critic on high-risk nodes (SPEC-018) ---
        if trigger in LLM_CRITIC_TRIGGERS and review_llm_enabled(context):
            for attempt in range(_CRITIC_MAX_REWORK + 1):
                critic = intent_critic_review(trigger, context, outputs)
                if critic.ok:
                    if attempt > 0:
                        critic.repaired = True
                    record_review_event(context, critic)
                    if attempt > 0:
                        detail = f"{detail} | critic-rework ok"
                    break
                if attempt >= _CRITIC_MAX_REWORK:
                    apply_critique_to_context(context, critic)
                    self._apply_decontam_scrub(
                        trigger, context, outputs, resolve_scrub_markers(context)
                    )
                    if trigger == "listening.compose":
                        outputs = self._dispatch(trigger, skill, context)
                        html = str(outputs.get("guide_html") or "")
                        outputs["guide_html"] = self._scrub_html_markers(
                            html, list(context.get("conflict_markers") or [])
                        )
                        context["guide_html"] = outputs["guide_html"]
                    record_review_event(context, critic)
                    detail = (
                        f"{detail} | critic-fail "
                        f"({', '.join(d.code for d in critic.deviations[:4])})"
                    )
                    break
                apply_critique_to_context(context, critic)
                self._apply_decontam_scrub(
                    trigger, context, outputs, resolve_scrub_markers(context)
                )
                outputs = self._dispatch(trigger, skill, context)
                detail = self._detail_from_outputs(trigger, outputs)

        return outputs, detail

    def _decontam_gate(
        self,
        trigger: str,
        skill: SkillManifest,
        context: dict[str, Any],
        outputs: dict[str, Any],
        detail: str,
    ) -> tuple[dict[str, Any], str]:
        """Back-compat alias → adversarial review gate."""
        return self._adversarial_review_gate(trigger, skill, context, outputs, detail)

    def _apply_decontam_scrub(
        self,
        trigger: str,
        context: dict[str, Any],
        outputs: dict[str, Any],
        markers: list[str],
    ) -> None:
        markers = markers or resolve_scrub_markers(context)
        context["conflict_markers"] = list(
            dict.fromkeys(
                list(context.get("conflict_markers") or []) + list(markers)
            )
        )
        work_title = str(
            outputs.get("work_title")
            or context.get("work_title")
            or ""
        )
        if trigger == "listening.synthesize":
            dossier = dict(outputs.get("corpus_dossier") or context.get("corpus_dossier") or {})
            if dossier:
                from aulos_skills.identity_hygiene import apply_identity_hygiene

                cleaned, hygiene = apply_identity_hygiene(
                    dossier,
                    composer=str(
                        outputs.get("composer")
                        or context.get("composer")
                        or context.get("composer_guess")
                        or ""
                    ),
                    work_title=work_title or str(dossier.get("work_title") or ""),
                    raw_message=str(context.get("raw_message") or ""),
                )
                if hygiene.markers:
                    context["conflict_markers"] = list(
                        dict.fromkeys(
                            list(context.get("conflict_markers") or []) + list(hygiene.markers)
                        )
                    )
                cleaned = self._scrub_foreign_chambers(
                    cleaned,
                    work_title=work_title or str(cleaned.get("work_title") or ""),
                    conflict_markers=list(context.get("conflict_markers") or []),
                    force_ambient_scrub=True,
                )
                outputs["corpus_dossier"] = cleaned
                context["corpus_dossier"] = cleaned
        elif trigger == "listening.width":
            width = dict(outputs.get("width_dossier") or context.get("width_dossier") or {})
            cleaned_width = self._scrub_foreign_chambers(
                width,
                work_title=work_title or str(context.get("work_title") or ""),
                conflict_markers=list(context.get("conflict_markers") or []),
                force_ambient_scrub=True,
            )
            salon = dict(cleaned_width.get("salon_dossier") or context.get("corpus_dossier") or {})
            if salon:
                salon = self._scrub_foreign_chambers(
                    salon,
                    work_title=work_title or str(salon.get("work_title") or ""),
                    conflict_markers=list(context.get("conflict_markers") or []),
                    force_ambient_scrub=True,
                )
                cleaned_width["salon_dossier"] = salon
                context["corpus_dossier"] = salon
            outputs["width_dossier"] = cleaned_width
            context["width_dossier"] = cleaned_width
        elif trigger == "listening.depth":
            depth = dict(outputs.get("depth_dossier") or context.get("depth_dossier") or {})
            # depth points live as lists — scrub via a thin dossier shell
            shell = {
                "depth_points": list(depth.get("depth_points") or []),
                "listening_map": list(depth.get("listening_map") or []),
                "practice_notes": list(depth.get("practice_notes") or []),
                "variation_deepdives": list(depth.get("variation_deepdives") or []),
                "sound_world": dict(depth.get("sound_world") or {}),
            }
            cleaned = self._scrub_foreign_chambers(
                shell,
                work_title=work_title,
                conflict_markers=list(context.get("conflict_markers") or []),
                force_ambient_scrub=True,
            )
            depth.update({k: cleaned[k] for k in shell if k in cleaned})
            outputs["depth_dossier"] = depth
            context["depth_dossier"] = depth
        elif trigger in ("listening.compose", "listening.revise"):
            dossier = dict(context.get("corpus_dossier") or {})
            if dossier:
                cleaned = self._scrub_foreign_chambers(
                    dossier,
                    work_title=work_title or str(dossier.get("work_title") or ""),
                    conflict_markers=list(context.get("conflict_markers") or []),
                    force_ambient_scrub=True,
                )
                context["corpus_dossier"] = cleaned
                width = dict(context.get("width_dossier") or {})
                if width.get("salon_dossier"):
                    width["salon_dossier"] = cleaned
                    context["width_dossier"] = width

    @staticmethod
    def _scrub_html_markers(html: str, markers: list[str]) -> str:
        """Drop block-level HTML chunks that still contain alien markers."""
        active = [m.lower() for m in markers if m and len(str(m)) >= 3]
        if not html or not active:
            return html
        import re as _re

        def drop_if_polluted(match: _re.Match[str]) -> str:
            chunk = match.group(0)
            low = chunk.lower()
            if any(m in low for m in active):
                return ""
            return chunk

        out = html
        # Prefer removing whole sections/articles/list items over silent word deletes.
        for pattern in (
            r"<section\b[^>]*>[\s\S]*?</section>",
            r"<article\b[^>]*>[\s\S]*?</article>",
            r"<li\b[^>]*>[\s\S]*?</li>",
            r"<p\b[^>]*>[\s\S]*?</p>",
            r"<h1\b[^>]*>[\s\S]*?</h1>",
        ):
            out = _re.sub(pattern, drop_if_polluted, out, flags=_re.I)
        return out

    def iter_listening_chain(
        self,
        *,
        message: str,
        work_hint: str | None = None,
        llm_enrichment: str | None = None,
        llm_dossier: dict[str, Any] | None = None,
        kb_dossier: dict[str, Any] | None = None,
        rag_hits: list[str] | None = None,
        rag_mode: str | None = None,
        disabled_skill_ids: set[str] | None = None,
        context_seed: dict[str, Any] | None = None,
    ):
        """Yield each SkillStepResult, then a final SkillRunReport."""
        context: dict[str, Any] = {
            "raw_message": message,
            "work_hint": work_hint or "",
            "llm_enrichment": llm_enrichment or "",
            "llm_dossier": dict(llm_dossier or {}),
            "kb_dossier": dict(kb_dossier or {}),
            "rag_hits": list(rag_hits or []),
            "rag_mode": rag_mode or "",
        }
        if context_seed:
            for key, value in context_seed.items():
                if key in {"raw_message", "work_hint"} and context.get(key):
                    continue
                context[key] = value
        # SPEC-034Δ: gateway program deepen loop bags travel via kb_dossier
        kb0 = dict(context.get("kb_dossier") or {})
        if kb0.get("program_iterations") and not context.get("program_iterations"):
            context["program_iterations"] = list(kb0.get("program_iterations") or [])
        if kb0.get("release_structure") and not context.get("release_structure"):
            context["release_structure"] = dict(kb0.get("release_structure") or {})
        # If enrichment looks like JSON dossier, parse into llm_dossier
        if not context["llm_dossier"] and llm_enrichment:
            parsed = parse_llm_dossier_json(str(llm_enrichment))
            if parsed:
                context["llm_dossier"] = parsed
        chain = [
            "listening.route",
            "listening.intake",
            "listening.corpus",
            "listening.synthesize",
            "listening.width",
            "listening.depth",
            "listening.compose",
            "listening.external_review",
            "listening.revise",
            "listening.eval",
        ]
        steps: list[SkillStepResult] = []
        versions: dict[str, str] = {}
        disabled = disabled_skill_ids or set()
        for trigger in chain:
            if trigger not in self.by_trigger:
                continue
            result = self.run_trigger(trigger, context, disabled_skill_ids=disabled)
            steps.append(result)
            versions[result.skill_id] = result.skill_version
            yield result
            review_step = self._review_milestone_step(trigger, context)
            if review_step is not None:
                steps.append(review_step)
                versions[review_step.skill_id] = review_step.skill_version
                yield review_step

        # If compose was skipped, ensure minimal guide exists for eval/UI
        if not context.get("guide_html") and context.get("work_title"):
            composed = self._run_compose(context)
            context.update(composed)

        eval_pass = bool(context.get("pass", True))
        eval_score = int(context.get("eval_score") or 0)
        # If eval skipped, soft-pass when guide exists
        if not any(s.id == "eval" and s.status == "completed" for s in steps):
            eval_pass = bool(context.get("guide_html"))
            eval_score = eval_score or (8 if eval_pass else 0)

        report = SkillRunReport(
            steps=steps,
            context=context,
            skill_versions=versions,
            guide_html=str(context.get("guide_html") or ""),
            summary=str(context.get("summary") or ""),
            work_title=str(context.get("work_title") or ""),
            composer=str(context.get("composer") or context.get("composer_guess") or ""),
            eval_pass=eval_pass,
            eval_score=eval_score,
            source="skills",
        )
        yield report

    def run_listening_chain(
        self,
        *,
        message: str,
        work_hint: str | None = None,
        llm_enrichment: str | None = None,
        llm_dossier: dict[str, Any] | None = None,
        kb_dossier: dict[str, Any] | None = None,
        rag_hits: list[str] | None = None,
        rag_mode: str | None = None,
        disabled_skill_ids: set[str] | None = None,
        context_seed: dict[str, Any] | None = None,
    ) -> SkillRunReport:
        report: SkillRunReport | None = None
        for item in self.iter_listening_chain(
            message=message,
            work_hint=work_hint,
            llm_enrichment=llm_enrichment,
            llm_dossier=llm_dossier,
            kb_dossier=kb_dossier,
            rag_hits=rag_hits,
            rag_mode=rag_mode,
            disabled_skill_ids=disabled_skill_ids,
            context_seed=context_seed,
        ):
            if isinstance(item, SkillRunReport):
                report = item
        assert report is not None
        return report
    def _thinking_from_skill(self, skill: SkillManifest) -> str:
        body = skill_body(skill)
        # Prefer first procedure-ish lines
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        proc = []
        capture = False
        for ln in lines:
            if ln.lower().startswith("## procedure"):
                capture = True
                continue
            if capture and ln.startswith("## "):
                break
            if capture and (ln[0].isdigit() or ln.startswith("-") or ln.startswith("*")):
                proc.append(ln.lstrip("-* ").strip())
        if proc:
            return " → ".join(proc[:4])
        return skill.summary or f"Executing {skill.skill_id}"

    def _detail_from_outputs(self, trigger: str, outputs: dict[str, Any]) -> str:
        if trigger == "listening.intake":
            return f"Normalized work: {outputs.get('work_title')}"
        if trigger == "listening.corpus":
            hit = outputs.get("corpus_hit")
            return "Corpus hit" if hit else "No curated dossier — cold research path"
        if trigger == "listening.synthesize":
            if outputs.get("synthesize_hit"):
                return f"Synthesized via {outputs.get('synthesize_source')}"
            return "Corpus already rich — synthesize pass-through"
        if trigger == "listening.width":
            points = point_texts(outputs.get("width_points") or [], limit=2)
            return "; ".join(points) if points else "Width dossier ready"
        if trigger == "listening.depth":
            points = point_texts(outputs.get("depth_points") or [], limit=2)
            return "; ".join(points) if points else "Depth dossier ready"
        if trigger == "listening.compose":
            return str(outputs.get("summary") or "Guide composed")[:280]
        if trigger == "listening.external_review":
            report = outputs.get("external_review_report") or {}
            return str(report.get("summary") or "External review ready")[:280]
        if trigger == "listening.revise":
            return str(outputs.get("summary") or "Guide revised after review")[:280]
        if trigger == "listening.eval":
            return f"score={outputs.get('eval_score')} pass={outputs.get('pass')} — {outputs.get('eval_notes')}"
        if trigger == "listening.route":
            return str(outputs.get("plan") or "Listening chain planned")
        return "ok"

    def _dispatch(self, trigger: str, skill: SkillManifest, context: dict[str, Any]) -> dict[str, Any]:
        if trigger == "listening.route":
            return self._run_route(context)
        if trigger == "listening.intake":
            return self._run_intake(context)
        if trigger == "listening.corpus":
            return self._run_corpus(skill, context)
        if trigger == "listening.synthesize":
            return self._run_synthesize(skill, context)
        if trigger == "listening.width":
            return self._run_width(context)
        if trigger == "listening.depth":
            return self._run_depth(context)
        if trigger == "listening.compose":
            return self._run_compose(context)
        if trigger == "listening.external_review":
            return self._run_external_review(context)
        if trigger == "listening.revise":
            return self._run_revise(context)
        if trigger == "listening.eval":
            return self._run_eval(context)
        return {"note": f"No deterministic executor for {trigger}; skill loaded only"}

    def _run_route(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "plan": (
            "intake → corpus → synthesize → width → depth → compose → "
            "external_review → revise → eval (Salon Codex + networked review round)"
            )
        }

    def _run_intake(self, context: dict[str, Any]) -> dict[str, Any]:
        from aulos_skills.intake_parse import guess_composer_and_title
        from aulos_skills.identity import load_catalog

        message = str(context.get("raw_message") or "")
        hint = str(context.get("work_hint") or "")
        text = f"{hint} {message}".strip()
        lowered = text.lower()

        from aulos_skills.work_resolver import resolve_listening_work

        kb = dict(context.get("kb_dossier") or {})
        resolved = resolve_listening_work(
            raw_message=message, work_hint=hint, kb_dossier=kb
        )
        identity = resolved.identity or resolve_identity(message, work_hint=hint)
        out = identity.to_context()
        # Overlay resolver fields (cleaned title + Catalog lock even on Discogs)
        for k, v in resolved.to_intake_fields().items():
            if v not in (None, "", [], {}):
                out[k] = v

        work_title = str(out.get("work_title") or "")
        composer = str(out.get("composer") or out.get("composer_guess") or "")

        if identity.status == "work" and identity.work_title and not work_title:
            work_title = identity.work_title
            composer = identity.composer_name or composer
        elif resolved.status != "work" or not work_title:
            cat = load_catalog()
            guessed = guess_composer_and_title(text, catalog_composers=cat.composers)
            if not work_title:
                work_title = guessed["work_title"] or "Unspecified classical work"
            if not composer:
                composer = identity.composer_name or guessed["composer"]
            if guessed.get("composer_id") and not out.get("composer_id"):
                out["composer_id"] = guessed["composer_id"]
            if identity.status == "composer_only" and not guessed["work_title"] and not work_title:
                work_title = f"{composer} — unspecified work" if composer else work_title

        # Discogs seed may still supply composer/title facts, but never wipe Catalog lock.
        prov = dict(kb.get("_provenance") or {})
        if prov.get("source") == "discogs" or prov.get("discogs"):
            if kb.get("composer") and not composer:
                composer = str(kb["composer"])
            if kb.get("work_title") and resolved.status != "work":
                from aulos_skills.prose_hygiene import clean_packaging_work_title

                work_title = clean_packaging_work_title(
                    str(kb["work_title"]), composer=composer
                )
            # Only clear wrong family/corpus when Catalog did NOT lock a work
            if resolved.status != "work" and identity.status != "work":
                out["family_hints"] = list(out.get("family_hints") or [])
                out["corpus_keys"] = []
                out["work_id"] = None
                out["ambient_ref"] = None

        goal = "structural_learning"
        if any(w in lowered for w in ("first time", "first hearing", "beginner")) or "入门" in text:
            goal = "first_hearing"
        elif any(w in lowered for w in ("perform", "practice", "rehearse")) or "练习" in text:
            goal = "performance_prep"

        # composer_only / multi_work: keep Catalog-shaped "Composer — Work" so
        # identity stays readable when no single work_id exists (SPEC-032).
        if (
            identity.status in {"composer_only", "multi_work", "ambiguous"}
            and composer
            and work_title
            and "—" not in work_title
            and composer.split()[-1].lower() not in work_title.lower()
        ):
            work_title = f"{composer} — {work_title}"

        out.update(
            {
                "work_title": work_title,
                "composer_guess": composer,
                "composer": composer,
                "listener_goal": goal,
                "experience_level": "curious_listener",
                "corpus_keys": list(out.get("corpus_keys") or identity.corpus_keys),
                "family_hints": list(
                    out.get("family_hints")
                    or ([] if not identity.family_id else [identity.family_id])
                ),
            }
        )
        # Class gate aliens even when Catalog work_id is missing (form policy + catalog nos.)
        from aulos_skills.identity_lock import build_identity_lock

        lock = build_identity_lock(
            work_title=work_title,
            work_hint=hint,
            raw_message=message,
        )
        if lock.alien_markers:
            merged_markers = list(out.get("conflict_markers") or [])
            for m in lock.alien_markers:
                if m not in merged_markers:
                    merged_markers.append(m)
            out["conflict_markers"] = merged_markers
        if lock.catalog_numbers:
            out["identity_lock_numbers"] = sorted(lock.catalog_numbers)
        if lock.form_families:
            out["identity_lock_forms"] = sorted(lock.form_families)

        # SPEC-034 / META-001 §4.1 — attach Discogs release structure at intake
        from aulos_skills.release_structure import (
            apply_structure_gate,
            enrich_lock_catalogs,
            structure_from_context,
        )

        gated = apply_structure_gate({**context, **out, "kb_dossier": kb})
        st = structure_from_context(gated)
        if st:
            out["release_structure"] = st
            if gated.get("structure_hard_fails"):
                out["structure_hard_fails"] = list(gated["structure_hard_fails"])
            if gated.get("refuse_families"):
                out["refuse_families"] = True
            if gated.get("program_expand_required"):
                out["program_expand_required"] = True
            if gated.get("critique_corrections"):
                out["critique_corrections"] = list(gated["critique_corrections"])
            nums = list(out.get("identity_lock_numbers") or [])
            enriched = enrich_lock_catalogs(
                {"catalog_numbers": nums, "work_title": work_title, "composer": composer},
                st,
            )
            if enriched.get("catalog_numbers"):
                out["identity_lock_numbers"] = list(enriched["catalog_numbers"])
        return out

    def _synthesize_assets_dir(self, skill: SkillManifest) -> Path:
        return skill.path / "assets"

    def _load_synthesize_index(self, skill: SkillManifest) -> dict[str, Any]:
        path = self._synthesize_assets_dir(skill) / "index.yaml"
        if not path.is_file():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _match_composer_card(self, skill: SkillManifest, text: str, composer_guess: str) -> dict[str, Any]:
        from aulos_skills.text_match import alias_in_text, composers_compatible

        index = self._load_synthesize_index(skill)
        blob = f"{composer_guess} {text}".lower()
        guess = (composer_guess or "").strip()
        for entry in index.get("composers") or []:
            aliases = [str(a).lower() for a in (entry.get("aliases") or []) if a]
            if not any(alias_in_text(a, blob) for a in aliases):
                continue
            path = self._synthesize_assets_dir(skill) / "composers" / str(entry.get("path") or "")
            if not path.is_file():
                continue
            card = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            card_name = str(card.get("composer") or entry.get("id") or "")
            # When intake already named a composer, refuse a mismatched card (SPEC-032).
            if guess and card_name and not composers_compatible(guess, card_name):
                continue
            return card
        return {}

    def _family_instrument_gate(self, family: dict[str, Any], blob: str) -> bool:
        """SPEC-033: soloist-scoped packs need soloist evidence; refuse conflicts."""
        from aulos_skills.instrument_evidence import (
            family_conflicts_blob_soloists,
            family_requires_soloist_evidence,
            family_soloist_misses_blob,
        )

        if family_requires_soloist_evidence(family) and family_soloist_misses_blob(
            family, blob
        ):
            return False
        if family_conflicts_blob_soloists(family, blob):
            return False
        return True

    def _match_family(
        self,
        skill: SkillManifest,
        text: str,
        family_hints: list[str],
        composer_guess: str = "",
    ) -> dict[str, Any]:
        index = self._load_synthesize_index(skill)
        blob = text.lower()
        composer_l = (composer_guess or "").lower()
        # Prefer explicit hints (catalog family_id) — still verify path + instrument gate.
        for hint in family_hints:
            for entry in index.get("families") or []:
                if str(entry.get("id") or "") == hint:
                    path = self._synthesize_assets_dir(skill) / "families" / str(entry.get("path") or "")
                    if path.is_file():
                        hinted = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                        if self._family_instrument_gate(hinted, blob):
                            return hinted
        best: dict[str, Any] = {}
        best_score = 0
        for entry in index.get("families") or []:
            path = self._synthesize_assets_dir(skill) / "families" / str(entry.get("path") or "")
            if not path.is_file():
                continue
            family = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if not self._family_instrument_gate(family, blob):
                continue
            match = dict(family.get("match") or {})
            score = 0
            evidence = 0
            for bucket in ("instruments", "forms"):
                for token in match.get(bucket) or []:
                    t = str(token).lower()
                    if t and t in blob:
                        score += 1
                        evidence += 1
            composer_tokens = [str(t).lower() for t in (match.get("composers") or []) if t]
            if composer_tokens:
                # Composer-scoped family packs must not unlock on bare form/instrument
                # overlap (e.g. Mozart piano sonata ≠ Beethoven cello-piano duo pack).
                # SPEC-009: composer alone is also insufficient — need instrument/form evidence
                # (Brahms violin concerto must not unlock duo-cello-piano).
                composer_hit = any(
                    t and (t in blob or t in composer_l) for t in composer_tokens
                )
                if not composer_hit:
                    continue
                if evidence < 1:
                    continue
                score += 2
            if score > best_score:
                best_score = score
                best = family
        return best if best_score >= 2 else {}

    def _run_synthesize(self, skill: SkillManifest, context: dict[str, Any]) -> dict[str, Any]:
        existing = dict(context.get("corpus_dossier") or {})
        richness = dossier_richness(existing)
        # Flagship corpus already complete — pass through
        if context.get("corpus_hit") and richness >= 7:
            return {
                "synthesize_hit": False,
                "synthesize_source": "corpus-passthrough",
                "corpus_dossier": existing,
            }

        # SPEC-034Δ — structure gate + iterative program deepen loop
        from aulos_skills.program_deepen import (
            finalize_program_dossier,
            fold_program_iterations,
        )
        from aulos_skills.release_structure import (
            apply_structure_gate,
            build_program_expand_dossier,
            is_multi_work_program,
            structure_from_context,
        )

        apply_structure_gate(context)
        release_structure = structure_from_context(context)
        kb_for_iter = dict(context.get("kb_dossier") or {})
        if kb_for_iter.get("program_iterations") and not context.get("program_iterations"):
            context["program_iterations"] = list(kb_for_iter.get("program_iterations") or [])
        program_expand: dict[str, Any] = {}
        if (
            is_multi_work_program(release_structure)
            and not context.get("structure_hard_fails")
            and (
                context.get("program_expand_required")
                or context.get("program_iterations")
                or release_structure.get("structure_ready")
            )
        ):
            iterations = list(context.get("program_iterations") or [])
            if iterations:
                program_expand = fold_program_iterations(
                    release_structure,
                    iterations,
                    composer=str(
                        context.get("composer")
                        or context.get("composer_guess")
                        or existing.get("composer")
                        or ""
                    ),
                    work_title=str(
                        context.get("work_title") or existing.get("work_title") or ""
                    ),
                    performers=list(
                        (context.get("discogs") or {}).get("performers")
                        or release_structure.get("performers")
                        or []
                    ),
                )
                context["program_loop_dossier"] = program_expand
                context["program_loop_applied"] = True
            else:
                # Scaffold only when gateway loop did not run (tests / offline)
                program_expand = build_program_expand_dossier(
                    release_structure,
                    composer=str(
                        context.get("composer")
                        or context.get("composer_guess")
                        or existing.get("composer")
                        or ""
                    ),
                    work_title=str(
                        context.get("work_title") or existing.get("work_title") or ""
                    ),
                    performers=list(
                        (context.get("discogs") or {}).get("performers")
                        or release_structure.get("performers")
                        or []
                    ),
                )

        text = f"{context.get('work_title', '')} {context.get('raw_message', '')}"
        composer_guess = str(context.get("composer_guess") or existing.get("composer") or "")
        family_hints = list(context.get("family_hints") or [])
        # SPEC-027: Catalog family_id wins as explicit hint before fuzzy match
        work_id_early = str(context.get("work_id") or "")
        if work_id_early:
            try:
                from aulos_skills.family_packs import catalog_family_id

                fid_cat = catalog_family_id(work_id_early)
                if fid_cat and fid_cat not in family_hints:
                    family_hints = [fid_cat, *family_hints]
                    context["family_hints"] = list(family_hints)
            except Exception:  # noqa: BLE001
                pass
        card = self._match_composer_card(skill, text, composer_guess)
        refuse_families = bool(context.get("refuse_families"))
        refuse_ids = {str(x) for x in (context.get("refuse_family_ids") or []) if x}
        family: dict[str, Any] = {}
        if not refuse_families:
            family = self._match_family(skill, text, family_hints, composer_guess=composer_guess)
            fid = str(family.get("family_id") or "")
            if fid and fid in refuse_ids:
                family = {}
        context["_last_matched_family"] = dict(family) if family else {}
        # SPEC-032: IntentLock composer is write-once truth over composer-card names.
        locked = dict(context.get("intent_lock") or {})
        locked_composer = str(locked.get("composer") or "").strip()
        card_composer = str(card.get("composer") or "").strip()
        if locked_composer:
            from aulos_skills.text_match import composers_compatible

            composer_name = locked_composer
            if card_composer and not composers_compatible(locked_composer, card_composer):
                card = {}
        else:
            composer_name = (
                card_composer
                or composer_guess
                or str(existing.get("composer") or "")
            )
        work_title = str(context.get("work_title") or existing.get("work_title") or "")

        layers: list[dict[str, Any]] = []
        sources: list[str] = []
        kb_dossier = dict(context.get("kb_dossier") or {})
        # Refuse KB dossiers that belong to a different work than intake identified.
        # Prefer catalog work_id / corpus_key; fall back to title sameness.
        if kb_dossier and (work_title or context.get("work_id")):
            kb_title = str(kb_dossier.get("work_title") or "")
            kb_work_id = str(kb_dossier.get("work_id") or "")
            resolved_id = str(context.get("work_id") or "")
            corpus_keys = {str(k) for k in (context.get("corpus_keys") or []) if k}
            kb_corpus = str(kb_dossier.get("dossier_id") or kb_dossier.get("corpus_key") or "")
            id_mismatch = bool(resolved_id and kb_work_id and resolved_id != kb_work_id)
            key_mismatch = bool(corpus_keys and kb_corpus and kb_corpus not in corpus_keys)
            title_mismatch = bool(
                work_title and kb_title and not self._titles_look_same(work_title, kb_title)
            )
            # Wrong-title / wrong-id KB must never thicken a resolved shelf.
            if id_mismatch or key_mismatch or title_mismatch:
                kb_dossier = {}
        # Guide #48: refuse KB layer whose dossier_id is a foreign family pack
        # (instruments miss locked title) even when titles were force-aligned.
        if kb_dossier:
            from aulos_skills.identity_hygiene import foreign_family_id

            title_blob = f"{work_title} {composer_name} {context.get('raw_message') or ''}"
            fid = foreign_family_id(kb_dossier, title_blob, composer=composer_name)
            if fid:
                kb_dossier = {}
            else:
                from aulos_skills.identity_hygiene import portrait_betrays_composer

                if portrait_betrays_composer(
                    kb_dossier.get("composer_portrait")
                    if isinstance(kb_dossier.get("composer_portrait"), dict)
                    else {},
                    composer_name,
                ):
                    kb_dossier = dict(kb_dossier)
                    kb_dossier["composer_portrait"] = {}
        if kb_dossier:
            layers.append(kb_dossier)
            sources.append("kb-rag")
        if family:
            layers.append(family_to_dossier(family, composer=composer_name, work_title=work_title))
            sources.append(f"family:{family.get('family_id')}")
        # SPEC-034Δ: program loop / expand wins over bare family map/deepdives
        if program_expand:
            layers.append(program_expand)
            src_tag = (
                "release-program-loop"
                if context.get("program_loop_applied")
                else "release-program-expand"
            )
            sources.append(src_tag)
            context["program_expand_applied"] = True
        elif context.get("structure_hard_fails"):
            sources.append("structure-blocked")
            context["program_expand_applied"] = False
        if card:
            layers.append(composer_to_dossier(card))
            sources.append("composer-card")
        # SPEC-026: Catalog-bound craft floor (any work_id; craft YAML still wins later)
        work_id = str(context.get("work_id") or "")
        if work_id:
            try:
                from aulos_skills.catalog_craft_floor import build_catalog_craft_floor

                floor = build_catalog_craft_floor(
                    work_id,
                    family=family if family else None,
                    composer_name=composer_name,
                    work_title=work_title,
                )
                if floor:
                    layers.append(floor)
                    sources.append(f"catalog-floor:{work_id}")
            except Exception:  # noqa: BLE001
                pass
        # SPEC-025: work craft pack after catalog floor (later layers win scalars)
        if work_id:
            try:
                from aulos_skills.craft_packs import craft_pack_to_dossier, load_craft_pack

                craft_pack = load_craft_pack(work_id)
                if craft_pack:
                    layers.append(
                        craft_pack_to_dossier(
                            craft_pack, composer=composer_name, work_title=work_title
                        )
                    )
                    sources.append(f"craft:{work_id}")
            except Exception:  # noqa: BLE001
                pass
        if existing:
            layers.append(existing)
            sources.append("corpus")
        llm_dossier = dict(context.get("llm_dossier") or {})
        if not llm_dossier and context.get("llm_enrichment"):
            llm_dossier = parse_llm_dossier_json(str(context.get("llm_enrichment")))
        if llm_dossier:
            # map stature reasons if model used flat keys
            if "historical_reasons" in llm_dossier and "historical_stature" not in llm_dossier:
                llm_dossier["historical_stature"] = {
                    "reasons": list(llm_dossier.get("historical_reasons") or []),
                    "reception_arc": str(llm_dossier.get("reception_arc") or ""),
                }
            # Don't let the model rename the work away from intake
            if work_title:
                llm_dossier = dict(llm_dossier)
                llm_dossier["work_title"] = work_title
                if composer_name:
                    llm_dossier["composer"] = composer_name
            from aulos_skills.identity_lock import dossier_betrays_identity_lock

            if dossier_betrays_identity_lock(
                llm_dossier,
                work_title=work_title,
                work_hint=str(context.get("work_hint") or ""),
                raw_message=str(context.get("raw_message") or ""),
            ):
                # Class gate: drop sibling-swap LLM layer (concerto→Requiem etc.)
                llm_dossier = {}
            if llm_dossier:
                layers.append(llm_dossier)
                sources.append("llm")
            # Re-assert craft scalars over LLM when craft pack exists (work shelf > model)
            if work_id:
                try:
                    from aulos_skills.craft_packs import craft_pack_to_dossier, load_craft_pack

                    craft_pack = load_craft_pack(work_id)
                    if craft_pack:
                        layers.append(
                            craft_pack_to_dossier(
                                craft_pack, composer=composer_name, work_title=work_title
                            )
                        )
                        if f"craft:{work_id}" not in sources:
                            sources.append(f"craft:{work_id}")
                except Exception:  # noqa: BLE001
                    pass

        corrections = [str(c) for c in (context.get("critique_corrections") or []) if c]
        refuse_topics = [str(t) for t in (context.get("refuse_topics") or []) if t]

        # SPEC-029: Unknown-Case Thicken — archetype floor when no family/catalog/craft
        used_family = bool(family)
        used_catalog_craft = any(
            s.startswith("catalog-floor:") or s.startswith("craft:") for s in sources
        )
        facet_clf: dict[str, Any] = {}
        archetype_used = False
        if not used_family and not used_catalog_craft:
            try:
                from aulos_skills.facet_classifier import classify_facets
                from aulos_skills.unknown_case_thicken import build_archetype_floor

                facet_clf = classify_facets(
                    work_title=work_title,
                    composer=composer_name,
                    raw_message=str(context.get("raw_message") or ""),
                    facets=dict(context.get("facets") or {}) or None,
                )
                if float(facet_clf.get("confidence") or 0.0) >= 0.4:
                    arch_floor = build_archetype_floor(
                        work_title,
                        composer_name,
                        classification=facet_clf,
                    )
                    if arch_floor:
                        layers.append(arch_floor)
                        arch_id = str(facet_clf.get("archetype_id") or "chamber-generic")
                        sources.append(f"archetype:{arch_id}")
                        prov = arch_floor.get("_provenance") or {}
                        if isinstance(prov, dict) and prov.get("dimension_template"):
                            dim = str(prov.get("dimension_id") or "")
                            if dim:
                                sources.append(f"dimension:{dim}")
                        archetype_used = True
                        context["facet_classification"] = facet_clf
            except Exception:  # noqa: BLE001
                facet_clf = {}
                archetype_used = False

        if not layers:
            # last-resort thin scaffold still better than raw sentence title
            thin = empty_dossier()
            thin["work_title"] = work_title or "Classical work"
            thin["composer"] = composer_name
            thesis = (
                f"Listen for recurring motives and form landmarks in {thin['work_title']}."
            )
            from aulos_skills.prose_hygiene import infer_form_label

            thin["form"] = infer_form_label(
                work_title=str(thin.get("work_title") or ""),
                form=str(thin.get("form") or ""),
                facets=dict(context.get("facets") or {}),
            )
            if "miniature" in thin["form"].lower() or "songs without words" in thin["form"].lower():
                thesis = (
                    f"Hear {thin['work_title']} as a lyric piano room — "
                    "lock the singing line and left-hand gait before chasing drama."
                )
            # Keep critique as caveats — never inject process locks into product thesis.
            if corrections:
                thin["myths_and_caveats"] = list(corrections[:4])
            thin["listening_thesis"] = thesis
            thin["width_points"] = [
                f"Frame {thin['work_title']} in biography, publication, and reception.",
                "Separate legends from documented fact.",
            ]
            thin["depth_points"] = [
                "Identify the unit the ear should lock onto first.",
                "Map landmarks with ear cues.",
                "Notice how the close remembers the opening.",
            ]
            thin["listening_map"] = [
                {"label": "Opening", "cue": "Establish tonic mood and primary motive."},
                {"label": "Middle", "cue": "Contrast, intensification, turning point."},
                {"label": "Close", "cue": "Return altered — memory as form."},
            ]
            thin["practice_notes"] = [
                "One focused hearing with a single question.",
                "Second hearing with a landmark list.",
            ]
            thin["myths_and_caveats"] = [
                "Cold path without family pack — verify anecdotes before stating as fact."
            ]
            if refuse_topics:
                thin["myths_and_caveats"].append(
                    "Do not treat as work body: " + ", ".join(refuse_topics[:6])
                )
            layers.append(thin)
            sources.append("generic-scaffold")

        merged = merge_dossiers(*layers)
        # Identity hygiene before lock overwrite — clear betraying portrait / foreign family id
        from aulos_skills.identity_hygiene import apply_identity_hygiene

        merged, hygiene = apply_identity_hygiene(
            merged,
            composer=composer_name,
            work_title=work_title,
            raw_message=str(context.get("raw_message") or ""),
        )
        if hygiene.markers:
            markers = list(context.get("conflict_markers") or [])
            for m in hygiene.markers:
                if m and m not in markers:
                    markers.append(m)
            context["conflict_markers"] = markers
            if any(f.code == "foreign_family_dossier" for f in hygiene.findings):
                context["refuse_families"] = True
                refused = list(context.get("refuse_family_ids") or [])
                for f in hygiene.findings:
                    if f.code != "foreign_family_dossier":
                        continue
                    for m in f.markers:
                        if str(m).startswith("family:"):
                            fid = str(m).split(":", 1)[1]
                            if fid and fid not in refused:
                                refused.append(fid)
                context["refuse_family_ids"] = refused
            # Drop polluted list chambers immediately (don't wait for review rework)
            merged = self._scrub_foreign_chambers(
                merged,
                work_title=work_title,
                conflict_markers=list(context.get("conflict_markers") or []),
                force_ambient_scrub=True,
            )
        # Rework path: park Intent Critic corrections in caveats — never product thesis.
        if corrections:
            caveats = list(merged.get("myths_and_caveats") or [])
            for c in corrections[:4]:
                if c not in caveats:
                    caveats.insert(0, c)
            merged["myths_and_caveats"] = caveats
        # Intake identity wins unless curated corpus already locked the work.
        if work_title and not context.get("corpus_hit"):
            merged["work_title"] = work_title
        elif not merged.get("work_title"):
            merged["work_title"] = work_title
        if composer_name and not context.get("corpus_hit"):
            merged["composer"] = composer_name
        elif not merged.get("composer"):
            merged["composer"] = composer_name
        if not merged.get("listening_thesis") and merged.get("work_introduction"):
            merged["listening_thesis"] = str(merged["work_introduction"]).split(".")[0][:240]
        from aulos_skills.prose_hygiene import (
            clean_packaging_work_title,
            looks_like_packaging_dump,
            partition_dossier_languages,
        )

        merged["work_title"] = clean_packaging_work_title(
            str(merged.get("work_title") or work_title or ""),
            composer=str(merged.get("composer") or composer_name or ""),
        )
        merged = partition_dossier_languages(merged)
        rag_hits = [
            point_text(h)
            for h in list(context.get("rag_hits") or [])
            if point_text(h) and not looks_like_packaging_dump(point_text(h))
        ]
        if rag_hits and len(merged.get("width_points") or []) < 4:
            extra = [f"From prior research cache: {h[:220]}" for h in rag_hits[:2]]
            extra = [e for e in extra if not looks_like_packaging_dump(e)]
            merged["width_points"] = list(merged.get("width_points") or []) + extra
            if extra and "kb-rag" not in sources:
                sources.append("kb-rag-hits")

        # Family is a FORM scaffold floor only — never a composer branch and never
        # allowed to overwrite richer KB/LLM chambers (copilot+KB owns thickening).
        if family and not context.get("corpus_hit"):
            from aulos_skills.salon_codex import SALON_LIST_KEYS, _coerce_list, _merge_list

            for key in SALON_LIST_KEYS:
                fam_list = _coerce_list(family.get(key))
                cur = _coerce_list(merged.get(key))
                if not fam_list:
                    continue
                if not cur:
                    merged[key] = fam_list
                elif len(cur) < 2:
                    # Thin LLM/KB — lift to family floor, keep any extras
                    merged[key] = _merge_list(fam_list, cur)
                else:
                    # Richer enrich wins; family only fills novel items
                    merged[key] = _merge_list(cur, fam_list)
            for key in ("genesis", "historical_stature", "sound_world", "ambient_audio"):
                fam_val = family.get(key)
                cur_val = merged.get(key)
                empty = cur_val in (None, "", {}, [])
                if fam_val and empty:
                    merged[key] = dict(fam_val) if isinstance(fam_val, dict) else fam_val
            for key in ("era", "form", "catalog", "listening_thesis", "work_introduction"):
                if family.get(key) and not str(merged.get(key) or "").strip():
                    merged[key] = family[key]
            if family.get("zh"):
                zh_fam = coerce_dict(family.get("zh") or family.get("zh_hans"))
                zh_merged = merge_dossiers(coerce_dict(merged.get("zh") or merged.get("zh_hans")), zh_fam)
                # Gap-fill zh lists the same way
                for key in SALON_LIST_KEYS:
                    fam_list = _coerce_list(zh_fam.get(key))
                    cur = _coerce_list(zh_merged.get(key))
                    if not fam_list:
                        continue
                    if not cur:
                        zh_merged[key] = fam_list
                    elif len(cur) < 2:
                        zh_merged[key] = _merge_list(fam_list, cur)
                    else:
                        zh_merged[key] = _merge_list(cur, fam_list)
                for key in ("genesis", "historical_stature", "sound_world"):
                    if zh_fam.get(key) and not zh_merged.get(key):
                        zh_merged[key] = zh_fam[key]
                for key in ("era", "form", "catalog", "listening_thesis", "work_introduction"):
                    if zh_fam.get(key) and not str(zh_merged.get(key) or "").strip():
                        zh_merged[key] = zh_fam[key]
                merged["zh"] = zh_merged

        from aulos_skills.chamber_contracts import ensure_chamber_floor
        from aulos_skills.knowledge_thicken import (
            knowledge_dossier_to_chambers,
            merge_knowledge_thicken,
        )

        # SPEC-025 knowledge-plane composer thicken (portrait / profile / genesis)
        kn_raw = (
            context.get("_knowledge_composer")
            or (context.get("kb_dossier") or {}).get("_knowledge_composer")
        )
        if isinstance(kn_raw, dict) and kn_raw:
            kn_patch = knowledge_dossier_to_chambers(kn_raw)
            merged = merge_knowledge_thicken(merged, kn_patch)
            if kn_patch and "knowledge-plane" not in sources:
                sources.append("knowledge-plane")
        elif isinstance((context.get("kb_dossier") or {}).get("_knowledge_thicken"), dict):
            merged = merge_knowledge_thicken(
                merged, dict((context.get("kb_dossier") or {}).get("_knowledge_thicken") or {})
            )
            if "knowledge-plane" not in sources:
                sources.append("knowledge-plane")

        merged = ensure_chamber_floor(merged, family if family else None)
        merged = finalize_program_dossier(merged, context)

        merged = self._scrub_foreign_chambers(
            merged,
            work_title=str(merged.get("work_title") or work_title),
            conflict_markers=resolve_scrub_markers(
                {
                    **context,
                    "work_title": merged.get("work_title") or work_title,
                    "composer": merged.get("composer") or composer_name,
                }
            ),
            force_ambient_scrub=bool(context.get("decontam_rework") or context.get("refuse_families")),
        )

        out: dict[str, Any] = {
            "synthesize_hit": True,
            "synthesize_source": "+".join(sources),
            "corpus_dossier": merged,
            "work_title": merged.get("work_title") or work_title,
            "composer_guess": merged.get("composer") or composer_name,
            "composer": merged.get("composer") or composer_name,
            "work_id": context.get("work_id"),
            "conflict_markers": list(context.get("conflict_markers") or []),
        }
        if release_structure:
            out["release_structure"] = release_structure
        if merged.get("guide_sheets"):
            out["guide_sheets"] = list(merged.get("guide_sheets") or [])
        if merged.get("program_parallel_plan"):
            out["program_parallel_plan"] = dict(merged.get("program_parallel_plan") or {})
        if context.get("structure_hard_fails"):
            out["structure_hard_fails"] = list(context["structure_hard_fails"])
        if context.get("program_expand_applied"):
            out["program_expand_applied"] = True
        if context.get("refuse_families"):
            out["refuse_families"] = True
        # SPEC-029/032: promote dry-run when unknown archetype path meets chamber floors
        if archetype_used:
            try:
                from aulos_skills.promote_candidate import build_promote_candidate

                lock_now = dict(context.get("intent_lock") or {})
                allow_promote = not (
                    context.get("review_failed") or context.get("decontam_failed")
                )
                cand = build_promote_candidate(
                    work_title=str(merged.get("work_title") or work_title),
                    composer=str(merged.get("composer") or composer_name),
                    classification=facet_clf,
                    dossier=merged,
                    locked_composer=str(lock_now.get("composer") or "") or None,
                    allow=allow_promote,
                )
                if cand:
                    out["promote_candidate"] = cand
            except Exception:  # noqa: BLE001
                pass
        return out

    @staticmethod
    def _scrub_foreign_chambers(
        dossier: dict[str, Any],
        *,
        work_title: str,
        conflict_markers: list[str] | None = None,
        force_ambient_scrub: bool = False,
    ) -> dict[str, Any]:
        """Drop list items AND scalars that belong to conflict works (catalog-derived)."""
        active = [m.lower() for m in (conflict_markers or []) if m and len(str(m)) >= 3]
        title_l = (work_title or "").lower()
        # Never scrub markers that are part of the confirmed title itself
        active = [m for m in active if m not in title_l]
        if not active:
            return dossier

        def polluted(blob: str) -> bool:
            return any(m in blob for m in active)

        def cleanse(items: list[Any]) -> list[Any]:
            out = []
            for item in items:
                blob = json.dumps(item, ensure_ascii=False).lower() if not isinstance(item, str) else item.lower()
                if polluted(blob):
                    continue
                out.append(item)
            return out

        out = dict(dossier)
        for key in (
            "depth_points",
            "width_points",
            "listening_map",
            "variation_deepdives",
            "interpretations",
            "appreciation_videos",
            "vinyl_and_discography",
            "related_works",
            "practice_notes",
            "myths_and_caveats",
        ):
            if out.get(key):
                out[key] = cleanse(list(out.get(key) or []))

        # historical_stature.reasons is a prime pollution sink (Goldberg + cello + target)
        stature = dict(out.get("historical_stature") or {}) if isinstance(out.get("historical_stature"), dict) else {}
        if stature.get("reasons"):
            stature["reasons"] = cleanse(list(stature.get("reasons") or []))
            if isinstance(stature.get("reception_arc"), str) and polluted(
                str(stature.get("reception_arc") or "").lower()
            ):
                stature["reception_arc"] = ""
            out["historical_stature"] = stature

        # Portrait betrayal / wrong-composer URL
        portrait = dict(out.get("composer_portrait") or {}) if isinstance(out.get("composer_portrait"), dict) else {}
        if portrait:
            from aulos_skills.identity_hygiene import portrait_betrays_composer

            composer_guess = str(out.get("composer") or "")
            if portrait_betrays_composer(portrait, composer_guess) or polluted(
                json.dumps(portrait, ensure_ascii=False).lower()
            ):
                out["composer_portrait"] = {}

        for key in ("listening_thesis", "work_introduction", "form", "catalog", "era"):
            val = out.get(key)
            if isinstance(val, str) and polluted(val.lower()):
                # SPEC-028: craft / catalog-floor prose may name conflict works to refuse them
                dossier_id = str(out.get("dossier_id") or "")
                prov = out.get("_provenance") if isinstance(out.get("_provenance"), dict) else {}
                protected = dossier_id.startswith(("craft:", "catalog-floor:")) or bool(
                    prov.get("craft_pack") or prov.get("catalog_craft_floor")
                )
                if not protected:
                    out[key] = ""

        amb = dict(out.get("ambient_audio") or {})
        peerish = False
        if amb:
            amb_blob = json.dumps(amb, ensure_ascii=False).lower()
            why_blob = f"{amb.get('why') or ''} {amb.get('why_zh') or ''}".lower()
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
            # Polluted ambient: drop unless honest peer/catalog-ref and not force-scrubbing.
            # Wrong-family peerish text must not shield pollution (SPEC-009 / guide #44).
            if polluted(amb_blob):
                if force_ambient_scrub:
                    out["ambient_audio"] = {}
                elif amb.get("selection_source") == "catalog-ref" or peerish:
                    pass
                else:
                    out["ambient_audio"] = {}

        zh_keys = ("zh", "zh_hans", "zh_hant")
        for zkey in zh_keys:
            zh = coerce_dict(out.get(zkey))
            if not zh:
                continue
            for key in (
                "depth_points",
                "width_points",
                "listening_map",
                "variation_deepdives",
                "interpretations",
                "appreciation_videos",
                "vinyl_and_discography",
                "related_works",
                "practice_notes",
                "myths_and_caveats",
            ):
                if zh.get(key):
                    zh[key] = cleanse(list(zh.get(key) or []))
            for key in (
                "listening_thesis",
                "work_introduction",
                "form",
                "catalog",
                "era",
                "work_title",
                "composer",
            ):
                val = zh.get(key)
                if isinstance(val, str) and polluted(val.lower()):
                    zh[key] = ""
            zh_amb = dict(zh.get("ambient_audio") or {})
            if zh_amb and polluted(json.dumps(zh_amb, ensure_ascii=False).lower()):
                if force_ambient_scrub or not peerish:
                    zh["ambient_audio"] = {}
            out[zkey] = zh
        return out

    @staticmethod
    def _titles_look_same(a: str, b: str) -> bool:
        """Same-work check — catalog weak tokens alone never prove identity."""
        ta = {t.lower() for t in re.findall(r"[a-z0-9\u4e00-\u9fff]{3,}", a or "", flags=re.I)}
        tb = {t.lower() for t in re.findall(r"[a-z0-9\u4e00-\u9fff]{3,}", b or "", flags=re.I)}
        if not ta or not tb:
            return False
        try:
            from aulos_skills.identity import load_catalog

            weak = set(load_catalog().weak_tokens)
        except Exception:  # noqa: BLE001
            weak = {
                "bach",
                "beethoven",
                "mozart",
                "bwv",
                "opus",
                "suite",
                "sonata",
                "variation",
                "symphony",
                "nocturne",
            }
        strong = (ta & tb) - weak
        if strong:
            return True
        return ta == tb

    def _run_corpus(self, skill: SkillManifest, context: dict[str, Any]) -> dict[str, Any]:
        corpus_dir = skill.path / "assets" / "corpus"
        index_path = corpus_dir / "index.yaml"
        keys = list(context.get("corpus_keys") or [])
        work_title = str(context.get("work_title") or "")
        if not index_path.is_file():
            return {"corpus_hit": False, "corpus_dossier": {}}
        index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
        entries = index.get("entries") or []
        match = None
        message_l = str(context.get("raw_message") or "").lower()
        title_l = work_title.lower()
        for entry in entries:
            key = str(entry.get("key") or "")
            aliases = [str(a).lower() for a in (entry.get("aliases") or []) if str(a).strip()]
            if key in keys:
                match = entry
                break
            # Prefer specific aliases (≥5 chars) as whole-phrase containment
            if title_l and any(len(a) >= 5 and a in title_l for a in aliases):
                match = entry
                break
            if any(len(a) >= 5 and a in message_l for a in aliases):
                match = entry
                break
        if match is None:
            return {"corpus_hit": False, "corpus_dossier": {}}
        rel = str(match.get("path") or "")
        body_path = corpus_dir / rel
        dossier: dict[str, Any]
        if body_path.is_file() and body_path.suffix.lower() in {".yaml", ".yml"}:
            dossier = self._parse_corpus_yaml(
                yaml.safe_load(body_path.read_text(encoding="utf-8")) or {},
                work_title=str(match.get("work_title") or work_title),
                composer=str(match.get("composer") or ""),
                key=str(match.get("key") or ""),
            )
        else:
            body = body_path.read_text(encoding="utf-8") if body_path.is_file() else ""
            dossier = self._parse_corpus_markdown(
                body,
                work_title=str(match.get("work_title") or work_title),
                composer=str(match.get("composer") or ""),
                key=str(match.get("key") or ""),
            )
        return {
            "corpus_hit": True,
            "corpus_dossier": dossier,
            "work_title": dossier.get("work_title") or work_title,
            "composer_guess": dossier.get("composer") or context.get("composer_guess") or "",
        }

    def _normalize_related(self, related: Any) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for item in related or []:
            if isinstance(item, dict):
                out.append(
                    {
                        "title": str(item.get("title") or item.get("name") or ""),
                        "why": str(item.get("why") or item.get("note") or ""),
                    }
                )
            else:
                out.append({"title": str(item), "why": ""})
        return [r for r in out if r["title"]]

    def _parse_corpus_yaml(
        self,
        data: dict[str, Any],
        *,
        work_title: str,
        composer: str,
        key: str,
    ) -> dict[str, Any]:
        stature = dict(data.get("historical_stature") or {})
        ambient = resolve_ambient_audio(
            dict(data.get("ambient_audio") or {}),
            corpus_dir=self._corpus_assets_dir_for_key(key),
        )
        return {
            "dossier_id": str(data.get("dossier_id") or key),
            "work_title": str(data.get("work_title") or work_title),
            "composer": str(data.get("composer") or composer),
            "catalog": str(data.get("catalog") or ""),
            "era": str(data.get("era") or ""),
            "form": str(data.get("form") or ""),
            "listening_thesis": str(data.get("listening_thesis") or "").strip(),
            "composer_portrait": dict(data.get("composer_portrait") or {}),
            "composer_profile": dict(data.get("composer_profile") or {}),
            "genesis": dict(data.get("genesis") or {}),
            "historical_stature": {
                "reasons": list(stature.get("reasons") or []),
                "reception_arc": str(stature.get("reception_arc") or ""),
            },
            "work_introduction": str(data.get("work_introduction") or "").strip(),
            "width_points": list(data.get("width_points") or []),
            "depth_points": list(data.get("depth_points") or []),
            "myths_and_caveats": list(data.get("myths_and_caveats") or []),
            "listening_map": list(data.get("listening_map") or []),
            "variation_deepdives": list(
                data.get("variation_deepdives") or data.get("section_deepdives") or []
            ),
            "sound_world": dict(data.get("sound_world") or {}),
            "ambient_audio": ambient,
            "related_works": self._normalize_related(data.get("related_works")),
            "interpretations": list(data.get("interpretations") or []),
            "appreciation_videos": list(data.get("appreciation_videos") or []),
            "vinyl_and_discography": list(data.get("vinyl_and_discography") or []),
            "practice_notes": list(data.get("practice_notes") or []),
            "zh": coerce_dict(data.get("zh") or data.get("zh_hans")),
            "raw_format": "yaml",
        }

    def _corpus_assets_dir_for_key(self, key: str) -> Path | None:
        skill = self.get_by_trigger("listening.corpus")
        if skill is None:
            return None
        return skill.path / "assets" / "corpus"

    def _parse_corpus_markdown(self, body: str, *, work_title: str, composer: str, key: str) -> dict[str, Any]:
        def section(name: str) -> str:
            pat = rf"##\s+{re.escape(name)}\s*\n(.*?)(?=\n##\s+|\Z)"
            m = re.search(pat, body, flags=re.S | re.I)
            return (m.group(1).strip() if m else "")

        def bullets(text: str) -> list[str]:
            out = []
            for ln in text.splitlines():
                ln = ln.strip()
                if ln.startswith("- "):
                    out.append(ln[2:].strip())
            return out

        width = bullets(section("Width seeds"))
        depth = bullets(section("Depth seeds"))
        myths = bullets(section("Myths and caveats"))
        practice = bullets(section("Practice listening"))
        map_rows: list[dict[str, str]] = []
        for ln in section("Listening map").splitlines():
            if "|" not in ln or ln.strip().startswith("| ---") or "Landmark" in ln:
                continue
            parts = [p.strip() for p in ln.strip().strip("|").split("|")]
            if len(parts) >= 2:
                map_rows.append({"label": parts[0], "cue": parts[1]})

        era_m = re.search(r"^era:\s*(.+)$", body, flags=re.M | re.I)
        form_m = re.search(r"^form:\s*(.+)$", body, flags=re.M | re.I)
        return {
            "dossier_id": key,
            "work_title": work_title,
            "composer": composer,
            "catalog": "",
            "era": era_m.group(1).strip() if era_m else "",
            "form": form_m.group(1).strip() if form_m else "",
            "listening_thesis": "",
            "composer_portrait": {},
            "composer_profile": {},
            "genesis": {},
            "historical_stature": {"reasons": [], "reception_arc": ""},
            "work_introduction": "",
            "width_points": width,
            "depth_points": depth,
            "myths_and_caveats": myths,
            "listening_map": map_rows,
            "variation_deepdives": [],
            "sound_world": {},
            "related_works": self._normalize_related(
                [
                    "Bach — Partitas & English Suites",
                    "Bach — Musical Offering / Art of Fugue",
                    "Beethoven — Diabelli Variations",
                ]
            ),
            "interpretations": [],
            "appreciation_videos": [],
            "vinyl_and_discography": [],
            "practice_notes": practice,
            "raw_markdown": body,
            "raw_format": "markdown",
        }

    def _run_width(self, context: dict[str, Any]) -> dict[str, Any]:
        corpus = dict(context.get("corpus_dossier") or {})
        if corpus.get("width_points") or corpus.get("composer_profile") or corpus.get("genesis"):
            points = list(corpus.get("width_points") or [])
            myths = list(corpus.get("myths_and_caveats") or [])
            related = self._normalize_related(corpus.get("related_works"))
            era = str(corpus.get("era") or "")
            stature = dict(corpus.get("historical_stature") or {})
            reception = str(stature.get("reception_arc") or "") or (
                "Reception framed from curated dossier with myth/evidence separation."
            )
            profile = dict(corpus.get("composer_profile") or {})
            genesis = dict(corpus.get("genesis") or {})
            portrait = dict(corpus.get("composer_portrait") or {})
            reasons = list(stature.get("reasons") or [])
        else:
            title = context.get("work_title") or "the work"
            points = [
                f"Frame “{title}” in composer biography, premiere/publication, and patronage setting.",
                "Map stylistic period and contemporary peers.",
                "Collect reception history: early reviews, revival moments, landmark recordings.",
                "Separate cultural myths from documented fact.",
            ]
            myths = ["Cold-research path: verify legendary anecdotes before stating as fact."]
            related = self._normalize_related(
                [
                    {"title": "Sibling works by the same composer", "why": "Oeuvre context"},
                    {"title": "Period companions", "why": "Stylistic neighborhood"},
                ]
            )
            era = "Classical repertoire (context pending enrichment)"
            reception = f"Wide frame for {title} assembled without curated dossier."
            profile = {}
            genesis = {}
            portrait = {}
            reasons = []
        enrichment = str(context.get("llm_enrichment") or "").strip()
        if enrichment:
            # Prefer structured JSON into chambers; never paste raw JSON into width bullets.
            parsed: dict[str, Any] | None = None
            try:
                raw_e = enrichment
                if raw_e.startswith("```"):
                    raw_e = re.sub(r"^```(?:json)?\s*", "", raw_e)
                    raw_e = re.sub(r"\s*```$", "", raw_e)
                blob = json.loads(raw_e)
                if isinstance(blob, dict):
                    parsed = blob
            except Exception:  # noqa: BLE001
                parsed = None
            if parsed:
                for key in ("listening_thesis", "work_introduction", "era", "form", "catalog"):
                    if parsed.get(key) and not corpus.get(key):
                        corpus[key] = parsed[key]
                if isinstance(parsed.get("width_points"), list) and parsed["width_points"]:
                    points = list(points) + [str(x) for x in parsed["width_points"][:4] if x]
                if isinstance(parsed.get("myths_and_caveats"), list) and parsed["myths_and_caveats"]:
                    myths = list(myths) + [str(x) for x in parsed["myths_and_caveats"][:3] if x]
                if isinstance(parsed.get("related_works"), list) and parsed["related_works"]:
                    related = self._normalize_related(list(related) + list(parsed["related_works"][:3]))
                if isinstance(parsed.get("composer_portrait"), dict) and parsed["composer_portrait"]:
                    portrait = parsed["composer_portrait"]
                if isinstance(parsed.get("genesis"), dict) and parsed["genesis"]:
                    genesis = parsed["genesis"]
            elif not enrichment.lstrip().startswith("{"):
                from aulos_skills.prose_hygiene import looks_like_packaging_dump

                note = enrichment[:220].strip()
                if note and not looks_like_packaging_dump(note):
                    points = [*points, note]
        width_dossier = {
            "era": era,
            "width_points": points,
            "myths_and_caveats": myths,
            "related_works": related,
            "reception_arc": reception,
            "composer_profile": profile,
            "composer_portrait": portrait,
            "genesis": genesis,
            "historical_reasons": reasons,
            "catalog": str(corpus.get("catalog") or ""),
            "work_introduction": str(corpus.get("work_introduction") or ""),
            "listening_thesis": str(corpus.get("listening_thesis") or ""),
            "interpretations": list(corpus.get("interpretations") or []),
            "appreciation_videos": list(corpus.get("appreciation_videos") or []),
            "vinyl_and_discography": list(corpus.get("vinyl_and_discography") or []),
            "zh": coerce_dict(corpus.get("zh") or corpus.get("zh_hans")),
            "salon_dossier": corpus,
        }
        return {
            "width_dossier": width_dossier,
            "width_points": points,
            "era": era,
            "related_works": related,
        }

    def _run_depth(self, context: dict[str, Any]) -> dict[str, Any]:
        corpus = dict(context.get("corpus_dossier") or {})
        if corpus.get("depth_points") or corpus.get("listening_map"):
            points = list(corpus.get("depth_points") or [])
            listening_map = list(corpus.get("listening_map") or [])
            practice = list(corpus.get("practice_notes") or [])
            form = str(corpus.get("form") or "")
            deepdives = list(corpus.get("variation_deepdives") or [])
            sound_world = dict(corpus.get("sound_world") or {})
        else:
            title = context.get("work_title") or "the work"
            points = [
                f"Identify the form unit of “{title}” and what the ear should lock onto first.",
                "List section landmarks with tempo and character words.",
                "Track motives, keys, and dramatic turning points with ear cues.",
            ]
            listening_map = [
                {"label": "Opening", "cue": "Establish tonic mood, tempo gait, and primary motive."},
                {"label": "Middle", "cue": "Listen for contrast, modulation, and intensification."},
                {"label": "Close", "cue": "Notice how themes return altered — memory as form."},
            ]
            practice = [
                "One focused hearing with a single question (form / color / rhetoric).",
                "Second hearing with movement list if available.",
                "Journal three timestamps where attention shifted.",
            ]
            form = "Large-scale work — form clarified in deep research"
            deepdives = []
            sound_world = {}
        from aulos_skills.prose_hygiene import infer_form_label

        form = infer_form_label(
            work_title=str(context.get("work_title") or corpus.get("work_title") or ""),
            form=form,
            facets=dict(context.get("facets") or {}),
        )
        # Miniature / cycle shelves: swap symphony-scale depth rhetoric
        if "miniature" in form.lower() or "songs without words" in form.lower():
            title = context.get("work_title") or corpus.get("work_title") or "the piece"
            points = [
                f"Treat “{title}” as a lyric room — lock the opening gait and singing line first.",
                "Map ternary or episodic rooms: opening character → contrast → return.",
                "Compare two pieces from the same set for shared lyric speech under different temperaments.",
            ]
            listening_map = [
                {"label": "Opening song", "cue": "Memorize the singing line and left-hand gait before ornament."},
                {"label": "Middle tint", "cue": "Mode shift, register lift, or episodic turn — still one lyric room."},
                {"label": "Return / close", "cue": "Does the opening song return intact, deepened, or ironized?"},
            ]
        return {
            "depth_dossier": {
                "form": form,
                "depth_points": points,
                "listening_map": listening_map,
                "practice_notes": practice,
                "variation_deepdives": deepdives,
                "sound_world": sound_world,
            },
            "depth_points": points,
            "listening_map": listening_map,
            "practice_notes": practice,
            "form": form,
        }

    def _run_compose(self, context: dict[str, Any]) -> dict[str, Any]:
        from aulos_skills.guide_render import render_bilingual_guide_html
        from aulos_skills.i18n import dossier_has_zh, ensure_chinese_variants, prefer_chinese_variant, re_has_cjk

        work_title = str(context.get("work_title") or "Classical work")
        composer = str(
            context.get("composer")
            or context.get("composer_guess")
            or (context.get("corpus_dossier") or {}).get("composer")
            or ""
        )
        if not composer or composer.lower() in {"unknown", "unknown composer", "composer"}:
            from aulos_skills.intake_parse import guess_composer_and_title
            from aulos_skills.identity import load_catalog

            recovered = guess_composer_and_title(
                f"{work_title} {context.get('raw_message') or ''}",
                catalog_composers=load_catalog().composers,
            )
            composer = recovered.get("composer") or composer
            if recovered.get("work_title") and (
                "一份" in work_title or "导赏" in work_title or work_title.startswith("Unspecified")
            ):
                work_title = recovered["work_title"]
        if not composer:
            composer = "Unknown composer"
        width = dict(context.get("width_dossier") or {})
        depth = dict(context.get("depth_dossier") or {})
        dossier = dict(width.get("salon_dossier") or context.get("corpus_dossier") or {})
        # Park critique corrections in caveats only — never product thesis / H1 lede.
        corrections = [str(c) for c in (context.get("critique_corrections") or []) if c]
        if corrections:
            caveats = list(dossier.get("myths_and_caveats") or [])
            for c in corrections[:4]:
                if c not in caveats:
                    caveats.insert(0, c)
            dossier["myths_and_caveats"] = caveats
        if width.get("listening_thesis"):
            dossier["listening_thesis"] = width["listening_thesis"]
        if width.get("work_introduction"):
            dossier["work_introduction"] = width["work_introduction"]
        if width.get("era"):
            dossier["era"] = width["era"]
        if depth.get("form"):
            dossier["form"] = depth["form"]
        if width.get("catalog"):
            dossier["catalog"] = width["catalog"]
        for key in (
            "width_points",
            "myths_and_caveats",
            "related_works",
            "composer_portrait",
            "composer_profile",
            "genesis",
            "interpretations",
            "appreciation_videos",
            "vinyl_and_discography",
        ):
            if width.get(key):
                dossier[key] = width[key]
        if corrections:
            caveats = list(dossier.get("myths_and_caveats") or [])
            for c in corrections[:4]:
                if c not in caveats:
                    caveats.insert(0, c)
            dossier["myths_and_caveats"] = caveats
        if width.get("historical_reasons") or width.get("reception_arc"):
            stature = dict(dossier.get("historical_stature") or {})
            if width.get("historical_reasons"):
                stature["reasons"] = list(width["historical_reasons"])
            if width.get("reception_arc"):
                stature["reception_arc"] = width["reception_arc"]
            dossier["historical_stature"] = stature
        for key in ("depth_points", "listening_map", "practice_notes", "variation_deepdives", "sound_world"):
            if depth.get(key):
                dossier[key] = depth[key]
        if width.get("zh"):
            dossier["zh"] = width["zh"]

        from aulos_skills.prose_hygiene import (
            clean_packaging_work_title,
            infer_form_label,
            partition_dossier_languages,
        )

        work_title = clean_packaging_work_title(work_title, composer=composer)
        context["work_title"] = work_title
        dossier["work_title"] = work_title
        dossier["composer"] = composer
        dossier["form"] = infer_form_label(
            work_title=work_title,
            form=str(dossier.get("form") or depth.get("form") or ""),
            facets=dict(context.get("facets") or {}),
        )
        dossier = partition_dossier_languages(dossier)
        # SPEC-025: craft-pack theses win over LLM poetic ZH/EN drift
        from aulos_skills.craft_packs import reassert_craft_leads

        dossier = reassert_craft_leads(dossier, str(context.get("work_id") or "") or None)
        context["corpus_dossier"] = dossier
        # If EN thesis emptied after CJK move, seed a short English lede from title
        if not str(dossier.get("listening_thesis") or "").strip():
            dossier["listening_thesis"] = (
                f"A listening path into {work_title}"
                + (f" by {composer}." if composer else ".")
            )

        dossier.setdefault("work_title", work_title)
        dossier.setdefault("composer", composer)

        corpus_dir = self._corpus_assets_dir_for_key("")
        prefer_zh_early = re_has_cjk(str(context.get("raw_message") or ""))
        ambient = select_ambient(
            work_title=work_title,
            composer=composer,
            era=str(dossier.get("era") or context.get("era") or ""),
            form=str(dossier.get("form") or context.get("form") or ""),
            family_hints=list(context.get("family_hints") or []),
            facets=dict(context.get("facets") or {}),
            ambient_ref=str(context.get("ambient_ref") or "") or None,
            conflict_markers=list(context.get("conflict_markers") or []),
            existing=dict(dossier.get("ambient_audio") or {}),
            corpus_dir=corpus_dir,
            fallback_mode=str(context.get("ambient_fallback_mode") or "embed"),
            appreciation_videos=list(dossier.get("appreciation_videos") or []),
            interpretations=list(dossier.get("interpretations") or []),
            prefer_zh=prefer_zh_early,
            allow_video_search=bool(context.get("ambient_allow_video_search", True)),
        )
        if ambient:
            dossier["ambient_audio"] = ambient
            # Keep zh layer from inheriting a conflicting empty ambient
            zh = coerce_dict(dossier.get("zh") or dossier.get("zh_hans"))
            if zh and not (zh.get("ambient_audio") or {}).get("url"):
                zh_ambient = dict(ambient)
                zh["ambient_audio"] = zh_ambient
                dossier["zh"] = zh

        dossier = ensure_chinese_variants(dossier)

        # Prefer Chinese chrome when the listener wrote in Chinese and ZH prose exists
        raw_msg = str(context.get("raw_message") or "")
        prefer_zh = re_has_cjk(raw_msg)
        default_lang = prefer_chinese_variant(raw_msg) if prefer_zh else "en"
        if prefer_zh:
            context["prefer_zh"] = True
            context["prefer_lang"] = default_lang

        # Seed minimal Chinese layers from catalog titles so 简体/繁体 switcher
        # appears even before LLM/corpus prose arrives.
        if prefer_zh and not dossier_has_zh(dossier):
            from aulos_skills.i18n import to_traditional

            title_zh = str(context.get("work_title_zh") or "").strip()
            if not title_zh and context.get("work_id"):
                from aulos_skills.identity import load_catalog

                work = load_catalog().works.get(str(context.get("work_id")))
                if work is not None:
                    title_zh = str(work.canonical_title_zh or "")
            composer_zh = ""
            if context.get("composer_id"):
                from aulos_skills.identity import load_catalog

                card = load_catalog().composers.get(str(context.get("composer_id")))
                if card is not None:
                    composer_zh = str(card.name_zh or "")
            seed = {
                "work_title": title_zh or work_title,
                "composer": composer_zh or composer,
                "listening_thesis": "",
                "work_introduction": "",
                "era": str(dossier.get("era") or ""),
                "form": str(dossier.get("form") or ""),
                "catalog": str(dossier.get("catalog") or ""),
            }
            # Chinese lede — never paste English thesis into zh seed
            seed["listening_thesis"] = f"《{seed['work_title']}》聆听导赏。"
            dossier["zh"] = seed
            dossier["zh_hans"] = dict(seed)
            dossier["zh_hant"] = {
                **{k: to_traditional(v) if isinstance(v, str) else v for k, v in seed.items()},
            }
            dossier = ensure_chinese_variants(dossier)

        thesis_en = str(dossier.get("listening_thesis") or "").strip()
        thesis_zh = ""
        if dossier_has_zh(dossier):
            thesis_zh = str((dossier.get("zh") or dossier.get("zh_hans") or {}).get("listening_thesis") or "").strip()
        summary = (thesis_zh if prefer_zh and thesis_zh else thesis_en) or thesis_zh or (
            f"A structured listening path for {work_title}."
        )
        html_default = default_lang if (prefer_zh and dossier_has_zh(dossier)) else "en"
        html = render_bilingual_guide_html(
            dossier=dossier,
            work_title=work_title,
            composer=composer,
            summary_en=thesis_en,
            summary_zh=thesis_zh,
            default_lang=html_default,
        )
        from aulos_skills.external_review import snapshot_draft

        rounds = dict(context.get("generation_rounds") or {})
        if not rounds.get("draft_v1"):
            context["guide_html"] = html
            context["summary"] = summary
            snapshot_draft(context, which="draft_v1", guide_html=html, summary=summary)
        return {
            "guide_html": html,
            "summary": summary,
            "composer": composer,
            "work_title": work_title,
            "generation_rounds": dict(context.get("generation_rounds") or {}),
        }

    def _run_external_review(self, context: dict[str, Any]) -> dict[str, Any]:
        from aulos_skills.external_review import build_external_review_report, snapshot_draft
        from aulos_skills.revise_repair import rescore_draft_v1_with_report
        from aulos_skills.review_targets import intents_from_expert_report
        from aulos_skills.targeted_revise import ROUNDS_SCHEMA_V2, _append_history, _score_snapshot, _utcnow_iso

        html = str(context.get("guide_html") or "")
        if html and not (context.get("generation_rounds") or {}).get("draft_v1"):
            snapshot_draft(
                context,
                which="draft_v1",
                guide_html=html,
                summary=str(context.get("summary") or ""),
            )
        llm_complete = context.get("llm_external_review_complete")
        if not callable(llm_complete):
            llm_complete = context.get("llm_critic_complete")
        if not callable(llm_complete):
            llm_complete = None
        report = build_external_review_report(context, llm_complete=llm_complete)
        corrections = list(context.get("critique_corrections") or [])
        for c in report.get("required_corrections") or []:
            if c and str(c) not in corrections:
                corrections.append(str(c))
        context["critique_corrections"] = corrections[:16]
        context["external_review_report"] = report
        rounds = dict(context.get("generation_rounds") or {})
        rounds["review_report"] = report
        rounds["schema"] = ROUNDS_SCHEMA_V2
        context["generation_rounds"] = rounds
        # Re-score draft_v1 with hard-flaw penalties from the expert report
        rescore_draft_v1_with_report(context, report)
        score = _score_snapshot(html or str((rounds.get("draft_v1") or {}).get("guide_html") or ""), context)
        intents = intents_from_expert_report(report)
        _append_history(
            context,
            {
                "id": f"rev-review-{_utcnow_iso()}",
                "at": _utcnow_iso(),
                "source": "expert",
                "summary": str(report.get("summary") or report.get("verdict") or "expert review")[:200],
                "targets": sorted({t for i in intents for t in (i.get("targets") or [])}),
                "scope": "review",
                "score_before": {"pct": score["pct"], "hard_flaws": score["hard_flaws"]},
                "score_after": {"pct": score["pct"], "hard_flaws": score["hard_flaws"]},
                "diff_summary": [f"verdict={report.get('verdict')}", f"findings={len(report.get('findings') or [])}"],
                "intent_ids": [str(i.get("id")) for i in intents],
            },
        )
        if report.get("verdict") in {"FAIL", "REVISE"}:
            context["external_review_needs_revise"] = True
        return {
            "external_review_report": report,
            "critique_corrections": list(context.get("critique_corrections") or []),
            "generation_rounds": dict(context.get("generation_rounds") or {}),
            "review_intents": intents,
        }

    def _run_revise(self, context: dict[str, Any]) -> dict[str, Any]:
        from aulos_skills.targeted_revise import run_targeted_revise

        report = dict(context.get("external_review_report") or {})
        corrections = list(context.get("critique_corrections") or [])
        for c in report.get("required_corrections") or []:
            if c and str(c) not in corrections:
                corrections.append(str(c))
        context["critique_corrections"] = corrections

        llm_complete = context.get("llm_revise_complete")
        if not callable(llm_complete):
            llm_complete = context.get("llm_external_review_complete")
        if not callable(llm_complete):
            llm_complete = None

        return run_targeted_revise(
            context,
            report=report,
            human_notes=str(context.get("review_notes") or "") or None,
            llm_complete=llm_complete,
            allow_full_compose=self._run_compose,
        )

    def _run_eval(self, context: dict[str, Any]) -> dict[str, Any]:
        html = str(context.get("guide_html") or "")
        html_l = html.lower()
        depth_points = point_texts((context.get("depth_dossier") or {}).get("depth_points") or [])
        listening_map = list((context.get("depth_dossier") or {}).get("listening_map") or [])
        score = 0
        notes: list[str] = []
        # specificity
        if len(depth_points) >= 3 and ("var" in html_l or "form" in html_l or len(listening_map) >= 2):
            score += 2
        elif depth_points:
            score += 1
            notes.append("Add more concrete landmarks")
        else:
            notes.append("Missing depth specificity")
        # ear-actionability
        earish = sum(1 for p in depth_points if any(w in p.lower() for w in ("listen", "hear", "notice", "track", "lock")))
        earish += sum(1 for m in listening_map if isinstance(m, dict) and "cue" in m)
        if earish >= 3 and listening_map:
            score += 2
        elif earish or listening_map:
            score += 1
            notes.append("Strengthen ear cues")
        else:
            notes.append("No ear-actionable cues")
        # source hygiene
        myth_ok = (
            "legend" in html_l
            or "caveat" in html_l
            or "debated" in html_l
            or "myths" in html_l
            or "传说" in html
            or "存疑" in html
            or not context.get("corpus_hit")
        )
        score += 2 if myth_ok else 1
        if not myth_ok:
            notes.append("Label legends vs facts")
        # structure — Salon Codex chambers (EN or ZH chrome)
        needed = (
            "listening map",
            "聆听地图",
            "practice",
            "练习聆听",
            "composer",
            "作曲家",
            "anatomy",
            "作品解剖",
        )
        structure_hits = sum(1 for n in needed if n in html_l or n in html)
        # bilingual craft
        bilingual = (
            'data-lang="zh-Hans"' in html
            or 'data-lang="zh-Hant"' in html
            or 'data-lang="zh"' in html
        ) and 'data-lang="en"' in html
        rich_identity = bool(
            context.get("corpus_hit")
            or context.get("synthesize_hit")
            or context.get("family_hints")
            or context.get("work_id")
        )
        # Full atelier coverage when identity/family/corpus resolved (product bar vs thin cold path)
        atelier_pairs = (
            ("id='composer-", 'id="composer-', "作曲家"),
            ("id='genesis-", 'id="genesis-', "创作背景与时代"),
            ("id='stature-", 'id="stature-', "何以传世"),
            ("id='sound-", 'id="sound-', "声响世界"),
            ("id='interpretations-", 'id="interpretations-', "名家演绎"),
            ("id='media-", 'id="media-', "聆听室"),
        )
        atelier_hits = 0
        missing_atelier: list[str] = []
        for en_sq, en_dq, zh_label in atelier_pairs:
            present = en_sq in html_l or en_dq in html_l or zh_label in html
            if present:
                atelier_hits += 1
            else:
                missing_atelier.append(zh_label)
        if rich_identity:
            media_hits = sum(
                1
                for n in ("interpretations", "名家演绎", "discogs", "sound world", "声响世界", "聆听室")
                if n.lower() in html_l or n in html
            )
            structure_hits += 1 if media_hits >= 2 else 0
            structure_hits += 1 if atelier_hits >= 4 else 0
            if atelier_hits < 4:
                notes.append(
                    "Missing atelier chambers: " + ", ".join(missing_atelier[:4])
                )
        structure_hits += 1 if bilingual else 0
        has_ambient = 'id="aulos-ambient"' in html or "data-ambient-player" in html
        if has_ambient:
            structure_hits += 1
        else:
            notes.append("Missing ambient listening player (soft — no work-matched audio/video)")
        score += 2 if structure_hits >= 4 else (1 if structure_hits >= 2 else 0)
        if structure_hits < 4:
            notes.append("Expand Salon Codex chambers")
        if not bilingual and (context.get("corpus_hit") or context.get("synthesize_hit")):
            notes.append("Add Chinese/English bilingual panes")
        # craft
        score += 2 if "<!DOCTYPE html>" in html and ("Fraunces" in html or "Noto Serif SC" in html) else (1 if html else 0)
        if rich_identity and atelier_hits < 4:
            # Identity-resolved guides must ship the full atelier shelf (Goldberg parity bar)
            score = min(score, 7)
            passed = False
        else:
            passed = score >= 8
        # Ambient absence is soft (SPEC-006): do not alone force fail.
        if context.get("decontam_failed"):
            notes.append("Decontam gate failed — foreign chambers remain")
            score = min(score, 7)
            passed = False
        if context.get("review_failed"):
            notes.append("本意偏离已拦截 — Intent Critic / review gate failed")
            score = min(score, 7)
            passed = False
        # SPEC-024 chamber contracts — identity-resolved shelves must meet craft floors
        from aulos_skills.chamber_contracts import audit_chamber_contracts
        from aulos_skills.product_scorecard import score_product

        dossier = dict(context.get("corpus_dossier") or {})
        identity_resolved = bool(
            context.get("work_id")
            or context.get("corpus_hit")
            or (context.get("family_hints") and context.get("synthesize_hit"))
        )
        contract_gaps = audit_chamber_contracts(
            dossier, identity_resolved=identity_resolved
        )
        high_gaps = [g for g in contract_gaps if g.get("severity") == "high"]
        if high_gaps:
            notes.extend(f"Contract: {g.get('note')}" for g in high_gaps[:4])
            score = min(score, 7)
            passed = False
        elif any(g.get("severity") == "medium" for g in contract_gaps) and identity_resolved:
            med_notes = [
                f"Contract: {g.get('note')}"
                for g in contract_gaps
                if g.get("severity") == "medium"
            ]
            notes.extend(med_notes[:3])
            if len(med_notes) >= 3:
                score = min(score, 7)
                passed = False

        # SPEC-025 ProductScorecard — reader quality owns eval_pass (process stays diagnostic)
        product = score_product(html=html, context=context, dossier=dossier)
        context["product_scorecard"] = product.to_dict()
        hard_gate = bool(
            context.get("decontam_failed")
            or context.get("review_failed")
            or high_gaps
        )
        if not product.pass_:
            for f in product.findings:
                if f.severity == "high":
                    note = f"Product: {f.note}"
                    if note not in notes:
                        notes.append(note)
                    if len([n for n in notes if n.startswith("Product:")]) >= 4:
                        break
            score = min(score, 7)
            passed = False
        else:
            notes.append(f"ProductScore {product.pct}% {product.band}")
            if product.band == "strong":
                score = max(score, 10)
            elif product.band == "solid":
                score = max(score, 9)
            # Product can lift soft atelier shortfalls; never revive decontam/review/contracts
            if not hard_gate:
                passed = True

        out = {
            "eval_score": score,
            "pass": passed,
            "eval_notes": "; ".join(notes) if notes else "Meets Salon Codex 导赏 quality bar",
            "product_scorecard": product.to_dict(),
        }
        # SPEC-019 — process scorecard rollup (does not replace legacy eval_score)
        context.update(out)
        process = rollup_process(context)
        out["process_scorecard"] = process
        context["process_scorecard"] = process
        from aulos_skills.external_review import build_rounds_comparison

        comparison = build_rounds_comparison(context)
        out["generation_rounds"] = dict(context.get("generation_rounds") or {})
        out["rounds_comparison"] = comparison
        return out



def run_report_to_dict(report: SkillRunReport) -> dict[str, Any]:
    return {
        "work_title": report.work_title,
        "composer": report.composer,
        "summary": report.summary,
        "guide_html": report.guide_html,
        "steps": [s.to_workflow_dict() for s in report.steps],
        "skill_versions": report.skill_versions,
        "eval_pass": report.eval_pass,
        "eval_score": report.eval_score,
        "source": report.source,
        "context_keys": sorted(report.context.keys()),
    }
