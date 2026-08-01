"""Async benchmark dispatch — queued → running → succeeded|failed."""

from __future__ import annotations

import logging
import threading

from sqlalchemy.orm import Session

from aulos_knowledge.benchmark import execute_benchmark_run
from aulos_knowledge.config import get_settings
from aulos_knowledge.db import BenchmarkRun

logger = logging.getLogger("aulos_knowledge.benchmark_queue")


def enqueue_benchmark(db: Session, *, trigger: str = "ops") -> BenchmarkRun:
    row = BenchmarkRun(status="queued", trigger=trigger)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def dispatch_benchmark(run_id: int) -> None:
    """Run benchmark on a background thread (non-blocking HTTP)."""
    t = threading.Thread(
        target=_run_benchmark_thread,
        args=(run_id,),
        name=f"aulos-kb-benchmark-{run_id}",
        daemon=True,
    )
    t.start()
    logger.info("benchmark_dispatched id=%s", run_id)


def enqueue_and_maybe_run(db: Session, *, trigger: str = "ops", sync: bool | None = None) -> BenchmarkRun:
    settings = get_settings()
    run_sync = settings.sync_jobs if sync is None else sync
    row = enqueue_benchmark(db, trigger=trigger)
    if run_sync:
        execute_benchmark_run(db, row.id)
        db.refresh(row)
    else:
        dispatch_benchmark(row.id)
    return row


def _run_benchmark_thread(run_id: int) -> None:
    from aulos_knowledge.db import SessionLocal

    if SessionLocal is None:
        logger.error("benchmark_thread_no_db id=%s", run_id)
        return
    db = SessionLocal()
    try:
        execute_benchmark_run(db, run_id)
        logger.info("benchmark_thread_done id=%s", run_id)
    except Exception:  # noqa: BLE001
        logger.exception("benchmark_thread_failed id=%s", run_id)
    finally:
        db.close()
