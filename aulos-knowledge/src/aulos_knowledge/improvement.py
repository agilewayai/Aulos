"""KB-IMPROVE-001 — Execute improvement actions from diagnosis."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.benchmark import execute_benchmark_run, get_benchmark_run
from aulos_knowledge.benchmark_queue import enqueue_and_maybe_run
from aulos_knowledge.config import get_settings
from aulos_knowledge.db import BenchmarkDiagnosis, BenchmarkRun, ImprovementAction, utcnow
from aulos_knowledge.diagnosis import diagnose_benchmark_run, get_diagnosis_for_run
from aulos_knowledge.jobs import enqueue_and_maybe_run as enqueue_fetch_job

logger = logging.getLogger("aulos_knowledge.improvement")


def _action_row(db: Session, action_id: int) -> ImprovementAction:
    row = db.get(ImprovementAction, action_id)
    if not row:
        raise ValueError(f"improvement action not found: {action_id}")
    return row


def execute_improvement_action(db: Session, action_id: int, *, sync: bool | None = None) -> dict[str, Any]:
    """Run one improvement action; update status + result."""
    settings = get_settings()
    run_sync = settings.sync_jobs if sync is None else sync
    row = _action_row(db, action_id)
    if row.status in ("succeeded", "skipped"):
        return _action_dict(row)

    try:
        payload = json.loads(row.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}

    row.status = "running"
    row.error = ""
    db.commit()

    try:
        result = _dispatch_action(db, row.action_type, payload, sync=run_sync)
        row.status = "succeeded"
        row.result_json = json.dumps(result, ensure_ascii=False)
        row.executed_at = utcnow()
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("improvement_action_failed id=%s", action_id)
        row.status = "failed"
        row.error = str(exc)[:2000]
        row.executed_at = utcnow()
        db.commit()
        raise

    db.refresh(row)
    return _action_dict(row)


def _dispatch_action(
    db: Session,
    action_type: str,
    payload: dict[str, Any],
    *,
    sync: bool,
) -> dict[str, Any]:
    if action_type == "crawl_source":
        source_id = str(payload.get("source_id") or "")
        params = dict(payload.get("params") or {})
        job = enqueue_fetch_job(db, source_id=source_id, params=params, sync=sync)
        return {"job_id": job.id, "source_id": source_id, "status": job.status}

    if action_type == "crawl_authority_bundle":
        composer_id = str(payload.get("composer_id") or "")
        results: list[dict[str, Any]] = []
        if payload.get("wikidata_qid"):
            job = enqueue_fetch_job(
                db,
                source_id="wikidata",
                params={"qids": [payload["wikidata_qid"]], "composer_id": composer_id},
                sync=sync,
            )
            results.append({"source_id": "wikidata", "job_id": job.id, "status": job.status})
        if payload.get("wikipedia_title"):
            job = enqueue_fetch_job(
                db,
                source_id="wikipedia",
                params={
                    "title": payload["wikipedia_title"],
                    "langs": ["en", "zh"],
                    "composer_id": composer_id,
                },
                sync=sync,
            )
            results.append({"source_id": "wikipedia", "job_id": job.id, "status": job.status})
        return {"bundle": results}

    if action_type == "explore_sources":
        from aulos_knowledge.source_discovery import discovery_run_dict, execute_discovery_run

        row = execute_discovery_run(
            db,
            composer_id=str(payload.get("composer_id") or ""),
            wikidata_qid=str(payload.get("wikidata_qid") or "").upper(),
            wikipedia_title=str(payload.get("wikipedia_title") or ""),
            max_depth=int(payload.get("max_depth") or 2),
            max_breadth=int(payload.get("max_breadth") or 24),
            trigger="improve",
            enqueue_crawl=bool(payload.get("enqueue_crawl", True)),
            sync=sync,
        )
        return discovery_run_dict(row)

    if action_type in {"engineering_task", "verify_sources", "review_quarantine", "inspect_jobs"}:
        return {"acknowledged": True, "action_type": action_type, "manual": True}

    raise ValueError(f"unsupported action_type: {action_type}")


def _action_dict(row: ImprovementAction) -> dict[str, Any]:
    try:
        payload = json.loads(row.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    try:
        result = json.loads(row.result_json or "{}")
    except json.JSONDecodeError:
        result = {}
    return {
        "id": row.id,
        "diagnosis_id": row.diagnosis_id,
        "item_id": row.item_id,
        "action_type": row.action_type,
        "layer": row.layer,
        "auto_safe": row.auto_safe,
        "status": row.status,
        "payload": payload,
        "result": result,
        "error": row.error or "",
        "executed_at": row.executed_at.isoformat() if row.executed_at else None,
    }


def execute_safe_actions(db: Session, diagnosis_id: int, *, sync: bool | None = None) -> list[dict[str, Any]]:
    rows = (
        db.query(ImprovementAction)
        .filter(
            ImprovementAction.diagnosis_id == diagnosis_id,
            ImprovementAction.auto_safe.is_(True),
            ImprovementAction.status == "proposed",
        )
        .order_by(ImprovementAction.id.asc())
        .all()
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            out.append(execute_improvement_action(db, row.id, sync=sync))
        except Exception as exc:  # noqa: BLE001
            out.append({**_action_dict(row), "error": str(exc)})
    return out


def run_improvement_cycle(
    db: Session,
    *,
    benchmark_run_id: int | None = None,
    trigger: str = "ops-improve",
    sync: bool | None = None,
) -> dict[str, Any]:
    """Diagnose → execute safe L1 actions → re-benchmark → return delta."""
    settings = get_settings()
    run_sync = settings.sync_jobs if sync is None else sync

    if benchmark_run_id is None:
        row = (
            db.query(BenchmarkRun)
            .filter(BenchmarkRun.status == "succeeded")
            .order_by(BenchmarkRun.id.desc())
            .first()
        )
        if not row:
            raise ValueError("no succeeded benchmark run to improve from")
        benchmark_run_id = row.id

    diagnosis = diagnose_benchmark_run(db, benchmark_run_id)
    diagnosis_id = int(diagnosis["diagnosis_id"])
    executed = execute_safe_actions(db, diagnosis_id, sync=run_sync)

    before = get_benchmark_run(db, benchmark_run_id) or {}
    before_score = float(before.get("overall_score") or 0)

    bench_row = enqueue_and_maybe_run(db, trigger=trigger, sync=run_sync)
    if run_sync:
        after_report = get_benchmark_run(db, bench_row.id) or {}
    else:
        after_report = {"id": bench_row.id, "status": bench_row.status}

    after_run_id = int(after_report.get("id") or bench_row.id)
    after_score = float(after_report.get("overall_score") or 0) if after_report.get("status") == "succeeded" else None

    diag_row = db.get(BenchmarkDiagnosis, diagnosis_id)
    if diag_row and after_score is not None:
        improved = after_score >= before_score
        diag_row.status = "closed" if improved else "open"
        db.commit()

    return {
        "benchmark_run_id_before": benchmark_run_id,
        "benchmark_run_id_after": after_run_id,
        "diagnosis_id": diagnosis_id,
        "score_before": before_score,
        "score_after": after_score,
        "score_delta": round(after_score - before_score, 2) if after_score is not None else None,
        "actions_executed": executed,
        "diagnosis": get_diagnosis_for_run(db, benchmark_run_id),
        "async_rebench": not run_sync,
    }


def wait_for_benchmark_run(db: Session, run_id: int, *, timeout_sec: float = 120) -> dict[str, Any]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        report = get_benchmark_run(db, run_id)
        if not report:
            raise ValueError(f"benchmark run {run_id} not found")
        status = str(report.get("status") or "")
        if status == "succeeded":
            return report
        if status == "failed":
            raise RuntimeError(report.get("error") or f"benchmark run {run_id} failed")
        time.sleep(0.5)
    raise TimeoutError(f"benchmark run {run_id} timed out")
