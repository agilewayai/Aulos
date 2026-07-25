"""Ops dashboard user / biz-ops endpoint tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "ops-users.db"
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


def _admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _register(client: TestClient, email: str) -> dict:
    reg = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "UserPass123!", "display_name": email.split("@")[0]},
    )
    assert reg.status_code == 201, reg.text
    return reg.json()


def test_ops_overview_and_users_list(client: TestClient) -> None:
    headers = _admin_headers(client)
    _register(client, "alice@example.com")
    _register(client, "bob@example.com")

    overview = client.get("/v1/ops/overview", headers=headers)
    assert overview.status_code == 200, overview.text
    body = overview.json()
    assert body["users_total"] >= 3
    assert body["users_unverified"] >= 2
    assert body["roles"]["superadmin"] >= 1

    users = client.get("/v1/ops/users", headers=headers)
    assert users.status_code == 200, users.text
    rows = users.json()
    assert isinstance(rows, list)
    assert len(rows) >= 3
    assert {"id", "email", "display_name", "email_verified", "is_active", "roles", "created_at"} <= set(
        rows[0].keys()
    )

    filtered = client.get("/v1/ops/users", params={"q": "alice"}, headers=headers)
    assert filtered.status_code == 200
    assert all("alice" in u["email"] for u in filtered.json())


def test_ops_users_requires_superadmin(client: TestClient) -> None:
    _register(client, "plain@example.com")
    from aulos_api.services.mailgun import get_fake_mailbox

    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    login = client.post(
        "/v1/auth/login",
        json={"email": "plain@example.com", "password": "UserPass123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/v1/ops/users", headers=headers).status_code == 403
    assert client.get("/v1/ops/overview", headers=headers).status_code == 403


def test_patch_user_and_resend_verification(client: TestClient) -> None:
    headers = _admin_headers(client)
    user = _register(client, "carol@example.com")
    user_id = user["id"]

    patched = client.patch(
        f"/v1/ops/users/{user_id}",
        headers=headers,
        json={"email_verified": True, "roles": ["user", "superadmin"], "display_name": "Carol Ops"},
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["email_verified"] is True
    assert body["display_name"] == "Carol Ops"
    assert "superadmin" in body["roles"]

    deactivated = client.patch(
        f"/v1/ops/users/{user_id}",
        headers=headers,
        json={"is_active": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    roles = client.get("/v1/ops/roles", headers=headers)
    assert roles.status_code == 200
    names = {r["name"] for r in roles.json()}
    assert {"user", "superadmin"} <= names

    # Reactivate + unverify so resend is meaningful
    client.patch(
        f"/v1/ops/users/{user_id}",
        headers=headers,
        json={"is_active": True, "email_verified": False},
    )
    from aulos_api.services.mailgun import clear_fake_mailbox, get_fake_mailbox

    clear_fake_mailbox()
    resend = client.post(f"/v1/ops/users/{user_id}/resend-verification", headers=headers)
    assert resend.status_code == 200, resend.text
    assert resend.json()["ok"] is True
    mailbox = get_fake_mailbox()
    assert any(m["kind"] == "verify_email" and m["to"] == "carol@example.com" for m in mailbox)


def test_cannot_lock_out_self(client: TestClient) -> None:
    headers = _admin_headers(client)
    me = client.get("/v1/auth/me", headers=headers).json()
    deny = client.patch(
        f"/v1/ops/users/{me['id']}",
        headers=headers,
        json={"is_active": False},
    )
    assert deny.status_code == 400
    deny_roles = client.patch(
        f"/v1/ops/users/{me['id']}",
        headers=headers,
        json={"roles": ["user"]},
    )
    assert deny_roles.status_code == 400


def test_secure_delete_user(client: TestClient) -> None:
    headers = _admin_headers(client)
    user = _register(client, "doomed@example.com")
    user_id = user["id"]

    # Wrong confirmation email
    bad = client.request(
        "DELETE",
        f"/v1/ops/users/{user_id}",
        headers=headers,
        json={"confirm_email": "wrong@example.com"},
    )
    assert bad.status_code == 400

    me = client.get("/v1/auth/me", headers=headers).json()
    self_del = client.request(
        "DELETE",
        f"/v1/ops/users/{me['id']}",
        headers=headers,
        json={"confirm_email": me["email"]},
    )
    assert self_del.status_code == 400

    ok = client.request(
        "DELETE",
        f"/v1/ops/users/{user_id}",
        headers=headers,
        json={"confirm_email": "doomed@example.com"},
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["ok"] is True
    assert body["deleted_user_id"] == user_id

    gone = client.get(f"/v1/ops/users/{user_id}", headers=headers)
    assert gone.status_code == 404

    listed = client.get("/v1/ops/users", params={"q": "doomed"}, headers=headers)
    assert listed.json() == []

    # Cannot re-register conflict... actually email freed so re-register should work
    again = _register(client, "doomed@example.com")
    assert again["email"] == "doomed@example.com"
