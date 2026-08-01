"""OPS listening.ambient_fallback_mode switch (SPEC-006)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "ambient.db"
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
    with TestClient(app) as c:
        login = c.post(
            "/v1/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass123!"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c


def test_ambient_fallback_default_embed(client: TestClient) -> None:
    res = client.get("/v1/ops/ambient-fallback")
    assert res.status_code == 200
    body = res.json()
    assert body["key"] == "listening.ambient_fallback_mode"
    assert body["mode"] == "embed"
    assert "stream" in body["allowed"]


def test_ambient_fallback_put_stream(client: TestClient) -> None:
    res = client.put("/v1/ops/ambient-fallback", json={"mode": "stream"})
    assert res.status_code == 200
    assert res.json()["mode"] == "stream"
    again = client.get("/v1/ops/ambient-fallback")
    assert again.json()["mode"] == "stream"
    # Invalid → normalize to embed on save
    bad = client.put("/v1/ops/ambient-fallback", json={"mode": "pirate"})
    assert bad.status_code == 200
    assert bad.json()["mode"] == "embed"
