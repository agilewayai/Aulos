"""Knowledge retrieve must not hijack unrelated queries onto Goldberg."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aulos_api.services.knowledge_base import works_compatible


def test_works_compatible_requires_distinctive_overlap() -> None:
    assert works_compatible(
        "Bach Goldberg Variations",
        doc_title="J.S. Bach — Goldberg Variations, BWV 988",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bwv-988",
        score=0.5,
    )
    assert not works_compatible(
        "Mozart Symphony No. 40",
        doc_title="J.S. Bach — Goldberg Variations, BWV 988",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bwv-988",
        score=0.55,
    )
    assert not works_compatible(
        "Bach Mass in B minor",
        doc_title="J.S. Bach — Goldberg Variations, BWV 988",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bwv-988",
        score=0.66,
    )


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "kb.db"
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


def test_retrieve_does_not_attach_goldberg_to_mozart(client: TestClient) -> None:
    from aulos_api.db.session import SessionLocal, get_engine
    from aulos_api.services.knowledge_base import retrieve, seed_corpus_knowledge

    get_engine()
    db = SessionLocal()
    try:
        seed_corpus_knowledge(db)
        result = retrieve(
            db,
            query="Mozart Symphony No. 40",
            work_hint="Mozart Symphony No. 40",
            composer="",
            user_id=1,
            k=6,
        )
        assert not (result.get("kb_dossier") or {}).get("work_title")
        assert result.get("rag_mode") in {"no_match", "empty", "lexical", "vector", "fastembed", "openai"}
        for hit in result.get("hits") or []:
            assert "Goldberg" not in (hit.get("title") or "")
    finally:
        db.close()
