"""SPEC-028 fleet ensure Catalog composer dossiers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "tasks.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("AULOS_KNOWLEDGE_PLANE_ENABLED", "true")

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
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ensure_dossiers_dry_run(client: TestClient) -> None:
    thin = {"composer": {"id": "x"}, "timeline": [], "portrait": None}
    with (
        patch(
            "aulos_api.services.knowledge_proxy.fetch_composer_dossier_sync",
            return_value=thin,
        ),
        patch(
            "aulos_api.services.knowledge_proxy.enqueue_composer_dossier_build_sync"
        ) as enq,
    ):
        resp = client.post(
            "/v1/ops/knowledge/composers/ensure-dossiers",
            headers=_admin_headers(client),
            json={"dry_run": True},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dry_run"] is True
    assert body["composer_count"] >= 1
    assert body["enqueued"]
    assert all(e.get("dry_run") for e in body["enqueued"])
    enq.assert_not_called()


def test_ensure_dossiers_enqueues_thin(client: TestClient) -> None:
    thin = {}
    rich = {
        "composer": {"id": "frederic-chopin", "summary_en": "A" * 50},
        "timeline": [{"event_type": "birth"}],
        "events_count": 3,
        "portrait": {"source_url": "https://example.com/p.jpg"},
    }

    def _fetch(cid: str) -> dict:
        return rich if cid == "frederic-chopin" else thin

    with (
        patch(
            "aulos_api.services.knowledge_proxy.fetch_composer_dossier_sync",
            side_effect=_fetch,
        ),
        patch(
            "aulos_api.services.knowledge_proxy.enqueue_composer_dossier_build_sync",
            return_value={"ok": True, "composer_id": "x", "job_id": 1},
        ) as enq,
    ):
        resp = client.post(
            "/v1/ops/knowledge/composers/ensure-dossiers",
            headers=_admin_headers(client),
            json={"dry_run": False},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "frederic-chopin" in body["rich"]
    assert enq.called
    assert body["enqueued"]
