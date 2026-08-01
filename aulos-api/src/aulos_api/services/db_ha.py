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
from sqlalchemy.pool import NullPool

from aulos_api.config import get_settings
from aulos_api.db.session import Base

logger = logging.getLogger("aulos_api.db_ha")

_lock = threading.RLock()
_primary_engine: Engine | None = None
_failover_engine: Engine | None = None
_probe_engines: dict[str, Engine] = {}
_active_role: str = "primary"  # primary | failover
_primary_fail_streak: int = 0
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


def _pool_kwargs_for_url(url: str) -> dict[str, Any]:
    """QueuePool sizing for Postgres; SQLite keeps SQLAlchemy defaults (+ check_same_thread)."""
    if url.startswith("sqlite"):
        return {}
    settings = get_settings()
    return {
        "pool_size": max(5, int(settings.db_pool_size or 20)),
        "max_overflow": max(0, int(settings.db_max_overflow or 40)),
        "pool_timeout": float(settings.db_pool_timeout or 30.0),
        "pool_recycle": max(60, int(settings.db_pool_recycle or 1800)),
    }


def _make_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _ensure_sqlite_parent(url)
    return create_engine(
        url,
        future=True,
        connect_args=connect_args,
        pool_pre_ping=True,
        **_pool_kwargs_for_url(url),
    )


def _probe_engine_for(url: str) -> Engine:
    """Dedicated NullPool engine so HA probes never compete with the business QueuePool."""
    with _lock:
        eng = _probe_engines.get(url)
        if eng is not None:
            return eng
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _ensure_sqlite_parent(url)
        eng = create_engine(
            url,
            future=True,
            connect_args=connect_args,
            poolclass=NullPool,
            pool_pre_ping=True,
        )
        _probe_engines[url] = eng
        return eng


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
    global _primary_engine, _failover_engine, _probe_engines, _primary_fail_streak
    with _lock:
        for eng in (_primary_engine, _failover_engine, *_probe_engines.values()):
            if eng is not None:
                eng.dispose()
        _primary_engine = None
        _failover_engine = None
        _probe_engines = {}
        _primary_fail_streak = 0


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
    global _active_role, _primary_fail_streak
    primary, failover = configure_engines()
    role = role.strip().lower()
    if role not in {"primary", "failover"}:
        raise ValueError("role must be primary|failover")
    if role == "failover" and failover is None:
        raise ValueError("failover engine not configured (set AULOS_DB_FAILOVER_URL)")
    with _lock:
        _active_role = role
        if role == "primary":
            _primary_fail_streak = 0
    logger.warning("db_active_role=%s reason=%s", role, reason)
    # Rebind SessionLocal in session module
    from aulos_api.db import session as sess

    sess.bind_session_factory(active_engine())
    return _active_role


def probe(engine: Engine | None, *, url: str | None = None) -> bool:
    if engine is None:
        return False
    # Prefer NullPool probe engine keyed by the real URL so a saturated business
    # QueuePool cannot look like a down primary. Never use str(engine.url) alone —
    # SQLAlchemy hides passwords as "***" which breaks auth.
    probe_url = (url or "").strip()
    if not probe_url:
        try:
            probe_url = engine.url.render_as_string(hide_password=False)
        except Exception:  # noqa: BLE001
            probe_url = ""
    probe_eng = _probe_engine_for(probe_url) if probe_url else engine
    try:
        with probe_eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("db_probe_failed dialect=%s err=%s", getattr(engine.dialect, "name", "?"), exc)
        return False


def ha_status() -> dict[str, Any]:
    settings = get_settings()
    primary, failover = configure_engines()
    global _primary_ok, _failover_ok
    _primary_ok = probe(primary, url=settings.db_url)
    fo = (settings.db_failover_url or "").strip()
    _failover_ok = probe(failover, url=fo) if failover else False
    with _lock:
        sync = dict(_last_sync)
        role = _active_role
        fail_streak = _primary_fail_streak
    pool = _pool_kwargs_for_url(settings.db_url)
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
        "pool": {
            "pool_size": pool.get("pool_size"),
            "max_overflow": pool.get("max_overflow"),
            "pool_timeout": pool.get("pool_timeout"),
            "pool_recycle": pool.get("pool_recycle"),
            "probe_isolated": True,
            "failover_fail_threshold": max(1, int(settings.db_failover_fail_threshold or 3)),
            "primary_fail_streak": fail_streak,
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

        # Auto-failover probe (isolated NullPool; require consecutive failures)
        if get_settings().db_auto_failover:
            settings = get_settings()
            primary, failover = configure_engines()
            ok = probe(primary, url=settings.db_url)
            global _primary_ok, _primary_fail_streak
            _primary_ok = ok
            threshold = max(1, int(settings.db_failover_fail_threshold or 3))
            with _lock:
                if ok:
                    _primary_fail_streak = 0
                else:
                    _primary_fail_streak += 1
                streak = _primary_fail_streak
            if (
                not ok
                and failover is not None
                and get_active_role() == "primary"
                and streak >= threshold
            ):
                try:
                    set_active_role(
                        "failover",
                        reason=f"auto_primary_down streak={streak}/{threshold}",
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("auto_failover_failed err=%s", exc)
            elif ok and get_active_role() == "failover" and settings.db_auto_failback:
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
