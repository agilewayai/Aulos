"""Regen / review must not reuse identity-polluted dossiers (anti-mask class)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aulos_skills.identity_lock import (
    dossier_betrays_identity_lock,
    scrub_dossier_if_identity_polluted,
)


def test_masked_bwv_with_foreign_op_betrays() -> None:
    title = "Bach — Concerto BWV 1060"
    dossier = {
        "work_title": title,
        "composer": "Johann Sebastian Bach",
        "listening_thesis": "Remember BWV 1060 dialogue.",
        "zh": {"listening_thesis": "欣德米特 Op.11 中提琴奏鸣曲。"},
    }
    assert dossier_betrays_identity_lock(dossier, work_title=title)
    scrubbed, hit = scrub_dossier_if_identity_polluted(
        dossier, work_title=title, composer="Johann Sebastian Bach"
    )
    assert hit
    assert scrubbed.get("_provenance", {}).get("scrubbed_identity_pollution")
    assert not scrubbed.get("zh")


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "regen.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")

    from aulos_api.config import get_settings
    from aulos_api.db import session as db_session

    get_settings.cache_clear()
    db_session.reset_engine()
    from aulos_api.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    db_session.reset_engine()


def test_retrieve_drops_masked_polluted_doc(client: TestClient) -> None:
    from aulos_api.db.models import KnowledgeChunk, KnowledgeDocument
    from aulos_api.db.session import SessionLocal, get_engine
    from aulos_api.services.knowledge_base import retrieve

    get_engine()
    db = SessionLocal()
    try:
        poisoned = {
            "composer": "Johann Sebastian Bach",
            "work_title": "Bach — Concerto BWV 1060",
            "listening_thesis": "BWV 1060 concerto dialogue.",
            "zh_hant": {"listening_thesis": "欣德米特中提琴奏鸣曲 Op.11 No.5"},
            "width_points": ["欣德米特本人是杰出的中提琴家"],
        }
        doc = KnowledgeDocument(
            work_key="regen-poison-bwv1060",
            composer="Johann Sebastian Bach",
            title="Johann Sebastian Bach — Concerto BWV 1060",
            dossier_json=json.dumps(poisoned, ensure_ascii=False),
            content_text="Bach BWV 1060",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        db.add(
            KnowledgeChunk(
                document_id=doc.id,
                section="title",
                text="Bach BWV 1060 for oboe and violin",
                embedding_json="[]",
            )
        )
        db.commit()
        out = retrieve(
            db,
            query="Bach Concerto BWV 1060 for Oboe and Violin",
            work_hint="Bach — Concerto BWV 1060 for Oboe and Violin",
            composer="Johann Sebastian Bach",
            user_id=1,
            k=6,
        )
        assert out.get("kb_dossier") in ({}, None) or not out.get("kb_dossier")
        for h in out.get("hits") or []:
            assert h.get("document_id") != doc.id
    finally:
        db.close()
