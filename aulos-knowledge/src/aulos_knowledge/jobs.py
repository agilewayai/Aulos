"""Job runner — enqueue durable fetch_jobs; sync or async dispatch (META-001 §3.3)."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.connectors import connector_registered, run_connector
from aulos_knowledge.db import FetchJob, SourceAuthority, utcnow

logger = logging.getLogger("aulos_knowledge.jobs")


def assert_source_crawlable(src: SourceAuthority) -> None:
    status = (src.verification_status or "").strip() or "candidate"
    if status != "verified":
        raise ValueError(f"source not verified: {src.id} (status={status})")
    if not src.enabled:
        raise ValueError(f"source disabled: {src.id}")
    if not connector_registered(src.connector or ""):
        raise ValueError(f"connector not registered: {src.connector or '(empty)'} for source {src.id}")


def enqueue_job(db: Session, *, source_id: str, params: dict[str, Any] | None = None) -> FetchJob:
    src = db.get(SourceAuthority, source_id)
    if src is None:
        raise ValueError(f"unknown source: {source_id}")
    assert_source_crawlable(src)
    job = FetchJob(
        source_id=source_id,
        status="queued",
        params_json=json.dumps(params or {}, ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def run_job(db: Session, job_id: int) -> FetchJob:
    job = db.get(FetchJob, job_id)
    if job is None:
        raise ValueError(f"job not found: {job_id}")
    src = db.get(SourceAuthority, job.source_id)
    if src is None:
        job.status = "failed"
        job.error = "source missing"
        job.finished_at = utcnow()
        db.commit()
        return job
    try:
        assert_source_crawlable(src)
    except ValueError as exc:
        job.status = "failed"
        job.error = str(exc)
        job.finished_at = utcnow()
        db.commit()
        return job
    job.status = "running"
    job.started_at = utcnow()
    job.error = ""
    db.commit()
    try:
        params = json.loads(job.params_json or "{}")
        run_connector(db, source=src, job=job, params=params)
        job.status = "succeeded"
        job.finished_at = utcnow()
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("job_failed id=%s", job_id)
        job.status = "failed"
        job.error = str(exc)[:2000]
        job.finished_at = utcnow()
        db.commit()
    db.refresh(job)
    return job


def enqueue_and_maybe_run(
    db: Session,
    *,
    source_id: str,
    params: dict[str, Any] | None,
    sync: bool | None = None,
) -> FetchJob:
    """Compatibility entry — delegates to job_queue (async dispatch when not sync)."""
    from aulos_knowledge.job_queue import enqueue_and_maybe_run as _enqueue

    return _enqueue(db, source_id=source_id, params=params, sync=sync)
