"""Durable listening-guide job queue — Redis list + background worker (SPEC-013).

Mirrors mail_queue: LPUSH jobs, BRPOP worker; thread fallback when Redis is down
or the worker is not Redis-capable (e.g. started with empty URL in tests).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("aulos_api.listening_queue")

LISTENING_QUEUE_KEY = "aulos:listening:queue"

_lock = threading.RLock()
_stop = threading.Event()
_worker_started = False
_worker_redis_ok = False
_worker_thread: threading.Thread | None = None


def _redis_url() -> str:
    from aulos_api.config import get_settings

    settings = get_settings()
    return (settings.redis_url or "").strip()


def queue_status() -> dict[str, Any]:
    depth = None
    url = _redis_url()
    if url:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
            depth = int(r.llen(LISTENING_QUEUE_KEY))
        except Exception as exc:  # noqa: BLE001
            logger.warning("listening_queue_depth_fail err=%s", exc)
    return {
        "queue": LISTENING_QUEUE_KEY,
        "redis_url_set": bool(url),
        "depth": depth,
        "worker_started": _worker_started,
        "worker_redis_ok": _worker_redis_ok,
    }


def enqueue_listening_job(
    *,
    guide_id: int,
    user_id: int,
    kind: str = "compose",
    work_hint: str | None = None,
    review_notes: str | None = None,
) -> dict[str, Any]:
    """Push a listening job. Prefer Redis; fall back to a daemon thread."""
    job = {
        "guide_id": int(guide_id),
        "user_id": int(user_id),
        "kind": kind,
        "work_hint": (work_hint or "").strip() or None,
        "review_notes": (review_notes or "").strip() or None,
        "enqueued_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    url = _redis_url()
    if url and _worker_redis_ok:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
            payload = json.dumps(job, ensure_ascii=False)
            r.lpush(LISTENING_QUEUE_KEY, payload)
            depth = r.llen(LISTENING_QUEUE_KEY)
            logger.info(
                "listening_enqueued guide=%s kind=%s depth=%s",
                guide_id,
                kind,
                depth,
            )
            return {"queued": True, "queue": LISTENING_QUEUE_KEY, "depth": depth, "guide_id": guide_id}
        except Exception as exc:  # noqa: BLE001
            logger.warning("listening_redis_enqueue_failed falling_back_thread err=%s", exc)

    threading.Thread(
        target=_run_job_safe,
        args=(job,),
        name=f"aulos-listen-{guide_id}",
        daemon=True,
    ).start()
    logger.info("listening_thread_fallback guide=%s kind=%s", guide_id, kind)
    return {"queued": True, "queue": "thread", "depth": None, "guide_id": guide_id}


def _run_job_safe(job: dict[str, Any]) -> None:
    try:
        run_listening_job(job)
    except Exception as exc:  # noqa: BLE001
        logger.exception("listening_job_failed guide=%s err=%s", job.get("guide_id"), exc)
        _mark_failed(int(job.get("guide_id") or 0), str(exc))


def _mark_failed(guide_id: int, detail: str) -> None:
    if not guide_id:
        return
    from aulos_api.db import session as db_session
    from aulos_api.db.models import ListeningGuide
    from aulos_api.services.listening_guide import utcnow

    db_session.get_engine()
    if db_session.SessionLocal is None:
        return
    db = db_session.SessionLocal()
    try:
        row = db.query(ListeningGuide).filter(ListeningGuide.id == guide_id).one_or_none()
        if row is None:
            return
        row.status = "failed"
        row.error_detail = (detail or "job failed")[:2000]
        row.updated_at = utcnow()
        db.add(row)
        db.commit()
    finally:
        db.close()


def _persist_steps(db: Any, row: Any, step: dict[str, Any]) -> None:
    from aulos_api.services.listening_guide import utcnow
    from aulos_api.services.listening_plan import upsert_step

    try:
        steps = json.loads(row.steps_json or "[]")
        if not isinstance(steps, list):
            steps = []
    except json.JSONDecodeError:
        steps = []
    steps = upsert_step([s for s in steps if isinstance(s, dict)], step)
    row.steps_json = json.dumps(steps, ensure_ascii=False)
    row.updated_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)


def run_listening_job(job: dict[str, Any]) -> dict[str, Any]:
    """Open a fresh DB session and run one queued compose/recompose/targeted_revise."""
    from aulos_api.db import session as db_session
    from aulos_api.services.listening_guide import (
        _persist_report,
        _run_chain_core,
        get_owned_guide,
        utcnow,
    )

    guide_id = int(job.get("guide_id") or 0)
    user_id = int(job.get("user_id") or 0)
    kind = str(job.get("kind") or "compose")
    work_hint = job.get("work_hint") if isinstance(job.get("work_hint"), str) else None
    review_notes = job.get("review_notes") if isinstance(job.get("review_notes"), str) else None

    db_session.get_engine()
    if db_session.SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized")
    db = db_session.SessionLocal()
    try:
        row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
        if row is None:
            raise RuntimeError(f"guide {guide_id} not found for user {user_id}")

        row.status = "running"
        row.error_detail = ""
        row.updated_at = utcnow()
        try:
            existing = json.loads(row.steps_json or "[]")
        except json.JSONDecodeError:
            existing = []
        if not existing:
            from aulos_api.services.listening_plan import initial_plan_steps

            row.steps_json = json.dumps(initial_plan_steps(), ensure_ascii=False)
        db.add(row)
        db.commit()
        db.refresh(row)

        if kind == "targeted_revise":
            updated = _run_targeted_revise_job(
                db,
                row=row,
                review_notes=review_notes,
                work_hint=work_hint,
            )
            logger.info(
                "listening_job_ok guide=%s kind=%s status=%s",
                updated.id,
                kind,
                updated.status,
            )
            return {"guide_id": updated.id, "status": updated.status}

        message = (row.message or "").strip() or f"Listening guide for {row.work_title}"
        hint = (work_hint or "").strip() or (row.work_title if kind == "recompose" else None)

        def on_step(step: dict[str, Any]) -> None:
            _persist_steps(db, row, step)

        async def _run() -> Any:
            report: Any = None
            async for item in _run_chain_core(
                db=db,
                user_id=user_id,
                message=message,
                work_hint=hint,
                on_step=on_step,
                yield_steps=False,
            ):
                report = item
            return report

        report = asyncio.run(_run())
        if report is None:
            raise RuntimeError("listening chain produced no report")

        updated = _persist_report(
            db=db,
            user_id=user_id,
            report=report,
            source=report.source,
            existing=row,
        )
        logger.info(
            "listening_job_ok guide=%s kind=%s status=%s",
            updated.id,
            kind,
            updated.status,
        )
        return {"guide_id": updated.id, "status": updated.status}
    finally:
        db.close()


def _run_targeted_revise_job(
    db: Any,
    *,
    row: Any,
    review_notes: str | None,
    work_hint: str | None,
) -> Any:
    """Apply chamber-targeted revise using existing research snapshot."""
    import sys
    from pathlib import Path
    from types import SimpleNamespace

    from aulos_api.services.listening_guide import _persist_report, utcnow

    try:
        research = json.loads(row.research_json or "{}")
    except json.JSONDecodeError:
        research = {}
    if not isinstance(research, dict):
        research = {}

    notes = (review_notes or research.get("pending_review_notes") or "").strip()
    if not notes:
        raise RuntimeError("targeted_revise requires review_notes")

    # Polluted snapshot → escalate to full recompose (do not patch foreign chambers).
    try:
        from aulos_skills.identity_lock import dossier_betrays_identity_lock
        from aulos_api.services.knowledge_base import purge_betraying_knowledge

        dossier0 = dict(research.get("corpus_dossier") or {})
        if dossier0 and dossier_betrays_identity_lock(
            dossier0,
            work_title=row.work_title or "",
            raw_message=row.message or "",
        ):
            logger.warning(
                "targeted_revise_escalated_identity_pollution guide=%s", row.id
            )
            research["corpus_dossier"] = {}
            research["prior_corpus_cleared_for_recompose"] = True
            research.pop("pending_review_notes", None)
            row.research_json = json.dumps(research, ensure_ascii=False)
            row.updated_at = utcnow()
            db.add(row)
            db.commit()
            purge_betraying_knowledge(
                db,
                work_title=row.work_title or "",
                raw_message=row.message or "",
                composer=row.composer or "",
                source_guide_id=int(row.id),
            )
            # Inline recompose — do not re-enqueue (avoids double execution).
            return run_listening_job(
                {
                    "guide_id": int(row.id),
                    "user_id": int(row.user_id),
                    "kind": "recompose",
                    "work_hint": work_hint or row.work_title,
                }
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("targeted_revise_pollution_gate_failed guide=%s err=%s", row.id, exc)

    def _mark(step_id: str, title: str, status: str, detail: str = "") -> None:
        _persist_steps(
            db,
            row,
            {
                "id": step_id,
                "title": title,
                "status": status,
                "thinking": title,
                "detail": detail,
            },
        )

    _mark("targeted.locate", "Locate review targets", "running")

    skills = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
    if skills.is_dir() and str(skills) not in sys.path:
        sys.path.insert(0, str(skills))
    from aulos_skills.targeted_revise import run_targeted_revise

    dossier = dict(research.get("corpus_dossier") or {})
    rounds = dict(research.get("generation_rounds") or {})
    if row.guide_html and not (rounds.get("draft_v1") or {}).get("guide_html"):
        rounds["draft_v1"] = {
            "guide_html": row.guide_html,
            "summary": row.summary or research.get("summary") or "",
        }

    context: dict[str, Any] = {
        "raw_message": row.message or "",
        "work_title": row.work_title or research.get("work_title") or work_hint or "",
        "composer": row.composer or research.get("composer") or "",
        "guide_html": row.guide_html or "",
        "summary": row.summary or research.get("summary") or "",
        "corpus_dossier": dossier,
        "generation_rounds": rounds,
        "external_review_report": dict(research.get("external_review_report") or {}),
        "critique_corrections": list(research.get("critique_corrections") or []),
        "intent_lock": research.get("intent_lock"),
        "review_notes": notes,
    }
    _mark("targeted.locate", "Locate review targets", "done", f"notes={len(notes)}")
    _mark("targeted.patch", "Patch chambers", "running")
    result = run_targeted_revise(context, human_notes=notes, allow_full_compose=None)
    _mark(
        "targeted.patch",
        "Patch chambers",
        "done",
        f"scope={result.get('revise_scope')} targets={result.get('patched_targets')}",
    )
    _mark("targeted.render", "Re-render + score", "running")

    pct = float(
        (
            ((result.get("generation_rounds") or {}).get("draft_v2") or {})
            .get("process_scorecard")
            or {}
        )
        .get("rollup", {})
        .get("pct")
        or 0
    )
    report = SimpleNamespace(
        eval_pass=True,
        eval_score=int(round(pct / 10.0)),
        skill_versions=dict(research.get("skill_versions") or {}),
        work_title=str(result.get("work_title") or row.work_title or ""),
        composer=str(result.get("composer") or row.composer or ""),
        summary=str(result.get("summary") or ""),
        guide_html=str(result.get("guide_html") or ""),
        source="targeted-revise",
        context=context,
        steps=[],
    )
    updated = _persist_report(
        db=db,
        user_id=int(row.user_id),
        report=report,
        source="targeted-revise",
        existing=row,
    )
    try:
        research2 = json.loads(updated.research_json or "{}")
    except json.JSONDecodeError:
        research2 = {}
    if isinstance(research2, dict):
        research2.pop("pending_review_notes", None)
        research2["revise_mode"] = "targeted"
        updated.research_json = json.dumps(research2, ensure_ascii=False)
        updated.updated_at = utcnow()
        db.add(updated)
        db.commit()
        db.refresh(updated)
    _mark("targeted.render", "Re-render + score", "done")
    return updated


def _worker_loop() -> None:
    global _worker_redis_ok
    r = None
    while not _stop.is_set():
        if r is None:
            url = _redis_url()
            if url:
                try:
                    import redis

                    r = redis.Redis.from_url(url, decode_responses=True)
                    _worker_redis_ok = True
                    logger.info("listening_worker_redis_ok queue=%s", LISTENING_QUEUE_KEY)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("listening_worker_redis_unavailable err=%s", exc)
                    r = None
                    _worker_redis_ok = False
            else:
                _worker_redis_ok = False
            if r is None:
                time.sleep(1.0)
                continue
        try:
            item = r.brpop(LISTENING_QUEUE_KEY, timeout=2)
        except Exception as exc:  # noqa: BLE001
            logger.warning("listening_brpop_fail err=%s", exc)
            r = None
            _worker_redis_ok = False
            time.sleep(1.0)
            continue
        if not item:
            continue
        _, payload = item
        try:
            job = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("listening_job_bad_json")
            continue
        _run_job_safe(job)


def start_listening_worker() -> None:
    global _worker_started, _worker_thread
    with _lock:
        if _worker_started:
            return
        _stop.clear()
        t = threading.Thread(target=_worker_loop, name="aulos-listening-worker", daemon=True)
        _worker_thread = t
        _worker_started = True
    t.start()
    logger.info("listening_worker_started")


def stop_listening_worker() -> None:
    global _worker_started, _worker_redis_ok, _worker_thread
    with _lock:
        if not _worker_started:
            return
        _stop.set()
        t = _worker_thread
    if t is not None and t.is_alive():
        t.join(timeout=5.0)
    with _lock:
        _worker_started = False
        _worker_redis_ok = False
        _worker_thread = None
        _stop.clear()


def reset_listening_worker_for_tests() -> None:
    """Test helper: allow a fresh worker after settings/DB reset."""
    stop_listening_worker()
