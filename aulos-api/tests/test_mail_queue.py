"""SPEC-011 transactional mail queue tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "mailq.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_MAIL_QUEUE_ENABLED", "true")
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


def test_fake_provider_still_sends_sync(client: TestClient) -> None:
    from aulos_api.services.mailgun import get_fake_mailbox

    reg = client.post(
        "/v1/auth/register",
        json={"email": "queue-fake@example.com", "password": "UserPass123!"},
    )
    assert reg.status_code == 201, reg.text
    mailbox = get_fake_mailbox()
    assert mailbox
    assert mailbox[-1]["kind"] == "verify_email"
    assert "html" in mailbox[-1]


def test_live_provider_enqueues_on_redis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "mailq-live.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "auto")
    monkeypatch.setenv("AULOS_MAIL_QUEUE_ENABLED", "true")
    monkeypatch.setenv("AULOS_REDIS_URL", "redis://127.0.0.1:6379/15")
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
    mock_r = MagicMock()
    mock_r.llen.return_value = 1

    with TestClient(app) as client:
        # Enable mailgun so provider becomes live
        login = client.post(
            "/v1/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass123!"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        client.put(
            "/v1/ops/mailgun",
            headers=headers,
            json={
                "api_key": "key-live",
                "domain": "mg.example.com",
                "from_email": "noreply@example.com",
                "enabled": True,
            },
        )

        with patch("redis.Redis.from_url", return_value=mock_r):
            from aulos_api.db.session import SessionLocal, get_engine
            from aulos_api.services.mailgun import send_verification_email

            get_engine()
            assert SessionLocal is not None
            db = SessionLocal()
            try:
                out = send_verification_email(
                    db=db,
                    to_email="live-user@example.com",
                    raw_token="tok_live_queue_test_abcdefgh",
                )
            finally:
                db.close()

        assert out.get("queued") is True
        assert out.get("queue") == "aulos:mail:queue"
        mock_r.lpush.assert_called_once()
        raw = mock_r.lpush.call_args[0][1]
        job = json.loads(raw)
        assert job["kind"] == "verify_email"
        assert job["to_email"] == "live-user@example.com"
        assert "Salon Codex" in job["html"]
        # Must not have hit fake mailbox / live httpx during enqueue
        from aulos_api.services.mailgun import get_fake_mailbox

        assert get_fake_mailbox() == []

    get_settings.cache_clear()
    db_session.reset_engine()


def test_deliver_mail_job_uses_fresh_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "mailq-deliver.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_MAIL_QUEUE_ENABLED", "true")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")

    from aulos_api.config import get_settings
    from aulos_api.db import session as db_session
    from aulos_api.services.mailgun import clear_fake_mailbox, get_fake_mailbox

    get_settings.cache_clear()
    db_session.reset_engine()
    clear_fake_mailbox()
    db_session.get_engine()
    db_session.init_db()

    from aulos_api.services.mail_queue import deliver_mail_job

    result = deliver_mail_job(
        {
            "kind": "verify_email",
            "to_email": "worker@example.com",
            "subject": "Test",
            "text": "plain",
            "html": "<p>hi</p>",
            "extra": {"verification_token": "abc"},
        }
    )
    assert result.get("provider") == "fake"
    assert get_fake_mailbox()[-1]["to"] == "worker@example.com"

    get_settings.cache_clear()
    db_session.reset_engine()


def test_ops_mail_queue_status(client: TestClient) -> None:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = client.get("/v1/ops/mail/queue", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["queue"] == "aulos:mail:queue"
    assert "enabled" in body
    assert "worker_started" in body
