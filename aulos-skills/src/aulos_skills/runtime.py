"""SkillRuntime — execute domain-runtime listening skills with observability."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import yaml

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

_DECONTAM_MAX_REWORK = 1


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
        if trigger in DECONTAM_TRIGGERS:
            outputs, detail = self._decontam_gate(trigger, skill, context, outputs, detail)
        context.update(outputs)
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

    def _decontam_gate(
        self,
        trigger: str,
        skill: SkillManifest,
        context: dict[str, Any],
        outputs: dict[str, Any],
        detail: str,
    ) -> tuple[dict[str, Any], str]:
        """Validate node outputs; scrub + rework once when polluted (SPEC-009)."""
        family_snap = dict(context.get("_last_matched_family") or {})
        for attempt in range(_DECONTAM_MAX_REWORK + 1):
            report = validate_node_outputs(
                trigger, context, outputs, family=family_snap or None
            )
            if report.ok:
                if attempt > 0:
                    record_decontam_event(
                        context,
                        trigger=trigger,
                        attempt=attempt,
                        report=report,
                        repaired=True,
                    )
                    detail = f"{detail} | decontam-rework ok"
                return outputs, detail

            if attempt >= _DECONTAM_MAX_REWORK:
                record_decontam_event(
                    context,
                    trigger=trigger,
                    attempt=attempt,
                    report=report,
                    repaired=False,
                )
                # Last-chance scrub of dossier / HTML context fields
                self._apply_decontam_scrub(trigger, context, outputs, report.markers_used)
                detail = (
                    f"{detail} | decontam-fail "
                    f"({', '.join(f.marker for f in report.findings[:4])})"
                )
                return outputs, detail

            apply_rework_hints(context, report)
            self._apply_decontam_scrub(trigger, context, outputs, report.markers_used)
            # Re-run node with refuse_families / expanded markers
            outputs = self._dispatch(trigger, skill, context)
            family_snap = dict(context.get("_last_matched_family") or {})
            detail = self._detail_from_outputs(trigger, outputs)
        return outputs, detail

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
                cleaned = self._scrub_foreign_chambers(
                    dossier,
                    work_title=work_title or str(dossier.get("work_title") or ""),
                    conflict_markers=list(context.get("conflict_markers") or []),
                    force_ambient_scrub=True,
                )
                outputs["corpus_dossier"] = cleaned
                context["corpus_dossier"] = cleaned
        elif trigger == "listening.width":
            width = dict(outputs.get("width_dossier") or context.get("width_dossier") or {})
            salon = dict(width.get("salon_dossier") or context.get("corpus_dossier") or {})
            if salon:
                cleaned = self._scrub_foreign_chambers(
                    salon,
                    work_title=work_title or str(salon.get("work_title") or ""),
                    conflict_markers=list(context.get("conflict_markers") or []),
                    force_ambient_scrub=True,
                )
                width["salon_dossier"] = cleaned
                outputs["width_dossier"] = width
                context["width_dossier"] = width
                context["corpus_dossier"] = cleaned
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
        elif trigger == "listening.compose":
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
            points = outputs.get("width_points") or []
            return "; ".join(points[:2]) if points else "Width dossier ready"
        if trigger == "listening.depth":
            points = outputs.get("depth_points") or []
            return "; ".join(points[:2]) if points else "Depth dossier ready"
        if trigger == "listening.compose":
            return str(outputs.get("summary") or "Guide composed")[:280]
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
        if trigger == "listening.eval":
            return self._run_eval(context)
        return {"note": f"No deterministic executor for {trigger}; skill loaded only"}

    def _run_route(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "plan": (
                "intake → corpus → synthesize → width → depth → compose → eval "
                "(Salon Codex atelier — curated or compounded)"
            )
        }

    def _run_intake(self, context: dict[str, Any]) -> dict[str, Any]:
        from aulos_skills.intake_parse import guess_composer_and_title
        from aulos_skills.identity import load_catalog

        message = str(context.get("raw_message") or "")
        hint = str(context.get("work_hint") or "")
        text = f"{hint} {message}".strip()
        lowered = text.lower()

        # Catalog-driven identity (SPEC-008) — no per-work elif trees.
        identity = resolve_identity(message, work_hint=hint)
        out = identity.to_context()

        if identity.status == "work" and identity.work_title:
            work_title = identity.work_title
            composer = identity.composer_name
        else:
            cat = load_catalog()
            guessed = guess_composer_and_title(text, catalog_composers=cat.composers)
            work_title = guessed["work_title"] or "Unspecified classical work"
            composer = identity.composer_name or guessed["composer"]
            if guessed.get("composer_id") and not out.get("composer_id"):
                out["composer_id"] = guessed["composer_id"]
            # Prefer catalog work_title when soft-guess only got composer_only
            if identity.status == "composer_only" and not guessed["work_title"]:
                work_title = f"{composer} — unspecified work" if composer else work_title

        # Prefer Discogs / KB seed title+composer when Catalog did not lock a work.
        kb = dict(context.get("kb_dossier") or {})
        prov = dict(kb.get("_provenance") or {})
        if prov.get("source") == "discogs" or (kb.get("_provenance") or {}).get("discogs"):
            if kb.get("composer"):
                composer = str(kb["composer"])
            if kb.get("work_title"):
                work_title = str(kb["work_title"])
            # Discogs path is not a Catalog work — clear wrong family hints.
            if identity.status != "work":
                out["family_hints"] = []
                out["corpus_keys"] = []
                out["work_id"] = None
                out["ambient_ref"] = None

        goal = "structural_learning"
        if any(w in lowered for w in ("first time", "first hearing", "beginner")) or "入门" in text:
            goal = "first_hearing"
        elif any(w in lowered for w in ("perform", "practice", "rehearse")) or "练习" in text:
            goal = "performance_prep"

        out.update(
            {
                "work_title": work_title,
                "composer_guess": composer,
                "composer": composer,
                "listener_goal": goal,
                "experience_level": "curious_listener",
                "corpus_keys": list(out.get("corpus_keys") or identity.corpus_keys),
                "family_hints": list(out.get("family_hints") or ([] if not identity.family_id else [identity.family_id])),
            }
        )
        return out

    def _synthesize_assets_dir(self, skill: SkillManifest) -> Path:
        return skill.path / "assets"

    def _load_synthesize_index(self, skill: SkillManifest) -> dict[str, Any]:
        path = self._synthesize_assets_dir(skill) / "index.yaml"
        if not path.is_file():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _match_composer_card(self, skill: SkillManifest, text: str, composer_guess: str) -> dict[str, Any]:
        index = self._load_synthesize_index(skill)
        blob = f"{composer_guess} {text}".lower()
        for entry in index.get("composers") or []:
            aliases = [str(a).lower() for a in (entry.get("aliases") or [])]
            if any(a and a in blob for a in aliases):
                path = self._synthesize_assets_dir(skill) / "composers" / str(entry.get("path") or "")
                if path.is_file():
                    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {}

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
        # Prefer explicit hints (catalog family_id) — still verify path exists.
        for hint in family_hints:
            for entry in index.get("families") or []:
                if str(entry.get("id") or "") == hint:
                    path = self._synthesize_assets_dir(skill) / "families" / str(entry.get("path") or "")
                    if path.is_file():
                        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        best: dict[str, Any] = {}
        best_score = 0
        for entry in index.get("families") or []:
            path = self._synthesize_assets_dir(skill) / "families" / str(entry.get("path") or "")
            if not path.is_file():
                continue
            family = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
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

        text = f"{context.get('work_title', '')} {context.get('raw_message', '')}"
        composer_guess = str(context.get("composer_guess") or existing.get("composer") or "")
        family_hints = list(context.get("family_hints") or [])
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
        composer_name = (
            str(card.get("composer") or "")
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
        if kb_dossier:
            layers.append(kb_dossier)
            sources.append("kb-rag")
        if family:
            layers.append(family_to_dossier(family, composer=composer_name, work_title=work_title))
            sources.append(f"family:{family.get('family_id')}")
        if card:
            layers.append(composer_to_dossier(card))
            sources.append("composer-card")
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
            layers.append(llm_dossier)
            sources.append("llm")

        if not layers:
            # last-resort thin scaffold still better than raw sentence title
            thin = empty_dossier()
            thin["work_title"] = work_title or "Classical work"
            thin["composer"] = composer_name
            thin["listening_thesis"] = (
                f"Listen for large-scale form and recurring motives in {thin['work_title']}."
            )
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
            layers.append(thin)
            sources.append("generic-scaffold")

        merged = merge_dossiers(*layers)
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
        rag_hits = list(context.get("rag_hits") or [])
        if rag_hits and len(merged.get("width_points") or []) < 4:
            extra = [f"From prior research cache: {h[:220]}" for h in rag_hits[:2]]
            merged["width_points"] = list(merged.get("width_points") or []) + extra
            if "kb-rag" not in sources:
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

        return {
            "synthesize_hit": True,
            "synthesize_source": "+".join(sources),
            "corpus_dossier": merged,
            "work_title": merged.get("work_title") or work_title,
            "composer_guess": merged.get("composer") or composer_name,
            "composer": merged.get("composer") or composer_name,
            "work_id": context.get("work_id"),
            "conflict_markers": list(context.get("conflict_markers") or []),
        }

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

        for key in ("listening_thesis", "work_introduction", "form", "catalog", "era"):
            val = out.get(key)
            if isinstance(val, str) and polluted(val.lower()):
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

        zh = coerce_dict(out.get("zh") or out.get("zh_hans"))
        if zh:
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
            out["zh"] = zh
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
            points = [*points, f"Live enrichment note: {enrichment[:400]}"]
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
                f"Identify large-scale form of “{title}” and the unit the ear should lock onto first.",
                "List movement/section landmarks with tempo and character words.",
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
        # Ensure compose-critical fields from width/depth are present on EN layer
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

        dossier.setdefault("work_title", work_title)
        dossier.setdefault("composer", composer)

        corpus_dir = self._corpus_assets_dir_for_key("")
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
        return {
            "guide_html": html,
            "summary": summary,
            "composer": composer,
            "work_title": work_title,
        }

    def _run_eval(self, context: dict[str, Any]) -> dict[str, Any]:
        html = str(context.get("guide_html") or "")
        html_l = html.lower()
        depth_points = list((context.get("depth_dossier") or {}).get("depth_points") or [])
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
        earish += sum(1 for m in listening_map if "cue" in m)
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
            ("id='composer-", "作曲家"),
            ("id='genesis-", "创作背景与时代"),
            ("id='stature-", "何以传世"),
            ("id='sound-", "声响世界"),
            ("id='interpretations-", "名家演绎"),
            ("id='media-", "聆听室"),
        )
        atelier_hits = 0
        missing_atelier: list[str] = []
        for en_id, zh_label in atelier_pairs:
            present = en_id in html_l or zh_label in html
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
            notes.append("Missing ambient listening player")
        score += 2 if structure_hits >= 4 else (1 if structure_hits >= 2 else 0)
        if structure_hits < 4:
            notes.append("Expand Salon Codex chambers")
        if not bilingual and (context.get("corpus_hit") or context.get("synthesize_hit")):
            notes.append("Add Chinese/English bilingual panes")
        # craft
        score += 2 if "<!DOCTYPE html>" in html and ("Fraunces" in html or "Noto Serif SC" in html) else (1 if html else 0)
        if not has_ambient:
            score = min(score, 7)
            passed = False
        elif rich_identity and atelier_hits < 4:
            # Identity-resolved guides must ship the full atelier shelf (Goldberg parity bar)
            score = min(score, 7)
            passed = False
        else:
            passed = score >= 8
        if context.get("decontam_failed"):
            notes.append("Decontam gate failed — foreign chambers remain")
            score = min(score, 7)
            passed = False
        return {
            "eval_score": score,
            "pass": passed,
            "eval_notes": "; ".join(notes) if notes else "Meets Salon Codex 导赏 quality bar",
        }


def _li(items: list[Any]) -> str:
    out = []
    for p in items:
        if isinstance(p, dict):
            # YAML may parse "Label: rest" bullets as single-key maps
            text = "; ".join(f"{k}: {v}" for k, v in p.items())
        else:
            text = str(p)
        if text:
            out.append(f"<li>{escape(text)}</li>")
    return "".join(out)


def _p(text: str) -> str:
    text = (text or "").strip()
    return f"<p>{escape(text)}</p>" if text else ""


def render_guide_html(
    *,
    work_title: str,
    composer: str,
    era: str,
    form: str,
    summary: str,
    width_points: list[str],
    depth_points: list[str],
    listening_map: list[dict[str, str]],
    practice_notes: list[str],
    related_works: list[dict[str, str]] | list[str],
    catalog: str = "",
    work_introduction: str = "",
    myths_and_caveats: list[str] | None = None,
    composer_portrait: dict[str, Any] | None = None,
    composer_profile: dict[str, Any] | None = None,
    genesis: dict[str, Any] | None = None,
    historical_reasons: list[str] | None = None,
    reception_arc: str = "",
    variation_deepdives: list[dict[str, Any]] | None = None,
    sound_world: dict[str, Any] | None = None,
    interpretations: list[dict[str, Any]] | None = None,
    appreciation_videos: list[dict[str, Any]] | None = None,
    vinyl_and_discography: list[dict[str, Any]] | None = None,
) -> str:
    myths_and_caveats = myths_and_caveats or []
    composer_portrait = composer_portrait or {}
    composer_profile = composer_profile or {}
    genesis = genesis or {}
    historical_reasons = historical_reasons or []
    variation_deepdives = variation_deepdives or []
    sound_world = sound_world or {}
    interpretations = interpretations or []
    appreciation_videos = appreciation_videos or []
    vinyl_and_discography = vinyl_and_discography or []

    related_norm: list[dict[str, str]] = []
    for item in related_works:
        if isinstance(item, dict):
            related_norm.append({"title": str(item.get("title") or ""), "why": str(item.get("why") or "")})
        else:
            related_norm.append({"title": str(item), "why": ""})

    map_blocks = "".join(
        f"<article class='map-item'><h3>{escape(str(m.get('label', '')))}</h3>"
        f"<p>{escape(str(m.get('cue', '')))}</p></article>"
        for m in listening_map
    )
    related_blocks = "".join(
        f"<article class='rel'><h3>{escape(r['title'])}</h3>"
        f"{_p(r['why'])}</article>"
        for r in related_norm
        if r["title"]
    )
    deepdive_blocks = "".join(
        f"<article class='map-item'><h3>{escape(str(d.get('title', '')))}</h3>"
        f"<p>{escape(str(d.get('note', '')))}</p></article>"
        for d in variation_deepdives
    )
    interp_blocks = "".join(
        (
            "<article class='interp'>"
            f"<h3>{escape(str(i.get('artist', '')))} · {escape(str(i.get('year', '')))}</h3>"
            f"<p class='meta-line'>{escape(str(i.get('instrument', '')))} — {escape(str(i.get('era_note', '')))}</p>"
            f"<p>{escape(str(i.get('why_listen', '')))}</p>"
            + (
                f"<p class='links'><a href=\"{escape(str(i['youtube_url']))}\" target=\"_blank\" rel=\"noopener\">YouTube</a></p>"
                if i.get("youtube_url")
                else ""
            )
            + (
                f"<p class='links'><a href=\"{escape(str(i['discogs_url']))}\" target=\"_blank\" rel=\"noopener\">Discogs</a></p>"
                if i.get("discogs_url")
                else ""
            )
            + "</article>"
        )
        for i in interpretations
    )
    video_blocks = "".join(
        f"<article class='media'><h3><a href=\"{escape(str(v.get('url', '')))}\" target=\"_blank\" rel=\"noopener\">"
        f"{escape(str(v.get('title', '')))}</a></h3><p>{escape(str(v.get('why', '')))}</p></article>"
        for v in appreciation_videos
        if v.get("url")
    )
    vinyl_blocks = "".join(
        f"<article class='media'><h3><a href=\"{escape(str(v.get('url', '')))}\" target=\"_blank\" rel=\"noopener\">"
        f"{escape(str(v.get('label', '')))}</a></h3><p>{escape(str(v.get('note', '')))}</p></article>"
        for v in vinyl_and_discography
        if v.get("url")
    )

    portrait_html = ""
    if composer_portrait.get("image_url"):
        portrait_html = (
            "<figure class='portrait'>"
            f"<img src=\"{escape(str(composer_portrait['image_url']))}\" "
            f"alt=\"Portrait of {escape(composer)}\" "
            f"width=\"800\" height=\"1040\" "
            f"loading=\"eager\" decoding=\"async\" fetchpriority=\"high\" "
            f"referrerpolicy=\"no-referrer\"/>"
            f"<figcaption>{escape(str(composer_portrait.get('caption') or ''))}"
            f"<span class='credit'>{escape(str(composer_portrait.get('credit') or ''))}</span>"
            "</figcaption></figure>"
        )

    profile_bits = []
    if composer_profile.get("lifespan"):
        profile_bits.append(f"<p class='meta-line'>{escape(str(composer_profile['lifespan']))}</p>")
    for key in ("summary", "temperament", "place_in_oeuvre", "place_in_history"):
        if composer_profile.get(key):
            label = {
                "summary": "Life",
                "temperament": "Temperament",
                "place_in_oeuvre": "In the oeuvre",
                "place_in_history": "In music history",
            }[key]
            profile_bits.append(f"<h3>{label}</h3>{_p(str(composer_profile[key]))}")
    profile_html = "".join(profile_bits)

    genesis_rows = []
    for key, label in (
        ("year", "Year"),
        ("place", "Place"),
        ("publication", "Publication"),
        ("patronage", "Patronage"),
        ("background", "Background"),
        ("instrument_culture", "Instrument culture"),
    ):
        if genesis.get(key):
            genesis_rows.append(
                f"<div class='fact'><span>{label}</span><p>{escape(str(genesis[key]))}</p></div>"
            )
    genesis_html = "".join(genesis_rows)

    sound_html_parts = []
    if sound_world.get("original_instrument"):
        sound_html_parts.append(f"<h3>Original instrument</h3>{_p(str(sound_world['original_instrument']))}")
    if sound_world.get("ensemble_notes"):
        sound_html_parts.append(f"<h3>Ensemble / scoring</h3>{_p(str(sound_world['ensemble_notes']))}")
    modes = list(sound_world.get("modern_modes") or [])
    if modes:
        sound_html_parts.append(f"<h3>Modern listening modes</h3><ul>{_li([str(m) for m in modes])}</ul>")
    sound_html = "".join(sound_html_parts)

    chips = "".join(
        f"<span class='chip'>{escape(c)}</span>"
        for c in [composer, catalog, era, form]
        if c
    )

    sections: list[str] = []
    # Portrait early — mobile readers must see the oil painting without hunting
    if portrait_html or profile_html:
        sections.append(
            f"<section id='composer'><h2>Composer</h2>"
            f"<div class='composer-grid'>{portrait_html}<div class='composer-copy'>{profile_html}</div></div>"
            f"</section>"
        )
    if work_introduction:
        sections.append(f"<section id='introduction'><h2>The work</h2>{_p(work_introduction)}</section>")
    if genesis_html:
        sections.append(f"<section id='genesis'><h2>Genesis &amp; world</h2><div class='facts'>{genesis_html}</div></section>")
    if historical_reasons or reception_arc:
        reasons_ul = f"<ul>{_li(historical_reasons)}</ul>" if historical_reasons else ""
        sections.append(
            f"<section id='stature'><h2>Why it endures</h2>{reasons_ul}{_p(reception_arc)}</section>"
        )
    if width_points:
        sections.append(f"<section id='wide'><h2>Wide research</h2><ul>{_li(width_points)}</ul></section>")
    anatomy_inner = ""
    if depth_points:
        anatomy_inner += f"<h3>Deep research</h3><ul>{_li(depth_points)}</ul>"
    if deepdive_blocks:
        anatomy_inner += f"<h3>Selected deep dives</h3><div class='map'>{deepdive_blocks}</div>"
    if map_blocks:
        anatomy_inner += f"<h3>Listening map</h3><div class='map'>{map_blocks}</div>"
    if anatomy_inner:
        sections.append(f"<section id='anatomy'><h2>Anatomy of the work</h2>{anatomy_inner}</section>")
    if sound_html:
        sections.append(f"<section id='sound'><h2>Sound world</h2>{sound_html}</section>")
    if related_blocks:
        sections.append(f"<section id='kindred'><h2>Kindred works</h2><div class='rels'>{related_blocks}</div></section>")
    if interp_blocks:
        sections.append(
            f"<section id='interpretations'><h2>Famous interpretations</h2><div class='interps'>{interp_blocks}</div></section>"
        )
    media_inner = ""
    if video_blocks:
        media_inner += f"<h3>YouTube &amp; appreciation</h3><div class='medias'>{video_blocks}</div>"
    if vinyl_blocks:
        media_inner += f"<h3>Discogs &amp; vinyl shelf</h3><div class='medias'>{vinyl_blocks}</div>"
    if media_inner:
        sections.append(f"<section id='media'><h2>Listening room media</h2>{media_inner}</section>")
    if practice_notes:
        sections.append(
            f"<section id='practice'><h2>How to practice listening</h2><ul>{_li(practice_notes)}</ul></section>"
        )
    if myths_and_caveats:
        sections.append(
            f"<section id='caveats'><h2>Myths &amp; caveats</h2><ul>{_li(myths_and_caveats)}</ul></section>"
        )

    body_sections = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{escape(work_title)} — Aulos Listening Guide</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
:root {{
  --stage: #0c1216; --panel: #151c22; --ink: #e8efe9; --mute: #9aafa3;
  --accent: #c9a66b; --line: rgba(232,239,233,0.11); --glow: rgba(201,166,107,0.14);
  --varnish: rgba(40,28,18,0.55);
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: var(--stage); color: var(--ink); font-family: Manrope, system-ui, sans-serif; }}
body {{
  min-height: 100vh;
  background:
    radial-gradient(ellipse 55% 40% at 85% 0%, var(--glow), transparent 50%),
    radial-gradient(ellipse 45% 35% at 0% 20%, rgba(90,70,40,0.12), transparent 55%),
    linear-gradient(168deg, #10171c 0%, #0c1216 48%, #12191f 100%);
}}
.wrap {{ max-width: 44rem; margin: 0 auto; padding: 2.75rem 1.25rem 4.5rem; }}
.eyebrow {{ letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent); font-size: 0.72rem; font-weight: 700; margin: 0 0 0.85rem; }}
h1 {{ font-family: Fraunces, Georgia, serif; font-weight: 700; font-size: clamp(1.75rem, 7vw, 3.05rem); line-height: 1.07; letter-spacing: -0.03em; margin: 0 0 0.85rem; }}
.lede {{ color: var(--mute); font-size: clamp(1rem, 3.6vw, 1.1rem); line-height: 1.7; margin: 0 0 1.5rem; max-width: 38rem; font-family: Fraunces, Georgia, serif; font-weight: 500; font-variation-settings: "opsz" 72; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0 0 2.5rem; }}
.chip {{ border: 1px solid var(--line); background: rgba(21,28,34,0.85); padding: 0.4rem 0.7rem; font-size: 0.82rem; color: var(--mute); max-width: 100%; }}
section {{ margin: 0 0 1.75rem; padding: 1.35rem 0 0; border-top: 1px solid var(--line); background: transparent; }}
h2 {{ font-family: Fraunces, Georgia, serif; font-size: clamp(1.2rem, 4.5vw, 1.45rem); margin: 0 0 0.95rem; letter-spacing: -0.02em; }}
h3 {{ font-family: Fraunces, Georgia, serif; font-size: 1.02rem; margin: 1rem 0 0.45rem; color: var(--ink); font-weight: 600; }}
p {{ color: var(--mute); line-height: 1.65; margin: 0 0 0.75rem; }}
ul {{ margin: 0; padding-left: 1.15rem; display: grid; gap: 0.55rem; color: var(--mute); line-height: 1.55; }}
.composer-grid {{ display: grid; gap: 1.25rem; align-items: start; }}
@media (min-width: 720px) {{
  .composer-grid {{ grid-template-columns: minmax(0, 13.5rem) minmax(0, 1fr); gap: 1.75rem; }}
}}
.portrait {{ margin: 0; width: 100%; }}
.portrait img {{
  width: 100%;
  height: auto;
  max-width: 100%;
  display: block;
  border: 1px solid var(--line);
  box-shadow: 0 18px 40px rgba(0,0,0,0.35);
  filter: saturate(0.92) contrast(1.04);
  background: #1a1510;
}}
.portrait figcaption {{ margin-top: 0.65rem; font-size: 0.82rem; color: var(--mute); line-height: 1.45; }}
.portrait .credit {{ display: block; margin-top: 0.35rem; opacity: 0.75; font-size: 0.75rem; }}
@media (max-width: 719px) {{
  .wrap {{ padding: 1.35rem 1rem 3.25rem; }}
  .meta {{ margin-bottom: 1.5rem; }}
  section {{ margin-bottom: 1.35rem; padding-top: 1.1rem; }}
  .portrait {{
    max-width: 17rem;
    margin: 0 auto;
  }}
  .portrait img {{
    max-height: min(68vh, 26rem);
    width: 100%;
    object-fit: contain;
    object-position: top center;
    box-shadow: 0 12px 28px rgba(0,0,0,0.4);
  }}
  .composer-copy h3:first-child {{ margin-top: 0.35rem; }}
  .map-item, .rel, .interp, .media {{
    padding: 0.75rem 0 0.75rem 0.8rem;
  }}
  .chip {{ font-size: 0.78rem; padding: 0.35rem 0.55rem; }}
}}
.facts {{ display: grid; gap: 0.85rem; }}
.fact span {{ display: block; letter-spacing: 0.14em; text-transform: uppercase; font-size: 0.68rem; color: var(--accent); font-weight: 700; margin-bottom: 0.25rem; }}
.fact p {{ margin: 0; }}
.map, .rels, .interps, .medias {{ display: grid; gap: 0.7rem; }}
.map-item, .rel, .interp, .media {{
  padding: 0.9rem 0 0.9rem 0.95rem;
  border-left: 2px solid var(--accent);
  background: linear-gradient(90deg, rgba(201,166,107,0.06), transparent 70%);
}}
.map-item h3, .rel h3, .interp h3, .media h3 {{ margin: 0 0 0.35rem; font-size: 0.98rem; }}
.meta-line {{ font-size: 0.88rem; color: var(--accent); margin-bottom: 0.35rem; }}
.links {{ margin: 0.35rem 0 0; font-size: 0.88rem; }}
a {{ color: var(--accent); text-underline-offset: 0.18em; }}
a:hover {{ color: var(--ink); }}
footer {{ margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid var(--line); color: var(--mute); font-size: 0.82rem; }}
img {{ max-width: 100%; height: auto; }}
@supports (padding: max(0px)) {{
  .wrap {{
    padding-left: max(1rem, env(safe-area-inset-left));
    padding-right: max(1rem, env(safe-area-inset-right));
    padding-bottom: max(3rem, calc(2rem + env(safe-area-inset-bottom)));
  }}
}}
</style>
</head>
<body>
<main class="wrap">
  <p class="eyebrow">Aulos · Salon Codex listening guide</p>
  <h1>{escape(work_title)}</h1>
  <p class="lede">{escape(summary)}</p>
  <div class="meta">{chips}</div>
  {body_sections}
  <footer>Generated by Aulos SkillRuntime — Salon Codex atelier for deep listening.</footer>
</main>
</body>
</html>
"""



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
