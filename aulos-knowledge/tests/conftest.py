"""Shared knowledge-plane test fixtures (AUDIT-009 F5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ADMIN_TOKEN = "test-knowledge-admin-token"
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}


@pytest.fixture(autouse=True)
def _knowledge_admin_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AULOS_KNOWLEDGE_ADMIN_TOKEN", ADMIN_TOKEN)
    from aulos_knowledge.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "knowledge.db"
    art = tmp_path / "artifacts"
    art.mkdir()
    monkeypatch.setenv("AULOS_KNOWLEDGE_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_KNOWLEDGE_ARTIFACT_ROOT", str(art))
    monkeypatch.setenv("AULOS_KNOWLEDGE_SYNC_JOBS", "true")
    from aulos_knowledge.config import get_settings

    get_settings.cache_clear()
    from aulos_knowledge.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
