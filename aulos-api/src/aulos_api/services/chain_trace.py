"""Listening-chain diagnostic logs for retrospective 复盘 (SPEC-012)."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any


SCHEMA = "aulos.chain_trace/v1"
_MAX_STR = 480


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clip(value: Any, limit: int = _MAX_STR) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if len(text) <= limit:
            return text
        return text[: limit - 1] + "…"
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, list):
        return [_clip(v, limit=min(limit, 160)) for v in value[:24]]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= 32:
                break
            out[str(k)[:64]] = _clip(v, limit=min(limit, 240))
        return out
    return _clip(str(value), limit=limit)


def _token_set(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-z0-9\u4e00-\u9fff]{3,}", text or "", flags=re.I)}


def _names_overlap(a: str, b: str) -> bool:
    """True when two composer/title strings share a meaningful token."""
    ta, tb = _token_set(a), _token_set(b)
    if not ta or not tb:
        return not (a or "").strip() or not (b or "").strip() or a.strip().lower() == b.strip().lower()
    # Drop ultra-generic musical nouns from overlap proof
    weak = {
        "piano",
        "sonata",
        "concerto",
        "symphony",
        "variation",
        "variations",
        "suite",
        "major",
        "minor",
        "opus",
        "the",
        "and",
        "for",
        "with",
        "奏鸣曲",
        "协奏曲",
        "交响",
        "变奏",
        "组曲",
    }
    ta = {t for t in ta if t not in weak}
    tb = {t for t in tb if t not in weak}
    if not ta or not tb:
        return True  # only weak tokens — do not flag
    return bool(ta & tb)


class ChainTraceBuilder:
    """Accumulate gateway + skill milestones for one listening run."""

    def __init__(self, *, message: str = "", work_hint: str = "") -> None:
        self.trace_id = str(uuid.uuid4())
        self.started_at = _utc_now()
        self.input = {
            "message": _clip(message, 600),
            "work_hint": _clip(work_hint or "", 255),
        }
        self.identity_arc: list[dict[str, Any]] = []
        self.milestones: list[dict[str, Any]] = []
        self._deviations: list[dict[str, Any]] = []
        self.note_identity(
            stage="input",
            composer="",
            work_title=_clip(work_hint or message, 200) or "",
            work_id=None,
        )

    def note_identity(
        self,
        *,
        stage: str,
        composer: str = "",
        work_title: str = "",
        work_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        row: dict[str, Any] = {
            "stage": stage,
            "composer": _clip(composer or "", 200),
            "work_title": _clip(work_title or "", 240),
            "work_id": work_id or None,
        }
        if extra:
            row["extra"] = _clip(extra)
        self.identity_arc.append(row)

    def milestone(
        self,
        mid: str,
        *,
        status: str = "ok",
        summary: str = "",
        facts: dict[str, Any] | None = None,
        signals: list[str] | None = None,
    ) -> None:
        self.milestones.append(
            {
                "id": mid,
                "status": status,
                "at": _utc_now(),
                "summary": _clip(summary, 320) or mid,
                "facts": _clip(facts or {}),
                "signals": list(signals or [])[:16],
            }
        )

    def ingest_skill_context(self, ctx: dict[str, Any] | None) -> None:
        """Pull diagnostic facts already present on SkillRunReport.context."""
        ctx = dict(ctx or {})
        self.milestone(
            "skill.intake",
            status="ok",
            summary=(
                f"Intake identity={ctx.get('identity_status') or 'n/a'} "
                f"title={_clip(ctx.get('work_title'), 80)}"
            ),
            facts={
                "identity_status": ctx.get("identity_status"),
                "identity_reason": ctx.get("identity_reason"),
                "identity_confidence": ctx.get("identity_confidence"),
                "work_id": ctx.get("work_id"),
                "composer_id": ctx.get("composer_id"),
                "composer": ctx.get("composer") or ctx.get("composer_guess"),
                "work_title": ctx.get("work_title"),
                "family_hints": list(ctx.get("family_hints") or [])[:8],
                "corpus_keys": list(ctx.get("corpus_keys") or [])[:8],
            },
        )
        synth_src = str(ctx.get("synthesize_source") or "")
        signals: list[str] = []
        work_id = str(ctx.get("work_id") or "") or None
        if "family:" in synth_src and not work_id:
            signals.append("family_without_work_id")
        self.milestone(
            "skill.synthesize",
            status="warn" if signals else ("ok" if ctx.get("synthesize_hit") or synth_src else "skip"),
            summary=f"Synthesize via {synth_src or 'n/a'}",
            facts={
                "synthesize_hit": bool(ctx.get("synthesize_hit")),
                "synthesize_source": synth_src,
                "corpus_hit": bool(ctx.get("corpus_hit")),
                "work_id": work_id,
                "composer": ctx.get("composer") or ctx.get("composer_guess"),
                "work_title": ctx.get("work_title"),
            },
            signals=signals,
        )
        if signals:
            self._deviations.append(
                {
                    "code": "family_without_work_id",
                    "at_milestone": "skill.synthesize",
                    "summary": "Family pack attached without Catalog work_id — pollution risk",
                    "facts": {"synthesize_source": synth_src},
                }
            )
        # SPEC-018 adversarial review
        intent = dict(ctx.get("intent_lock") or {})
        review_events = list(ctx.get("review_events") or [])
        if intent or review_events:
            failed = bool(ctx.get("review_failed"))
            self.milestone(
                "skill.review",
                status="fail" if failed else "ok",
                summary=(
                    f"IntentLock source={intent.get('source') or 'n/a'} "
                    f"events={len(review_events)} "
                    f"{'FAILED' if failed else 'ok'}"
                ),
                facts={
                    "intent_lock": {
                        "work_title": intent.get("work_title"),
                        "composer": intent.get("composer"),
                        "catalog_numbers": list(intent.get("catalog_numbers") or [])[:8],
                        "form_families": list(intent.get("form_families") or [])[:8],
                        "source": intent.get("source"),
                    },
                    "review_events": review_events[-6:],
                    "review_failed": failed,
                    "critique_corrections": list(ctx.get("critique_corrections") or [])[:6],
                },
                signals=["review_failed"] if failed else [],
            )
            if failed:
                self._deviations.append(
                    {
                        "code": "intent_review_failed",
                        "at_milestone": "skill.review",
                        "summary": "本意偏离已拦截 — adversarial review failed",
                        "facts": {"events": len(review_events)},
                    }
                )
        process = dict(ctx.get("process_scorecard") or {})
        if process:
            rollup = dict(process.get("rollup") or {})
            self.milestone(
                "skill.scorecard",
                status="fail" if rollup.get("hard_fail") else "ok",
                summary=(
                    f"Process scorecard {rollup.get('pct')}% "
                    f"band={rollup.get('band') or 'n/a'}"
                ),
                facts={
                    "pct": rollup.get("pct"),
                    "band": rollup.get("band"),
                    "hard_fail": bool(rollup.get("hard_fail")),
                    "node_count": len(process.get("nodes") or []),
                    "gates": dict(process.get("gates") or {}),
                },
                signals=["scorecard_hard_fail"] if rollup.get("hard_fail") else [],
            )

    def finalize(
        self,
        *,
        work_title: str = "",
        composer: str = "",
        work_id: str | None = None,
        eval_pass: bool | None = None,
        eval_score: int | None = None,
    ) -> dict[str, Any]:
        self.note_identity(
            stage="final",
            composer=composer,
            work_title=work_title,
            work_id=work_id,
        )
        self.milestone(
            "persist",
            status="ok",
            summary=f"Final shelf: {composer or '?'} — {_clip(work_title, 100)}",
            facts={
                "composer": composer,
                "work_title": work_title,
                "work_id": work_id,
                "eval_pass": eval_pass,
                "eval_score": eval_score,
            },
        )
        self._detect_arc_deviations()
        return {
            "schema": SCHEMA,
            "trace_id": self.trace_id,
            "started_at": self.started_at,
            "finished_at": _utc_now(),
            "input": self.input,
            "identity_arc": list(self.identity_arc),
            "milestones": list(self.milestones),
            "deviations": list(self._deviations),
        }

    def _detect_arc_deviations(self) -> None:
        by_stage = {row["stage"]: row for row in self.identity_arc}
        locked = by_stage.get("locked") or by_stage.get("discogs")
        final = by_stage.get("final")
        if not locked or not final:
            return
        lc, lt = str(locked.get("composer") or ""), str(locked.get("work_title") or "")
        fc, ft = str(final.get("composer") or ""), str(final.get("work_title") or "")
        if lc and fc and not _names_overlap(lc, fc):
            self._deviations.append(
                {
                    "code": "composer_drift",
                    "at_milestone": "persist",
                    "summary": f"Composer drifted: locked={lc!r} final={fc!r}",
                    "facts": {"locked": lc, "final": fc},
                }
            )
        if lt and ft and not _names_overlap(lt, ft):
            self._deviations.append(
                {
                    "code": "title_drift",
                    "at_milestone": "persist",
                    "summary": f"Title drifted from locked Discogs/Catalog shelf",
                    "facts": {"locked": _clip(lt, 160), "final": _clip(ft, 160)},
                }
            )


def extract_chain_trace(research: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(research, dict):
        return None
    trace = research.get("chain_trace")
    if isinstance(trace, dict) and trace.get("schema") == SCHEMA:
        return trace
    return None
