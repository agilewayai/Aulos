from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from aulos_api.config import get_settings

_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def bind_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Point SessionLocal at the active HA engine (primary or failover)."""
    global _engine, SessionLocal
    _engine = engine
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal


def get_engine():
    global _engine, SessionLocal
    if _engine is None:
        # Prefer HA-aware active engine when failover is configured
        settings = get_settings()
        if (settings.db_failover_url or "").strip():
            from aulos_api.services import db_ha

            eng = db_ha.active_engine()
            bind_session_factory(eng)
            return eng

        connect_args = {"check_same_thread": False} if settings.db_url.startswith("sqlite") else {}
        if settings.db_url.startswith("sqlite:///"):
            from pathlib import Path

            raw = settings.db_url.removeprefix("sqlite:///")
            path = Path(raw)
            if not path.is_absolute() and raw.startswith("./"):
                path = Path(raw)
            path.parent.mkdir(parents=True, exist_ok=True)
        pool_kwargs: dict = {}
        if not settings.db_url.startswith("sqlite"):
            from aulos_api.services.db_ha import _pool_kwargs_for_url

            pool_kwargs = _pool_kwargs_for_url(settings.db_url)
        _engine = create_engine(
            settings.db_url,
            future=True,
            connect_args=connect_args,
            pool_pre_ping=True,
            **pool_kwargs,
        )
        SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def reset_engine() -> None:
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    SessionLocal = None
    try:
        from aulos_api.services import db_ha

        db_ha.reset_ha_engines()
    except Exception:  # noqa: BLE001
        pass


def init_db() -> None:
    from aulos_api.db import models  # noqa: F401
    from aulos_api.db.schema_patches import apply_all_schema_patches

    settings = get_settings()
    if (settings.db_failover_url or "").strip():
        from aulos_api.services import db_ha

        db_ha.configure_engines()
        bind_session_factory(db_ha.active_engine())
        return

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    apply_all_schema_patches(engine)


def get_db():
    get_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
