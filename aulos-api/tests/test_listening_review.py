"""OPS listening.review_llm switch (SPEC-018)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "review.db"
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


def _admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_listening_review_defaults_and_save(client: TestClient) -> None:
    headers = _admin_headers(client)
    got = client.get("/v1/ops/listening-review", headers=headers)
    assert got.status_code == 200, got.text
    body = got.json()
    assert body["key"] == "listening.review_llm"
    assert body["enabled"] is True

    off = client.put(
        "/v1/ops/listening-review",
        headers=headers,
        json={"enabled": False},
    )
    assert off.status_code == 200, off.text
    assert off.json()["enabled"] is False

    again = client.get("/v1/ops/listening-review", headers=headers)
    assert again.json()["enabled"] is False

    on = client.put(
        "/v1/ops/listening-review",
        headers=headers,
        json={"enabled": True},
    )
    assert on.json()["enabled"] is True
