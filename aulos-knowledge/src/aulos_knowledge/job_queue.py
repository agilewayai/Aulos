"""Async fetch-job dispatch — META-001 §3.3 / REQ-008 crawl jobs.

HTTP enqueues durable ``fetch_jobs`` rows; a background thread runs connectors
when ``AULOS_KNOWLEDGE_SYNC_JOBS=false``. Sync mode remains the CI/dev escape hatch.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.config import get_settings
from aulos_knowledge.db import FetchJob
from aulos_knowledge.jobs import enqueue_job, run_job

logger = logging.getLogger("aulos_knowledge.job_queue")

_drain_stop = threading.Event()
_drain_thread: threading.Thread | None = None
_dispatch_lock = threading.Lock()
_inflight: set[int] = set()


def dispatch_job(job_id: int) -> None:
    """Run one fetch job on a daemon thread (non-blocking HTTP)."""
    with _dispatch_lock:
        if job_id in _inflight:
            return
        _inflight.add(job_id)
    t = threading.Thread(
        target=_run_job_thread,
        args=(job_id,),
        name=f"aulos-kb-job-{job_id}",
        daemon=True,
    )
    t.start()
    logger.info("job_dispatched id=%s", job_id)


def enqueue_and_maybe_run(
    db: Session,
    *,
    source_id: str,
    params: dict[str, Any] | None = None,
    sync: bool | None = None,
) -> FetchJob:
    """Enqueue crawl job; run inline when sync, else background dispatch."""
    settings = get_settings()
    run_sync = settings.sync_jobs if sync is None else sync
    job = enqueue_job(db, source_id=source_id, params=params)
    if run_sync:
        return run_job(db, job.id)
    dispatch_job(job.id)
    db.refresh(job)
    return job


def _run_job_thread(job_id: int) -> None:
    from aulos_knowledge.db import SessionLocal

    try:
        if SessionLocal is None:
            logger.error("job_thread_no_db id=%s", job_id)
            return
        db = SessionLocal()
        try:
            run_job(db, job_id)
            logger.info("job_thread_done id=%s", job_id)
        except Exception:  # noqa: BLE001
            logger.exception("job_thread_failed id=%s", job_id)
        finally:
            db.close()
    finally:
        with _dispatch_lock:
            _inflight.discard(job_id)


def drain_queued_jobs(db: Session, *, limit: int = 8) -> list[int]:
    """Pick up orphaned ``queued`` jobs (e.g. after process restart)."""
    rows = (
        db.query(FetchJob)
        .filter(FetchJob.status == "queued")
        .order_by(FetchJob.id.asc())
        .limit(max(1, min(limit, 32)))
        .all()
    )
    ids: list[int] = []
    for row in rows:
        with _dispatch_lock:
            if row.id in _inflight:
                continue
        dispatch_job(row.id)
        ids.append(row.id)
    return ids


def start_job_drain_loop(*, interval_sec: float = 2.0) -> None:
    """Background loop: dispatch stuck queued jobs while async mode is on."""
    global _drain_thread
    if get_settings().sync_jobs:
        logger.info("job_drain_skip sync_jobs=true")
        return
    if _drain_thread and _drain_thread.is_alive():
        return
    _drain_stop.clear()

    def _loop() -> None:
        from aulos_knowledge.db import SessionLocal

        logger.info("job_drain_started interval=%s", interval_sec)
        while not _drain_stop.is_set():
            try:
                if SessionLocal is None:
                    time.sleep(interval_sec)
                    continue
                db = SessionLocal()
                try:
                    drain_queued_jobs(db)
                finally:
                    db.close()
            except Exception:  # noqa: BLE001
                logger.exception("job_drain_tick_failed")
            _drain_stop.wait(interval_sec)
        logger.info("job_drain_stopped")

    _drain_thread = threading.Thread(target=_loop, name="aulos-kb-job-drain", daemon=True)
    _drain_thread.start()


def stop_job_drain_loop() -> None:
    _drain_stop.set()
