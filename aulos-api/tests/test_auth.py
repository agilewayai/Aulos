"""Auth MVP tests — TDD for register / verify / login / roles / Mailgun ops."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
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
    from aulos_api.services.mailgun import clear_fake_mailbox

    get_settings.cache_clear()
    db_session.reset_engine()
    clear_fake_mailbox()

    from aulos_api.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    clear_fake_mailbox()
    get_settings.cache_clear()
    db_session.reset_engine()


def test_register_login_requires_verification(client: TestClient) -> None:
    reg = client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "UserPass123!", "display_name": "User"},
    )
    assert reg.status_code == 201, reg.text
    body = reg.json()
    assert body["email"] == "user@example.com"
    assert body["email_verified"] is False
    assert "user" in body["roles"]

    denied = client.post(
        "/v1/auth/login",
        json={"email": "user@example.com", "password": "UserPass123!"},
    )
    assert denied.status_code == 403
    assert "verif" in denied.json()["detail"].lower()


def test_verify_email_then_login(client: TestClient) -> None:
    from aulos_api.services.mailgun import get_fake_mailbox

    client.post(
        "/v1/auth/register",
        json={"email": "verify@example.com", "password": "UserPass123!"},
    )
    mailbox = get_fake_mailbox()
    assert mailbox, "expected fake verification email"
    token = mailbox[-1]["verification_token"]

    verified = client.post("/v1/auth/verify-email", json={"token": token})
    assert verified.status_code == 200
    assert verified.json()["email_verified"] is True

    login = client.post(
        "/v1/auth/login",
        json={"email": "verify@example.com", "password": "UserPass123!"},
    )
    assert login.status_code == 200
    data = login.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"

    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "verify@example.com"
    assert "user" in me.json()["roles"]


def test_bootstrap_superadmin_can_configure_mailgun(client: TestClient) -> None:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/v1/auth/me", headers=headers)
    assert "superadmin" in me.json()["roles"]

    current = client.get("/v1/ops/mailgun", headers=headers)
    assert current.status_code == 200

    updated = client.put(
        "/v1/ops/mailgun",
        headers=headers,
        json={
            "api_key": "key-test",
            "domain": "mg.example.com",
            "from_email": "noreply@example.com",
            "enabled": True,
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["domain"] == "mg.example.com"
    assert body["from_email"] == "noreply@example.com"
    assert body["enabled"] is True
    assert body["api_key_set"] is True
    assert "key-test" not in str(body)  # never echo secret


def test_non_superadmin_cannot_access_mailgun_ops(client: TestClient) -> None:
    from aulos_api.services.mailgun import get_fake_mailbox

    client.post(
        "/v1/auth/register",
        json={"email": "normal@example.com", "password": "UserPass123!"},
    )
    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    login = client.post(
        "/v1/auth/login",
        json={"email": "normal@example.com", "password": "UserPass123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    denied = client.get("/v1/ops/mailgun", headers=headers)
    assert denied.status_code == 403


def test_duplicate_register_rejected(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "password": "UserPass123!"}
    assert client.post("/v1/auth/register", json=payload).status_code == 201
    again = client.post("/v1/auth/register", json=payload)
    assert again.status_code == 409
