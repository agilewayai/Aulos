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


def apply_dev_blog_patches(engine: Engine) -> list[str]:
    """Allow multiple posts per evidence day; index for list/search."""
    applied: list[str] = []
    dialect = engine.dialect.name
    with engine.begin() as conn:
        insp = inspect(conn)
        if not insp.has_table("dev_blog_posts"):
            return applied

        if dialect == "postgresql":
            for stmt, change_id in (
                (
                    "ALTER TABLE dev_blog_posts DROP CONSTRAINT IF EXISTS dev_blog_posts_day_key",
                    "dev_blog_posts.drop_day_unique",
                ),
                (
                    "DROP INDEX IF EXISTS ix_dev_blog_posts_day_unique",
                    "dev_blog_posts.drop_day_unique_idx",
                ),
                (
                    "DROP INDEX IF EXISTS ix_dev_blog_posts_day",
                    "dev_blog_posts.drop_day_unique_ix",
                ),
            ):
                try:
                    conn.execute(text(stmt))
                    applied.append(change_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("schema_patch_skip change=%s err=%s", change_id, exc)

        for idx_sql, change_id in (
            (
                "CREATE INDEX IF NOT EXISTS ix_dev_blog_posts_day "
                "ON dev_blog_posts (day)",
                "dev_blog_posts.ix_day",
            ),
            (
                "CREATE INDEX IF NOT EXISTS ix_dev_blog_posts_generated_at "
                "ON dev_blog_posts (generated_at)",
                "dev_blog_posts.ix_generated_at",
            ),
        ):
            try:
                conn.execute(text(idx_sql))
                if change_id not in applied:
                    applied.append(change_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("schema_index_skip change=%s err=%s", change_id, exc)

    return applied


def apply_ops_tasks_patches(engine: Engine) -> list[str]:
    """Create ops_tasks table for durable background jobs."""
    applied: list[str] = []
    dialect = engine.dialect.name
    with engine.begin() as conn:
        insp = inspect(conn)
        if insp.has_table("ops_tasks"):
            return applied
        if dialect == "postgresql":
            conn.execute(
                text(
                    """
                    CREATE TABLE ops_tasks (
                        id SERIAL PRIMARY KEY,
                        task_type VARCHAR(64) NOT NULL,
                        source VARCHAR(64) NOT NULL,
                        status VARCHAR(16) NOT NULL DEFAULT 'queued',
                        payload_json TEXT NOT NULL DEFAULT '{}',
                        result_json TEXT NOT NULL DEFAULT '{}',
                        error_detail TEXT NOT NULL DEFAULT '',
                        created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        started_at TIMESTAMPTZ,
                        finished_at TIMESTAMPTZ
                    )
                    """
                )
            )
        else:
            conn.execute(
                text(
                    """
                    CREATE TABLE ops_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_type VARCHAR(64) NOT NULL,
                        source VARCHAR(64) NOT NULL,
                        status VARCHAR(16) NOT NULL DEFAULT 'queued',
                        payload_json TEXT NOT NULL DEFAULT '{}',
                        result_json TEXT NOT NULL DEFAULT '{}',
                        error_detail TEXT NOT NULL DEFAULT '',
                        created_by_user_id INTEGER REFERENCES users(id),
                        created_at DATETIME NOT NULL,
                        started_at DATETIME,
                        finished_at DATETIME
                    )
                    """
                )
            )
        applied.append("ops_tasks.create")
        for idx_sql, change_id in (
            ("CREATE INDEX IF NOT EXISTS ix_ops_tasks_task_type ON ops_tasks (task_type)", "ops_tasks.ix_task_type"),
            ("CREATE INDEX IF NOT EXISTS ix_ops_tasks_source ON ops_tasks (source)", "ops_tasks.ix_source"),
            ("CREATE INDEX IF NOT EXISTS ix_ops_tasks_status ON ops_tasks (status)", "ops_tasks.ix_status"),
            ("CREATE INDEX IF NOT EXISTS ix_ops_tasks_created_at ON ops_tasks (created_at)", "ops_tasks.ix_created_at"),
        ):
            try:
                conn.execute(text(idx_sql))
                applied.append(change_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("schema_index_skip change=%s err=%s", change_id, exc)
    return applied


def apply_all_schema_patches(engine: Engine) -> list[str]:
    """Run every registered business-schema patch against one engine."""
    out = apply_listening_guide_patches(engine)
    out.extend(apply_dev_blog_patches(engine))
    out.extend(apply_ops_tasks_patches(engine))
    return out
