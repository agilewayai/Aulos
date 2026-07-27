"""Admin route auth gate for knowledge plane."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_admin_routes_require_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "knowledge-auth.db"
    art = tmp_path / "artifacts"
    art.mkdir()
    monkeypatch.setenv("AULOS_KNOWLEDGE_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_KNOWLEDGE_ARTIFACT_ROOT", str(art))
    monkeypatch.setenv("AULOS_KNOWLEDGE_SYNC_JOBS", "true")
    monkeypatch.setenv("AULOS_KNOWLEDGE_ADMIN_TOKEN", "plane-secret-token")
    from aulos_knowledge.config import get_settings

    get_settings.cache_clear()
    from aulos_knowledge.app import create_app

    app = create_app()
    with TestClient(app) as client:
        denied = client.get("/v1/admin/sources")
        assert denied.status_code == 401
        ok = client.get("/v1/admin/sources", headers={"Authorization": "Bearer plane-secret-token"})
        assert ok.status_code == 200
    get_settings.cache_clear()
