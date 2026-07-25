from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "api.db"
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


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "aulos-api"


def test_chat_requires_auth(client: TestClient) -> None:
    response = client.post("/v1/chat", json={"message": "hello", "thread_id": "t1"})
    assert response.status_code == 401


def test_chat_fake_authenticated(client: TestClient) -> None:
    from aulos_api.services.mailgun import get_fake_mailbox

    client.post(
        "/v1/auth/register",
        json={"email": "chat@example.com", "password": "UserPass123!"},
    )
    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    login = client.post(
        "/v1/auth/login",
        json={"email": "chat@example.com", "password": "UserPass123!"},
    )
    assert login.status_code == 200
    access = login.json()["access_token"]
    response = client.post(
        "/v1/chat",
        json={"message": "hello", "thread_id": "t1"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "hello" in body["reply"]
    assert body["thread_id"] == "t1"
    assert body["source"] == "fake"
