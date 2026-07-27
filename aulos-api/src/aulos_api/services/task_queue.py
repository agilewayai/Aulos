"""Unified Ops background task queue — Redis + durable ops_tasks rows (SPEC-018)."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from aulos_api.db.models import OpsTask, utcnow

logger = logging.getLogger("aulos_api.task_queue")

OPS_TASK_QUEUE_KEY = "aulos:ops:tasks:queue"

TASK_DEV_BLOG_GENERATE = "dev_blog.generate"
SOURCE_OPS_DEV_BLOG = "ops.dev_blog"

_lock = threading.RLock()
_stop = threading.Event()
_worker_started = False
_worker_thread: threading.Thread | None = None

TaskHandler = Callable[[dict[str, Any]], dict[str, Any]]


def _redis_url() -> str:
    from aulos_api.config import get_settings

    return (get_settings().redis_url or "").strip()


def _handlers() -> dict[str, TaskHandler]:
    return {
        TASK_DEV_BLOG_GENERATE: _handle_dev_blog_generate,
    }


def queue_status() -> dict[str, Any]:
    from aulos_api.config import get_settings

    settings = get_settings()
    depth = None
    url = _redis_url()
    if url:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
            depth = int(r.llen(OPS_TASK_QUEUE_KEY))
        except Exception as exc:  # noqa: BLE001
            logger.warning("task_queue_depth_fail err=%s", exc)
    return {
        "enabled": bool(settings.task_queue_enabled),
        "sync_mode": bool(settings.task_queue_sync),
        "queue": OPS_TASK_QUEUE_KEY,
        "redis_url_set": bool(url),
        "depth": depth,
        "worker_started": _worker_started,
        "task_types": sorted(_handlers().keys()),
    }


def task_to_dict(row: OpsTask) -> dict[str, Any]:
    from aulos_api.timefmt import to_utc_iso

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
        "task_type": row.task_type,
        "source": row.source,
        "status": row.status,
        "payload": payload,
        "result": result,
        "error_detail": row.error_detail or "",
        "created_by_user_id": row.created_by_user_id,
        "created_at": to_utc_iso(row.created_at),
        "started_at": to_utc_iso(row.started_at) if row.started_at else None,
        "finished_at": to_utc_iso(row.finished_at) if row.finished_at else None,
    }


def list_tasks(
    db: Session,
    *,
    status: str | None = None,
    task_type: str | None = None,
    source: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    q = db.query(OpsTask)
    if status:
        q = q.filter(OpsTask.status == status.strip())
    if task_type:
        q = q.filter(OpsTask.task_type == task_type.strip())
    if source:
        q = q.filter(OpsTask.source == source.strip())
    rows = q.order_by(OpsTask.created_at.desc(), OpsTask.id.desc()).limit(max(1, min(limit, 200))).all()
    return [task_to_dict(r) for r in rows]


def get_task(db: Session, task_id: int) -> OpsTask | None:
    if task_id < 1:
        return None
    return db.query(OpsTask).filter(OpsTask.id == task_id).one_or_none()


def dashboard(db: Session) -> dict[str, Any]:
    from aulos_api.db.models import ListeningGuide
    from aulos_api.services.listening_queue import queue_status as listening_queue_status
    from aulos_api.services.mail_queue import queue_status as mail_queue_status

    mail = mail_queue_status()
    listening = listening_queue_status()
    ops = queue_status()

    listening_active = (
        db.query(ListeningGuide)
        .filter(ListeningGuide.status.in_(("queued", "running")))
        .count()
    )

    recent = list_tasks(db, limit=30)
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for row in db.query(OpsTask).all():
        by_status[row.status] = by_status.get(row.status, 0) + 1
        by_type[row.task_type] = by_type.get(row.task_type, 0) + 1

    return {
        "queues": [
            {
                "source": "mail",
                "task_type": "mail.send",
                "label": "Mail",
                "depth": mail.get("depth"),
                "worker_started": mail.get("worker_started"),
                "enabled": mail.get("enabled"),
                "queue": mail.get("queue"),
            },
            {
                "source": "listening",
                "task_type": "listening.guide",
                "label": "Listening guides",
                "depth": listening.get("depth"),
                "worker_started": listening.get("worker_started"),
                "active_jobs": listening_active,
                "queue": listening.get("queue"),
            },
            {
                "source": "ops",
                "task_type": "ops.*",
                "label": "Ops tasks",
                "depth": ops.get("depth"),
                "worker_started": ops.get("worker_started"),
                "enabled": ops.get("enabled"),
                "queue": ops.get("queue"),
                "task_types": ops.get("task_types"),
            },
        ],
        "recent_tasks": recent,
        "counts_by_status": by_status,
        "counts_by_type": by_type,
    }


def enqueue_task(
    db: Session,
    *,
    task_type: str,
    source: str,
    payload: dict[str, Any],
    created_by_user_id: int | None = None,
) -> OpsTask:
    from aulos_api.config import get_settings

    settings = get_settings()
    if task_type not in _handlers():
        raise ValueError(f"unknown task_type: {task_type}")

    row = OpsTask(
        task_type=task_type,
        source=source,
        status="queued",
        payload_json=json.dumps(payload, ensure_ascii=False),
        result_json="{}",
        created_by_user_id=created_by_user_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    if not settings.task_queue_enabled or settings.task_queue_sync:
        _run_task_by_id(row.id)
        db.refresh(row)
        return row

    job = {"task_id": row.id}
    url = _redis_url()
    if url:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
            r.lpush(OPS_TASK_QUEUE_KEY, json.dumps(job))
            logger.info("task_enqueued id=%s type=%s source=%s", row.id, task_type, source)
            return row
        except Exception as exc:  # noqa: BLE001
            logger.warning("task_redis_enqueue_failed id=%s err=%s", row.id, exc)

    threading.Thread(
        target=_run_task_by_id,
        args=(row.id,),
        name=f"aulos-task-{row.id}",
        daemon=True,
    ).start()
    return row


def _handle_dev_blog_generate(payload: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from aulos_api.config import get_settings
    from aulos_api.db import session as db_session
    from aulos_api.services import dev_blog as blog

    day = str(payload.get("day") or "")
    post_id = payload.get("post_id")
    force = bool(payload.get("force"))

    async def _run() -> dict[str, Any]:
        db = db_session.SessionLocal()
        try:
            root = None
            raw_root = (get_settings().repo_root or "").strip()
            if raw_root:
                root = Path(raw_root)
            if force and post_id is not None:
                row = await blog.generate_post(db, day, post_id=int(post_id), repo_root=root)
            elif force:
                row = await blog.generate_or_load(db, day, force=True, repo_root=root)
            else:
                row = await blog.generate_post(db, day, repo_root=root)
            return {"post_id": row.id, "day": row.day, "title": row.title, "provider": row.provider}
        finally:
            db.close()

    return asyncio.run(_run())


def _run_task_by_id(task_id: int) -> None:
    from aulos_api.db import session as db_session

    db_session.get_engine()
    if db_session.SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized")
    db = db_session.SessionLocal()
    try:
        row = get_task(db, task_id)
        if row is None:
            logger.error("task_missing id=%s", task_id)
            return
        if row.status in ("completed", "failed"):
            return
        handlers = _handlers()
        handler = handlers.get(row.task_type)
        if handler is None:
            row.status = "failed"
            row.error_detail = f"no handler for {row.task_type}"
            row.finished_at = utcnow()
            db.commit()
            return
        row.status = "running"
        row.started_at = utcnow()
        row.error_detail = ""
        db.commit()
        try:
            payload = json.loads(row.payload_json or "{}")
            if not isinstance(payload, dict):
                payload = {}
            result = handler(payload)
            row.status = "completed"
            row.result_json = json.dumps(result, ensure_ascii=False)
            row.finished_at = utcnow()
            db.commit()
            logger.info("task_done id=%s type=%s", task_id, row.task_type)
        except Exception as exc:  # noqa: BLE001
            logger.exception("task_failed id=%s err=%s", task_id, exc)
            row.status = "failed"
            row.error_detail = str(exc)[:2000]
            row.finished_at = utcnow()
            db.commit()
    finally:
        db.close()


def _worker_loop() -> None:
    url = _redis_url()
    r = None
    if url:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
            logger.info("task_worker_redis_ok queue=%s", OPS_TASK_QUEUE_KEY)
        except Exception as exc:  # noqa: BLE001
            logger.warning("task_worker_redis_unavailable err=%s", exc)
            r = None

    while not _stop.is_set():
        if r is None:
            _stop.wait(2.0)
            continue
        try:
            item = r.brpop(OPS_TASK_QUEUE_KEY, timeout=1)
            if not item:
                continue
            _, raw = item
            job = json.loads(raw)
            task_id = int(job.get("task_id") or 0)
            if task_id < 1:
                continue
            _run_task_by_id(task_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("task_worker_err err=%s", exc)
            time.sleep(2)


def start_task_worker() -> None:
    global _worker_started, _worker_thread
    from aulos_api.config import get_settings

    if not get_settings().task_queue_enabled or get_settings().task_queue_sync:
        logger.info("task_worker_skip sync_or_disabled")
        return
    with _lock:
        if _worker_started:
            return
        _stop.clear()
        _worker_started = True
        t = threading.Thread(target=_worker_loop, name="aulos-ops-task-queue", daemon=True)
        _worker_thread = t
    t.start()
    logger.info("task_worker_started queue=%s", OPS_TASK_QUEUE_KEY)


def stop_task_worker() -> None:
    global _worker_started, _worker_thread
    with _lock:
        if not _worker_started:
            return
        _stop.set()
        t = _worker_thread
    if t is not None and t.is_alive():
        t.join(timeout=5.0)
    with _lock:
        _worker_started = False
        _worker_thread = None
        _stop.clear()


def reset_task_worker_for_tests() -> None:
    stop_task_worker()
