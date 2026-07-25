"""Job runner — sync in-process for dev; ARQ hook later."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.connectors import run_connector
from aulos_knowledge.db import FetchJob, SourceAuthority, utcnow

logger = logging.getLogger("aulos_knowledge.jobs")


def enqueue_job(db: Session, *, source_id: str, params: dict[str, Any] | None = None) -> FetchJob:
    src = db.get(SourceAuthority, source_id)
    if src is None:
        raise ValueError(f"unknown source: {source_id}")
    if not src.enabled:
        raise ValueError(f"source disabled: {source_id}")
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
    if src is None or not src.enabled:
        job.status = "failed"
        job.error = "source missing or disabled"
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


def enqueue_and_maybe_run(db: Session, *, source_id: str, params: dict[str, Any] | None, sync: bool) -> FetchJob:
    job = enqueue_job(db, source_id=source_id, params=params)
    if sync:
        return run_job(db, job.id)
    return job
