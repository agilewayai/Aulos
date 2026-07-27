"""Business DB HA: Postgres primary + SQLite failover mirror."""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from aulos_api.config import get_settings
from aulos_api.db.session import Base

logger = logging.getLogger("aulos_api.db_ha")

_lock = threading.RLock()
_primary_engine: Engine | None = None
_failover_engine: Engine | None = None
_active_role: str = "primary"  # primary | failover
_last_sync: dict[str, Any] = {
    "status": "never",
    "at": None,
    "error": "",
    "tables": {},
    "duration_ms": 0,
    "trigger": "",
}
_primary_ok: bool | None = None
_failover_ok: bool | None = None
_stop = threading.Event()
_worker_started = False
_worker_thread: threading.Thread | None = None


def _ensure_sqlite_parent(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    from pathlib import Path

    raw = url.removeprefix("sqlite:///")
    path = Path(raw)
    path.parent.mkdir(parents=True, exist_ok=True)


def _make_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _ensure_sqlite_parent(url)
    return create_engine(url, future=True, connect_args=connect_args, pool_pre_ping=True)


def configure_engines() -> tuple[Engine, Engine | None]:
    """Create/reuse primary + optional failover engines; apply schema on both."""
    global _primary_engine, _failover_engine, _active_role
    settings = get_settings()
    with _lock:
        first = _primary_engine is None
        if _primary_engine is None:
            _primary_engine = _make_engine(settings.db_url)
            from aulos_api.db import models  # noqa: F401

            Base.metadata.create_all(bind=_primary_engine)
            from aulos_api.db.schema_patches import apply_all_schema_patches

            apply_all_schema_patches(_primary_engine)

        fo = (settings.db_failover_url or "").strip()
        if fo and _failover_engine is None:
            if fo == settings.db_url:
                logger.warning("db_failover_url equals db_url — failover disabled")
            else:
                _failover_engine = _make_engine(fo)
                from aulos_api.db import models  # noqa: F401

                Base.metadata.create_all(bind=_failover_engine)
                from aulos_api.db.schema_patches import apply_all_schema_patches

                apply_all_schema_patches(_failover_engine)

        if first:
            role = (settings.db_active_role or "primary").strip().lower()
            if role not in {"primary", "failover"}:
                role = "primary"
            if role == "failover" and _failover_engine is None:
                role = "primary"
            _active_role = role
        return _primary_engine, _failover_engine


def reset_ha_engines() -> None:
    global _primary_engine, _failover_engine
    with _lock:
        for eng in (_primary_engine, _failover_engine):
            if eng is not None:
                eng.dispose()
        _primary_engine = None
        _failover_engine = None


def active_engine() -> Engine:
    primary, failover = configure_engines()
    with _lock:
        if _active_role == "failover" and failover is not None:
            return failover
        return primary


def get_active_role() -> str:
    configure_engines()
    with _lock:
        return _active_role


def set_active_role(role: str, *, reason: str = "manual") -> str:
    global _active_role
    primary, failover = configure_engines()
    role = role.strip().lower()
    if role not in {"primary", "failover"}:
        raise ValueError("role must be primary|failover")
    if role == "failover" and failover is None:
        raise ValueError("failover engine not configured (set AULOS_DB_FAILOVER_URL)")
    with _lock:
        _active_role = role
    logger.warning("db_active_role=%s reason=%s", role, reason)
    # Rebind SessionLocal in session module
    from aulos_api.db import session as sess

    sess.bind_session_factory(active_engine())
    return _active_role


def probe(engine: Engine | None) -> bool:
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("db_probe_failed dialect=%s err=%s", getattr(engine.dialect, "name", "?"), exc)
        return False


def ha_status() -> dict[str, Any]:
    settings = get_settings()
    primary, failover = configure_engines()
    global _primary_ok, _failover_ok
    _primary_ok = probe(primary)
    _failover_ok = probe(failover) if failover else False
    with _lock:
        sync = dict(_last_sync)
        role = _active_role
    return {
        "active_role": role,
        "primary": {
            "url_scheme": settings.db_url.split(":", 1)[0],
            "dialect": primary.dialect.name,
            "ok": _primary_ok,
        },
        "failover": {
            "configured": failover is not None,
            "url_scheme": (settings.db_failover_url or "").split(":", 1)[0] or None,
            "dialect": failover.dialect.name if failover else None,
            "ok": _failover_ok,
        },
        "sync": sync,
        "auto_failover": settings.db_auto_failover,
        "sync_interval_sec": settings.db_sync_interval_sec,
        "redis_queue": settings.db_sync_redis_url or settings.redis_url,
    }


def clone_primary_to_failover(*, trigger: str = "manual") -> dict[str, Any]:
    """Full table clone: primary → failover (SQLite mirror)."""
    primary, failover = configure_engines()
    if failover is None:
        raise RuntimeError("failover not configured")
    if not probe(primary):
        raise RuntimeError("primary unreachable — refuse to overwrite failover")

    t0 = time.perf_counter()
    tables_out: dict[str, int] = {}
    from aulos_api.db import models  # noqa: F401

    sorted_tables = list(Base.metadata.sorted_tables)
    with primary.connect() as src, failover.begin() as dst:
        if failover.dialect.name == "sqlite":
            dst.execute(text("PRAGMA foreign_keys=OFF"))
        # Clear association / child tables first (reverse FK order)
        for table in reversed(sorted_tables):
            dst.execute(table.delete())
        for table in sorted_tables:
            rows = src.execute(table.select()).mappings().all()
            payload = [dict(r) for r in rows]
            if payload:
                from sqlalchemy import insert

                dst.execute(insert(table), payload)
            tables_out[table.name] = len(payload)
        if failover.dialect.name == "sqlite":
            dst.execute(text("PRAGMA foreign_keys=ON"))

    duration_ms = int((time.perf_counter() - t0) * 1000)
    result = {
        "status": "ok",
        "at": datetime.now(timezone.utc).isoformat(),
        "error": "",
        "tables": tables_out,
        "duration_ms": duration_ms,
        "trigger": trigger,
        "row_total": sum(tables_out.values()),
    }
    with _lock:
        global _last_sync
        _last_sync = result
    logger.info(
        "db_clone_ok trigger=%s rows=%s ms=%s",
        trigger,
        result["row_total"],
        duration_ms,
    )
    return result


def enqueue_sync(redis_url: str | None = None, *, trigger: str = "ops") -> dict[str, Any]:
    """Push a sync job onto Redis list (OPS message queue)."""
    settings = get_settings()
    url = (redis_url or settings.db_sync_redis_url or settings.redis_url or "").strip()
    if not url:
        # In-process immediate fallback
        return clone_primary_to_failover(trigger=trigger)
    try:
        import redis

        r = redis.Redis.from_url(url, decode_responses=True)
        job = f"{trigger}:{datetime.now(timezone.utc).isoformat()}"
        r.lpush("aulos:db_sync:queue", job)
        depth = r.llen("aulos:db_sync:queue")
        return {"queued": True, "queue": "aulos:db_sync:queue", "depth": depth, "job": job}
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis_enqueue_failed falling_back_inline err=%s", exc)
        return clone_primary_to_failover(trigger=f"{trigger}-inline")


def _worker_loop() -> None:
    settings = get_settings()
    url = (settings.db_sync_redis_url or settings.redis_url or "").strip()
    interval = max(30, int(settings.db_sync_interval_sec or 300))
    r = None
    if url:
        try:
            import redis

            r = redis.Redis.from_url(url, decode_responses=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("db_sync_redis_unavailable err=%s", exc)
            r = None

    next_sched = time.time() + interval
    while not _stop.is_set():
        # Drain queue
        if r is not None:
            try:
                item = r.brpop("aulos:db_sync:queue", timeout=1)
                if item:
                    _, job = item
                    try:
                        clone_primary_to_failover(trigger=f"queue:{job}")
                    except Exception as exc:  # noqa: BLE001
                        with _lock:
                            _last_sync.update(
                                {
                                    "status": "error",
                                    "error": str(exc)[:500],
                                    "at": datetime.now(timezone.utc).isoformat(),
                                    "trigger": f"queue:{job}",
                                }
                            )
                        logger.exception("db_clone_failed")
                    continue
            except Exception as exc:  # noqa: BLE001
                logger.warning("db_sync_brpop_err err=%s", exc)
                time.sleep(2)

        # Scheduled clone
        if time.time() >= next_sched:
            next_sched = time.time() + interval
            if get_settings().db_sync_enabled and _failover_engine is not None:
                try:
                    clone_primary_to_failover(trigger="schedule")
                except Exception as exc:  # noqa: BLE001
                    with _lock:
                        _last_sync.update(
                            {
                                "status": "error",
                                "error": str(exc)[:500],
                                "at": datetime.now(timezone.utc).isoformat(),
                                "trigger": "schedule",
                            }
                        )
                    logger.warning("scheduled_clone_failed err=%s", exc)

        # Auto-failover probe
        if get_settings().db_auto_failover:
            primary, failover = configure_engines()
            ok = probe(primary)
            global _primary_ok
            _primary_ok = ok
            if not ok and failover is not None and get_active_role() == "primary":
                try:
                    set_active_role("failover", reason="auto_primary_down")
                except Exception as exc:  # noqa: BLE001
                    logger.warning("auto_failover_failed err=%s", exc)
            elif ok and get_active_role() == "failover" and get_settings().db_auto_failback:
                try:
                    set_active_role("primary", reason="auto_primary_recovered")
                except Exception as exc:  # noqa: BLE001
                    logger.warning("auto_failback_failed err=%s", exc)

        _stop.wait(1.0)


def start_ha_worker() -> None:
    global _worker_started, _worker_thread
    with _lock:
        if _worker_started:
            return
        _stop.clear()
        _worker_started = True
    configure_engines()
    from aulos_api.db import session as sess

    sess.bind_session_factory(active_engine())
    t = threading.Thread(target=_worker_loop, name="aulos-db-ha", daemon=True)
    with _lock:
        _worker_thread = t
    t.start()
    logger.info("db_ha_worker_started role=%s", get_active_role())


def stop_ha_worker() -> None:
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


def reset_ha_worker_for_tests() -> None:
    """Test helper: stop worker and clear started flag without touching engines."""
    stop_ha_worker()
