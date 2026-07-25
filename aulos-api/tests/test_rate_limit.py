"""Rate-limit middleware + abuse detection."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aulos_api.security.rate_limit import (
    AbuseDetector,
    RateRule,
    SlidingWindowLimiter,
    client_ip,
    default_api_rules,
)


def test_sliding_window_blocks_after_limit() -> None:
    lim = SlidingWindowLimiter()
    now = 1000.0
    for i in range(3):
        d = lim.hit("t:ip", limit=3, window_sec=60, now=now + i)
        assert d.allowed
    blocked = lim.hit("t:ip", limit=3, window_sec=60, now=now + 3)
    assert not blocked.allowed
    assert blocked.retry_after > 0


def test_abuse_detector_escalates() -> None:
    det = AbuseDetector(strike_limit=3, window_sec=60)
    assert det.note_block(ip="1.2.3.4", path="/v1/auth/login", rule="auth_login") is False
    assert det.note_block(ip="1.2.3.4", path="/v1/auth/login", rule="auth_login") is False
    assert det.note_block(ip="1.2.3.4", path="/v1/auth/login", rule="auth_login") is True


def test_client_ip_trusts_forwarded() -> None:
    assert client_ip({"x-forwarded-for": "9.9.9.9, 10.0.0.1"}, "127.0.0.1", trust_proxy=True) == "9.9.9.9"
    assert client_ip({"x-forwarded-for": "9.9.9.9"}, "127.0.0.1", trust_proxy=False) == "127.0.0.1"


def test_default_rules_cover_sensitive_paths() -> None:
    login = default_api_rules("POST", "/v1/auth/login")
    assert login is not None and login.name == "auth_login"
    register = default_api_rules("POST", "/v1/auth/register")
    assert register is not None and register.name == "auth_register"
    guides = default_api_rules("GET", "/v1/public/guides/abc")
    assert guides is not None and guides.name == "public_guides"
    assert default_api_rules("GET", "/health") is None


def _tiny_login_rules(method: str, path: str) -> RateRule | None:
    if method.upper() == "POST" and path == "/v1/auth/login":
        return RateRule("auth_login", limit=2, window_sec=60)
    return None


@pytest.fixture()
def limited_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "rl.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("AULOS_ABUSE_STRIKE_LIMIT", "20")
    monkeypatch.setattr("aulos_api.security.middleware.default_api_rules", _tiny_login_rules)

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


def test_login_rate_limit_returns_429(limited_client: TestClient) -> None:
    payload = {"email": "nobody@example.com", "password": "wrong-password"}
    assert limited_client.post("/v1/auth/login", json=payload).status_code == 401
    assert limited_client.post("/v1/auth/login", json=payload).status_code == 401
    blocked = limited_client.post("/v1/auth/login", json=payload)
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Too many requests"
    assert blocked.headers.get("Retry-After")
    assert blocked.headers.get("X-RateLimit-Rule") == "auth_login"


def test_chat_requires_auth(limited_client: TestClient) -> None:
    res = limited_client.post("/v1/chat", json={"message": "hello", "thread_id": "t1"})
    assert res.status_code == 401
