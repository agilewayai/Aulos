"""SPEC-018 Ops background task queue tests."""

from __future__ import annotations

from pathlib import Path

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
    monkeypatch.setenv("AULOS_TASK_QUEUE_SYNC", "true")

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


def test_ops_tasks_dashboard_and_list(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "aulos-api").mkdir(parents=True)
    monkeypatch.setenv("AULOS_REPO_ROOT", str(root))
    from aulos_api.config import get_settings

    get_settings.cache_clear()

    headers = _admin_headers(client)
    dash = client.get("/v1/ops/tasks/dashboard", headers=headers)
    assert dash.status_code == 200
    body = dash.json()
    assert "queues" in body
    assert any(q["source"] == "ops" for q in body["queues"])

    gen = client.post("/v1/ops/dev-blog/2026-07-21/generate", headers=headers, json={})
    assert gen.status_code == 202
    task_id = gen.json()["task_id"]

    listed = client.get("/v1/ops/tasks", headers=headers, params={"task_type": "dev_blog.generate"})
    assert listed.status_code == 200
    assert any(t["id"] == task_id for t in listed.json())

    one = client.get(f"/v1/ops/tasks/{task_id}", headers=headers)
    assert one.status_code == 200
    assert one.json()["status"] == "completed"
