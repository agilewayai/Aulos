"""Idempotent schema patches for business DB (Postgres primary + SQLite failover).

create_all does not ADD columns to existing tables. Every model-field addition must
be listed here and applied on BOTH dialects at boot / HA configure.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("aulos_api.schema_patches")


def apply_listening_guide_patches(engine: Engine) -> list[str]:
    """Add missing listening_guides columns/indexes. Returns applied change ids."""
    applied: list[str] = []
    dialect = engine.dialect.name
    ts = "TIMESTAMP WITH TIME ZONE" if dialect == "postgresql" else "DATETIME"
    with engine.begin() as conn:
        insp = inspect(conn)
        if not insp.has_table("listening_guides"):
            return applied
        cols = {c["name"] for c in insp.get_columns("listening_guides")}

        def add(col: str, ddl: str, change_id: str) -> None:
            nonlocal cols
            if col in cols:
                return
            conn.execute(text(ddl))
            cols.add(col)
            applied.append(change_id)
            logger.info("schema_patch applied dialect=%s change=%s", dialect, change_id)

        add(
            "skill_versions_json",
            "ALTER TABLE listening_guides ADD COLUMN skill_versions_json TEXT DEFAULT '{}'",
            "listening_guides.skill_versions_json",
        )
        add(
            "share_slug",
            "ALTER TABLE listening_guides ADD COLUMN share_slug VARCHAR(64)",
            "listening_guides.share_slug",
        )
        add(
            "published_at",
            f"ALTER TABLE listening_guides ADD COLUMN published_at {ts}",
            "listening_guides.published_at",
        )
        add(
            "message",
            "ALTER TABLE listening_guides ADD COLUMN message TEXT DEFAULT ''",
            "listening_guides.message",
        )
        add(
            "error_detail",
            "ALTER TABLE listening_guides ADD COLUMN error_detail TEXT DEFAULT ''",
            "listening_guides.error_detail",
        )
        add(
            "tags_json",
            "ALTER TABLE listening_guides ADD COLUMN tags_json TEXT DEFAULT '[]'",
            "listening_guides.tags_json",
        )
        add(
            "favorited_at",
            f"ALTER TABLE listening_guides ADD COLUMN favorited_at {ts}",
            "listening_guides.favorited_at",
        )
        add(
            "updated_at",
            f"ALTER TABLE listening_guides ADD COLUMN updated_at {ts}",
            "listening_guides.updated_at",
        )

        for idx_sql, change_id in (
            (
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_listening_guides_share_slug "
                "ON listening_guides (share_slug)",
                "listening_guides.ix_share_slug",
            ),
            (
                "CREATE INDEX IF NOT EXISTS ix_listening_guides_favorited_at "
                "ON listening_guides (favorited_at)",
                "listening_guides.ix_favorited_at",
            ),
            (
                "CREATE INDEX IF NOT EXISTS ix_listening_guides_status "
                "ON listening_guides (status)",
                "listening_guides.ix_status",
            ),
        ):
            try:
                conn.execute(text(idx_sql))
                applied.append(change_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("schema_index_skip change=%s err=%s", change_id, exc)

    return applied


def apply_all_schema_patches(engine: Engine) -> list[str]:
    """Run every registered business-schema patch against one engine."""
    return apply_listening_guide_patches(engine)
