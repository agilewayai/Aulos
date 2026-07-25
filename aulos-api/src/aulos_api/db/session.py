from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from aulos_api.config import get_settings

_engine = None
SessionLocal: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def get_engine():
    global _engine, SessionLocal
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if settings.db_url.startswith("sqlite") else {}
        if settings.db_url.startswith("sqlite:///"):
            from pathlib import Path

            raw = settings.db_url.removeprefix("sqlite:///")
            # sqlite:////abs/path -> /abs/path ; sqlite:///./rel -> ./rel
            path = Path(raw)
            if not path.is_absolute() and raw.startswith("./"):
                path = Path(raw)
            path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(settings.db_url, future=True, connect_args=connect_args)
        SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def reset_engine() -> None:
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    SessionLocal = None


def init_db() -> None:
    from aulos_api.db import models  # noqa: F401
    from sqlalchemy import inspect, text

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    # Lightweight SQLite column add for evolving MVP tables
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            cols = {c["name"] for c in inspect(conn).get_columns("listening_guides")} if inspect(conn).has_table("listening_guides") else set()
            if cols and "skill_versions_json" not in cols:
                conn.execute(text("ALTER TABLE listening_guides ADD COLUMN skill_versions_json TEXT DEFAULT '{}'"))
            if cols and "share_slug" not in cols:
                conn.execute(text("ALTER TABLE listening_guides ADD COLUMN share_slug VARCHAR(64)"))
            if cols and "published_at" not in cols:
                conn.execute(text("ALTER TABLE listening_guides ADD COLUMN published_at DATETIME"))
            # unique index for share_slug (ignore if already present)
            if cols or inspect(conn).has_table("listening_guides"):
                try:
                    conn.execute(
                        text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS ix_listening_guides_share_slug "
                            "ON listening_guides (share_slug)"
                        )
                    )
                except Exception:  # noqa: BLE001
                    pass


def get_db():
    get_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
