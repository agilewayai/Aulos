"""Transactional mail message queue — Redis list + background worker.

Mirrors the DB-sync queue pattern (ADR-007): LPUSH jobs, BRPOP worker.
Fake provider stays synchronous so offline tests keep an immediate mailbox.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("aulos_api.mail_queue")

MAIL_QUEUE_KEY = "aulos:mail:queue"

_lock = threading.RLock()
_stop = threading.Event()
_worker_started = False
_worker_thread: threading.Thread | None = None
_last_delivery: dict[str, Any] = {
    "status": "never",
    "at": None,
    "error": "",
    "kind": "",
    "to": "",
    "via": "",
}


def _redis_url() -> str:
    from aulos_api.config import get_settings

    settings = get_settings()
    return (settings.mail_queue_redis_url or settings.redis_url or "").strip()


def queue_status() -> dict[str, Any]:
    from aulos_api.config import get_settings

    settings = get_settings()
    depth = None
    url = _redis_url()
    if url:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
            depth = int(r.llen(MAIL_QUEUE_KEY))
        except Exception as exc:  # noqa: BLE001
            logger.warning("mail_queue_depth_fail err=%s", exc)
    with _lock:
        last = dict(_last_delivery)
    return {
        "enabled": bool(settings.mail_queue_enabled),
        "queue": MAIL_QUEUE_KEY,
        "redis_url_set": bool(url),
        "depth": depth,
        "worker_started": _worker_started,
        "last_delivery": last,
    }


def enqueue_mail_job(
    *,
    kind: str,
    to_email: str,
    subject: str,
    text: str,
    html: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Push a mail job onto Redis. On failure, deliver in a daemon thread."""
    job = {
        "kind": kind,
        "to_email": to_email,
        "subject": subject,
        "text": text,
        "html": html or "",
        "extra": extra or {},
        "enqueued_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    url = _redis_url()
    if url:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
            payload = json.dumps(job, ensure_ascii=False)
            r.lpush(MAIL_QUEUE_KEY, payload)
            depth = r.llen(MAIL_QUEUE_KEY)
            logger.info(
                "mail_enqueued kind=%s to=%s depth=%s",
                kind,
                to_email,
                depth,
            )
            return {"queued": True, "queue": MAIL_QUEUE_KEY, "depth": depth, "kind": kind}
        except Exception as exc:  # noqa: BLE001
            logger.warning("mail_redis_enqueue_failed falling_back_thread err=%s", exc)

    threading.Thread(
        target=_deliver_job_safe,
        args=(job,),
        name=f"aulos-mail-{kind}",
        daemon=True,
    ).start()
    logger.info("mail_thread_fallback kind=%s to=%s", kind, to_email)
    return {"queued": True, "queue": "thread", "depth": None, "kind": kind}


def _deliver_job_safe(job: dict[str, Any]) -> None:
    try:
        deliver_mail_job(job)
    except Exception as exc:  # noqa: BLE001
        logger.exception("mail_job_failed kind=%s err=%s", job.get("kind"), exc)
        with _lock:
            _last_delivery.update(
                {
                    "status": "error",
                    "error": str(exc)[:500],
                    "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "kind": str(job.get("kind") or ""),
                    "to": str(job.get("to_email") or ""),
                    "via": "worker",
                }
            )


def deliver_mail_job(job: dict[str, Any]) -> dict[str, Any]:
    """Open a fresh DB session and send one queued message."""
    from aulos_api.db import session as db_session
    from aulos_api.services.mailgun import deliver_message

    db_session.get_engine()
    if db_session.SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized")
    db = db_session.SessionLocal()
    try:
        result = deliver_message(
            db=db,
            to_email=str(job.get("to_email") or ""),
            subject=str(job.get("subject") or ""),
            text=str(job.get("text") or ""),
            html=str(job.get("html") or "") or None,
            kind=str(job.get("kind") or "queued"),
            extra=job.get("extra") if isinstance(job.get("extra"), dict) else None,
        )
        with _lock:
            _last_delivery.update(
                {
                    "status": "ok",
                    "error": "",
                    "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "kind": str(job.get("kind") or ""),
                    "to": str(job.get("to_email") or ""),
                    "via": "queue",
                }
            )
        return result
    finally:
        db.close()


def _worker_loop() -> None:
    url = _redis_url()
    r = None
    if url:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
            logger.info("mail_worker_redis_ok queue=%s", MAIL_QUEUE_KEY)
        except Exception as exc:  # noqa: BLE001
            logger.warning("mail_worker_redis_unavailable err=%s", exc)
            r = None

    while not _stop.is_set():
        if r is None:
            _stop.wait(2.0)
            url = _redis_url()
            if url:
                try:
                    import redis

                    r = redis.Redis.from_url(url, decode_responses=True)
                except Exception:
                    r = None
            continue
        try:
            item = r.brpop(MAIL_QUEUE_KEY, timeout=1)
            if not item:
                continue
            _, raw = item
            try:
                job = json.loads(raw)
            except json.JSONDecodeError:
                logger.error("mail_job_bad_json raw=%s", str(raw)[:200])
                continue
            if not isinstance(job, dict):
                logger.error("mail_job_bad_shape")
                continue
            _deliver_job_safe(job)
        except Exception as exc:  # noqa: BLE001
            logger.warning("mail_worker_brpop_err err=%s", exc)
            time.sleep(2)


def start_mail_worker() -> None:
    global _worker_started, _worker_thread
    from aulos_api.config import get_settings

    if not get_settings().mail_queue_enabled:
        logger.info("mail_worker_skip disabled")
        return
    with _lock:
        if _worker_started:
            return
        _stop.clear()
        _worker_started = True
        t = threading.Thread(target=_worker_loop, name="aulos-mail-queue", daemon=True)
        _worker_thread = t
    t.start()
    logger.info("mail_worker_started queue=%s", MAIL_QUEUE_KEY)


def stop_mail_worker() -> None:
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


def reset_mail_worker_for_tests() -> None:
    stop_mail_worker()
