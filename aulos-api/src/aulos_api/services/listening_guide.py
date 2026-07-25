"""Classical listening-guide workflow powered by aulos-skills SkillRuntime."""

from __future__ import annotations

import json
import logging
import secrets
import sys
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from aulos_api.db.models import ListeningGuide
from aulos_api.services.knowledge_base import retrieve as kb_retrieve
from aulos_api.services.knowledge_base import upsert_from_report
from aulos_api.services.llm_providers import chat_with_ops_llm, load_llm_config
from aulos_api.services.skills_ops import _load_disabled
from aulos_api.timefmt import to_utc_iso_optional

logger = logging.getLogger("aulos_api.listening")


def _ensure_aulos_skills_importable() -> None:
    try:
        import aulos_skills  # noqa: F401
        return
    except ImportError:
        pass
    sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
    if sibling.is_dir() and str(sibling) not in sys.path:
        sys.path.insert(0, str(sibling))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return to_utc_iso_optional(dt)


def _new_share_slug() -> str:
    return secrets.token_urlsafe(12).replace("-", "").replace("_", "")[:16]


def _research_payload(report: Any) -> dict[str, Any]:
    ctx = getattr(report, "context", None) or {}
    dossier = dict(ctx.get("corpus_dossier") or {})
    if not dossier:
        width = dict(ctx.get("width_dossier") or {})
        dossier = dict(width.get("salon_dossier") or {})
    return {
        "eval_pass": report.eval_pass,
        "eval_score": report.eval_score,
        "skill_versions": report.skill_versions,
        "corpus_hit": bool(ctx.get("corpus_hit")),
        "synthesize_hit": bool(ctx.get("synthesize_hit")),
        "synthesize_source": ctx.get("synthesize_source"),
        "rag_mode": ctx.get("rag_mode"),
        "rag_hit_count": len(ctx.get("rag_hits") or []),
        "corpus_dossier": dossier,
        "work_title": report.work_title,
        "composer": report.composer,
        "summary": report.summary,
    }


