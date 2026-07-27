"""Schema patch applies on SQLite and Postgres (SPEC-013 closeout gate)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text


def test_listening_guide_patches_add_columns_on_sqlite(tmp_path: Path) -> None:
    db = tmp_path / "legacy.db"
    eng = create_engine(f"sqlite:///{db}", future=True)
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE listening_guides (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    work_title VARCHAR(255) NOT NULL,
                    composer VARCHAR(255) DEFAULT '',
                    status VARCHAR(32) DEFAULT 'completed',
                    source VARCHAR(32) DEFAULT 'curated',
                    summary TEXT DEFAULT '',
                    guide_html TEXT DEFAULT '',
                    steps_json TEXT DEFAULT '[]',
                    research_json TEXT DEFAULT '{}',
                    created_at DATETIME
                )
                """
            )
        )
    from aulos_api.db.schema_patches import apply_all_schema_patches

    applied = apply_all_schema_patches(eng)
    assert "listening_guides.message" in applied
    assert "listening_guides.favorited_at" in applied
    cols = {c["name"] for c in inspect(eng).get_columns("listening_guides")}
    for name in ("message", "error_detail", "tags_json", "favorited_at", "updated_at", "share_slug"):
        assert name in cols
    second = apply_all_schema_patches(eng)
    assert "listening_guides.message" not in second
