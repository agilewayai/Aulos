"""Mailgun configuration + delivery observability tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "mailgun.db"
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


@pytest.fixture()
def auto_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "mailgun-auto.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "auto")
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


def _superadmin_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_mailgun_configuration_test_succeeds_when_configured(client: TestClient) -> None:
    from aulos_api.services.mailgun import get_fake_mailbox

    headers = _superadmin_headers(client)
    saved = client.put(
        "/v1/ops/mailgun",
        headers=headers,
        json={
            "api_key": "key-test",
            "domain": "mg.example.com",
            "from_email": "noreply@example.com",
            "enabled": True,
            "region": "us",
        },
    )
    assert saved.status_code == 200
    assert saved.json()["provider_mode"] == "fake"
    assert saved.json()["ready_for_live_send"] is True

    result = client.post(
        "/v1/ops/mailgun/test",
        headers=headers,
        json={"to_email": "probe@example.com"},
    )
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["ok"] is True
    assert body["provider_mode"] == "fake"
    assert "probe@example.com" in body["detail"]
    assert "FAKE" in body["detail"]
    assert body["delivery_id"] is not None

    mailbox = get_fake_mailbox()
    assert any(m.get("to") == "probe@example.com" and m.get("kind") == "config_test" for m in mailbox)
    probe = next(m for m in mailbox if m.get("kind") == "config_test")
    assert "Salon Codex" in (probe.get("html") or "")
    assert "#c9a66b" in (probe.get("html") or "")

    deliveries = client.get("/v1/ops/mailgun/deliveries", headers=headers)
    assert deliveries.status_code == 200
    assert any(d["kind"] == "config_test" and d["status"] == "accepted_fake" for d in deliveries.json())


def test_mailgun_configuration_test_fails_when_incomplete(client: TestClient) -> None:
    headers = _superadmin_headers(client)
    client.put(
        "/v1/ops/mailgun",
        headers=headers,
        json={"api_key": "", "domain": "", "from_email": "", "enabled": True},
    )
    result = client.post(
        "/v1/ops/mailgun/test",
        headers=headers,
        json={"to_email": "probe@example.com"},
    )
    assert result.status_code == 400
    assert "not fully configured" in result.json()["detail"].lower()


def test_mailgun_configuration_test_requires_superadmin(client: TestClient) -> None:
    from aulos_api.services.mailgun import get_fake_mailbox

    client.post(
        "/v1/auth/register",
        json={"email": "user@example.com", "password": "UserPass123!"},
    )
    verify_token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": verify_token})
    login = client.post(
        "/v1/auth/login",
        json={"email": "user@example.com", "password": "UserPass123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    denied = client.post(
        "/v1/ops/mailgun/test",
        headers=headers,
        json={"to_email": "probe@example.com"},
    )
    assert denied.status_code == 403


def test_auto_provider_sends_live_mailgun_when_enabled(auto_client: TestClient) -> None:
    headers = _superadmin_headers(auto_client)
    saved = auto_client.put(
        "/v1/ops/mailgun",
        headers=headers,
        json={
            "api_key": "key-live",
            "domain": "mg.example.com",
            "from_email": "noreply@example.com",
            "enabled": True,
            "region": "eu",
        },
    )
    assert saved.status_code == 200
    assert saved.json()["provider_mode"] == "mailgun"
    assert saved.json()["region"] == "eu"

    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.status_code = 200
    mock_response.text = '{"id":"<msg@mailgun>","message":"Queued. Thank you."}'
    mock_response.json.return_value = {"id": "<msg@mailgun>", "message": "Queued. Thank you."}

    with patch("aulos_api.services.mailgun.httpx.post", return_value=mock_response) as mocked:
        result = auto_client.post(
            "/v1/ops/mailgun/test",
            headers=headers,
            json={"to_email": "live@example.com"},
        )
        assert result.status_code == 200, result.text
        body = result.json()
        assert body["ok"] is True
        assert body["provider_mode"] == "mailgun"
        assert body["delivery_id"] is not None
        mocked.assert_called_once()
        args, kwargs = mocked.call_args
        assert args[0] == "https://api.eu.mailgun.net/v3/mg.example.com/messages"
        assert kwargs["auth"] == ("api", "key-live")
        payload = kwargs["data"]
        assert "html" in payload
        assert "Salon Codex" in payload["html"]
        assert "#0c1216" in payload["html"]
        assert "#c9a66b" in payload["html"]

    deliveries = auto_client.get("/v1/ops/mailgun/deliveries", headers=headers)
    assert deliveries.status_code == 200
    rows = deliveries.json()
    assert rows[0]["status"] == "sent"
    assert rows[0]["provider"] == "mailgun"
    assert rows[0]["provider_message_id"] == "<msg@mailgun>"


def test_auto_provider_surfaces_mailgun_http_error(auto_client: TestClient) -> None:
    headers = _superadmin_headers(auto_client)
    auto_client.put(
        "/v1/ops/mailgun",
        headers=headers,
        json={
            "api_key": "key-bad",
            "domain": "mg.example.com",
            "from_email": "noreply@example.com",
            "enabled": True,
        },
    )
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.status_code = 401
    mock_response.text = "Forbidden"
    mock_response.json.side_effect = ValueError("no json")

    with patch("aulos_api.services.mailgun.httpx.post", return_value=mock_response):
        result = auto_client.post(
            "/v1/ops/mailgun/test",
            headers=headers,
            json={"to_email": "live@example.com"},
        )
        assert result.status_code == 502
        assert "401" in result.json()["detail"]

    deliveries = auto_client.get("/v1/ops/mailgun/deliveries", headers=headers)
    assert any(d["status"] == "failed" for d in deliveries.json())