async def _optional_llm_dossier(db: Session, work_title: str, composer: str) -> tuple[dict | None, str | None, str]:
    cfg = load_llm_config(db)
    if not cfg.ready_for_live:
        return None, None, "skills"
    prompt = (
        "You are Aulos, a classical listening-guide research agent.\n"
        f"Work: {work_title}\n"
        f"Composer: {composer or 'unknown'}\n\n"
        "Return ONLY a compact JSON object (no markdown) with bilingual Salon Codex fields:\n"
        "listening_thesis, work_introduction, width_points, depth_points,\n"
        "listening_map ({{label,cue}}), practice_notes, myths_and_caveats,\n"
        "and a nested object zh with the SAME fields in professional Classical-Chinese 导赏 prose "
        "(museum wall-text quality; no Chinglish; no raw English skill jargon; use terms like 奏鸣曲/变奏/对位/羽管键琴 appropriately).\n"
        "Optional: related_works, interpretations.\n"
        "Rules: ear-actionable; label legends; no invented Discogs/YouTube IDs; keep JSON under 1200 words."
        "\nCRITICAL: the zh object is required — omit neither English nor Chinese layers."
    )
    try:
        live = await chat_with_ops_llm(db=db, message=prompt, timeout=90.0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("llm_dossier_failed work=%s err=%s", work_title, exc)
        return None, None, "skills"
    if live is None:
        return None, None, "skills"
    text, provider = live
    try:
        from aulos_skills.salon_codex import parse_llm_dossier_json
    except ImportError:
        return None, text[:400], f"skills+{provider}"
    dossier = parse_llm_dossier_json(text)
    note = None if dossier else text[:400]
    return (dossier or None), note, f"skills+{provider}"


async def _optional_llm_note(db: Session, work_title: str) -> tuple[str | None, str]:
    cfg = load_llm_config(db)
    if not cfg.ready_for_live:
        return None, "skills"
    prompt = (
        "You are Aulos, a classical-music research agent. "
        f"Give a compact enrichment note (max 80 words) for listening to: {work_title}."
    )
    try:
        live = await chat_with_ops_llm(db=db, message=prompt, timeout=45.0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("llm_note_failed work=%s err=%s", work_title, exc)
        return None, "skills"
    if live is None:
        return None, "skills"
    text, provider = live
    return text, f"skills+{provider}"


def _apply_report_to_row(row: ListeningGuide, *, report: Any, source: str) -> ListeningGuide:
    steps = [s.to_workflow_dict() for s in report.steps]
    row.work_title = report.work_title
    row.composer = report.composer
    row.status = "completed"
    row.source = source
    row.summary = report.summary
    row.guide_html = report.guide_html
    row.steps_json = json.dumps(steps)
    row.research_json = json.dumps(_research_payload(report), ensure_ascii=False)
    row.skill_versions_json = json.dumps(report.skill_versions)
    return row


def _persist_report(
    *,
    db: Session,
    user_id: int,
    report: Any,
    source: str,
    existing: ListeningGuide | None = None,
) -> ListeningGuide:
    if existing is not None:
        row = _apply_report_to_row(existing, report=report, source=source)
        db.add(row)
    else:
        row = ListeningGuide(user_id=user_id)
        _apply_report_to_row(row, report=report, source=source)
        db.add(row)
    db.commit()
    db.refresh(row)
    try:
        upsert_from_report(db, report=report, guide_id=row.id, user_id=user_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("kb_index_failed guide=%s err=%s", row.id, exc)
    logger.info(
        "listening_guide_ok id=%s user=%s work=%s source=%s skills=%s recompose=%s",
        row.id,
        user_id,
        report.work_title,
        source,
        list(report.skill_versions.keys()),
        existing is not None,
    )
    return row


def _rag_context(db: Session, *, message: str, work_hint: str, composer: str, user_id: int) -> dict[str, Any]:
    try:
        return kb_retrieve(
            db,
            query=message,
            work_hint=work_hint,
            composer=composer,
            user_id=user_id,
            k=6,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("kb_retrieve_failed err=%s", exc)
        return {"rag_mode": "error", "hits": [], "kb_dossier": {}, "rag_hits": []}


async def _run_chain_core(
    *,
    db: Session,
    user_id: int,
    message: str,
    work_hint: str | None = None,
    on_step: Callable[[dict[str, Any]], None] | None = None,
    yield_steps: bool = False,
) -> AsyncIterator[dict[str, Any] | Any]:
    """Shared create/recompose chain. Yields step dicts when yield_steps, then SkillRunReport."""
    _ensure_aulos_skills_importable()
    from aulos_skills.runtime import SkillRunReport, SkillRuntime

    disabled = _load_disabled(db)
    runtime = SkillRuntime()
    intake = runtime.run_trigger(
        "listening.intake",
        {"raw_message": message, "work_hint": work_hint or ""},
        disabled_skill_ids=disabled,
    )
    work_guess = str(intake.outputs.get("work_title") or message[:80])
    composer_guess = str(intake.outputs.get("composer_guess") or "")
    rag = _rag_context(
        db,
        message=message,
        work_hint=work_hint or work_guess,
        composer=composer_guess,
        user_id=user_id,
    )
    llm_dossier, enrichment, source = await _optional_llm_dossier(db, work_guess, composer_guess)
    if llm_dossier is None and enrichment is None:
        enrichment, source = await _optional_llm_note(db, work_guess)

    report: SkillRunReport | None = None
    for item in runtime.iter_listening_chain(
        message=message,
        work_hint=work_hint,
        llm_enrichment=enrichment,
        llm_dossier=llm_dossier,
        kb_dossier=dict(rag.get("kb_dossier") or {}),
        rag_hits=list(rag.get("rag_hits") or []),
        rag_mode=str(rag.get("rag_mode") or ""),
        disabled_skill_ids=disabled,
    ):
        if isinstance(item, SkillRunReport):
            report = item
        else:
            step = item.to_workflow_dict()
            if on_step is not None:
                on_step(step)
            if yield_steps:
                yield {"event": "step", "data": step}

    assert report is not None
    if source != "skills":
        report.source = source
    report.context["rag_mode"] = rag.get("rag_mode")
    report.context["rag_hits"] = rag.get("rag_hits") or []
    yield report


async def run_listening_guide_workflow(
    *,
    db: Session,
    user_id: int,
    message: str,
    work_hint: str | None = None,
    on_step: Callable[[dict[str, Any]], None] | None = None,
) -> ListeningGuide:
    report: Any = None
    async for item in _run_chain_core(
        db=db,
        user_id=user_id,
        message=message,
        work_hint=work_hint,
        on_step=on_step,
        yield_steps=False,
    ):
        report = item
    assert report is not None
    return _persist_report(db=db, user_id=user_id, report=report, source=report.source)


async def iter_listening_guide_events(
    *,
    db: Session,
    user_id: int,
    message: str,
    work_hint: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    try:
        report: Any = None
        async for item in _run_chain_core(
            db=db,
            user_id=user_id,
            message=message,
            work_hint=work_hint,
            yield_steps=True,
        ):
            if isinstance(item, dict) and item.get("event") == "step":
                yield item
            else:
                report = item
        assert report is not None
        row = _persist_report(db=db, user_id=user_id, report=report, source=report.source)
        yield {"event": "done", "data": guide_to_dict(row)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("listening_guide_stream_failed")
        yield {"event": "error", "data": {"detail": str(exc)}}


async def iter_recompose_events(
    *,
    db: Session,
    user_id: int,
    guide_id: int,
    message: str | None = None,
    work_hint: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Re-run chain into an existing guide row; preserve share_slug / published_at."""
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        yield {"event": "error", "data": {"detail": "Guide not found"}}
        return
    text = (message or "").strip() or f"Listening guide for {row.work_title}"
    hint = (work_hint or "").strip() or row.work_title
    try:
        report: Any = None
        async for item in _run_chain_core(
            db=db,
            user_id=user_id,
            message=text,
            work_hint=hint,
            yield_steps=True,
        ):
            if isinstance(item, dict) and item.get("event") == "step":
                yield item
            else:
                report = item
        assert report is not None
        updated = _persist_report(
            db=db,
            user_id=user_id,
            report=report,
            source=report.source,
            existing=row,
        )
        yield {"event": "done", "data": guide_to_dict(updated)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("listening_guide_recompose_failed id=%s", guide_id)
        yield {"event": "error", "data": {"detail": str(exc)}}


def guide_to_dict(row: ListeningGuide) -> dict:
    try:
        steps = json.loads(row.steps_json or "[]")
    except json.JSONDecodeError:
        steps = []
    try:
        skill_versions = json.loads(row.skill_versions_json or "{}")
    except json.JSONDecodeError:
        skill_versions = {}
    try:
        research = json.loads(row.research_json or "{}")
    except json.JSONDecodeError:
        research = {}
    published = bool(row.share_slug and row.published_at)
    html = row.guide_html or ""
    html = html.replace('loading="lazy"', 'loading="eager"')
    return {
        "id": row.id,
        "work_title": row.work_title,
        "composer": row.composer,
        "status": row.status,
        "source": row.source,
        "summary": row.summary,
        "guide_html": html,
        "steps": steps,
        "skill_versions": skill_versions,
        "eval_pass": research.get("eval_pass"),
        "eval_score": research.get("eval_score"),
        "created_at": _iso(row.created_at),
        "published": published,
        "share_slug": row.share_slug if published else None,
        "share_path": f"/g/{row.share_slug}" if published and row.share_slug else None,
        "published_at": _iso(row.published_at) if published else None,
    }


def get_owned_guide(db: Session, *, user_id: int, guide_id: int) -> ListeningGuide | None:
    return (
        db.query(ListeningGuide)
        .filter(ListeningGuide.id == guide_id, ListeningGuide.user_id == user_id)
        .one_or_none()
    )


def get_owned_guide_by_share_slug(db: Session, *, user_id: int, slug: str) -> ListeningGuide | None:
    slug = (slug or "").strip()
    if not slug:
        return None
    return (
        db.query(ListeningGuide)
        .filter(
            ListeningGuide.share_slug == slug,
            ListeningGuide.user_id == user_id,
        )
        .one_or_none()
    )


def publish_guide(db: Session, *, user_id: int, guide_id: int) -> ListeningGuide | None:
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    if not row.share_slug:
        for _ in range(8):
            candidate = _new_share_slug()
            exists = (
                db.query(ListeningGuide.id)
                .filter(ListeningGuide.share_slug == candidate)
                .one_or_none()
            )
            if exists is None:
                row.share_slug = candidate
                break
        else:
            row.share_slug = secrets.token_hex(12)
    row.published_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("listening_guide_published id=%s slug=%s", row.id, row.share_slug)
    return row


def unpublish_guide(db: Session, *, user_id: int, guide_id: int) -> ListeningGuide | None:
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    row.published_at = None
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("listening_guide_unpublished id=%s", row.id)
    return row


def update_publish_guide(db: Session, *, user_id: int, guide_id: int) -> ListeningGuide | None:
    """Ensure guide is published (same slug). Content already live if published."""
    return publish_guide(db, user_id=user_id, guide_id=guide_id)


def get_published_guide_by_slug(db: Session, slug: str) -> ListeningGuide | None:
    slug = (slug or "").strip()
    if not slug:
        return None
    return (
        db.query(ListeningGuide)
        .filter(
            ListeningGuide.share_slug == slug,
            ListeningGuide.published_at.isnot(None),
        )
        .one_or_none()
    )
