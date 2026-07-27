"""Public guide HTML security contract (AUDIT-009 F2 follow-up)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aulos_api.security_headers import PUBLIC_GUIDE_CSP, SECURITY_HEADERS


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "guide-sec.db"
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


def test_public_guide_has_csp_and_security_headers(client: TestClient) -> None:
    from datetime import datetime, timezone

    from aulos_api.db.models import ListeningGuide, User
    from aulos_api.db.session import SessionLocal

    malicious_html = (
        "<html><head><script>window.__xss=localStorage.getItem('aulos_access_token')</script></head>"
        '<body><p>evil</p><a href="javascript:alert(1)">x</a>'
        '<img src=x onerror="alert(1)"></body></html>'
    )
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == "admin@example.com").one()
        row = ListeningGuide(
            user_id=user.id,
            work_title="Security Test Work",
            composer="Test Composer",
            status="completed",
            source="test",
            summary="security fixture",
            guide_html=malicious_html,
            share_slug="evil-slug-test",
            published_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()

    resp = client.get("/v1/public/guides/evil-slug-test")
    assert resp.status_code == 200
    assert resp.headers["Content-Security-Policy"] == PUBLIC_GUIDE_CSP
    for key, value in SECURITY_HEADERS.items():
        assert resp.headers.get(key) == value
    assert "<script>" in resp.text
    assert "javascript:" not in resp.text.lower()
    assert "onerror" not in resp.text.lower()
    # Ambient/share hardening may inject trusted scripts after sanitize.
    assert "aulos-share-chrome" in resp.text or "aulos-mobile-harden" in resp.text
