"""Knowledge benchmark ops task queue."""

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


def test_enqueue_knowledge_benchmark_task(client: TestClient) -> None:
    headers = _admin_headers(client)
    with patch("aulos_api.services.task_queue._handle_knowledge_benchmark") as mock_handler:
        mock_handler.return_value = {
            "run_id": 42,
            "overall_score": 81.5,
            "grade": "B",
            "duration_ms": 120,
        }
        r = client.post("/v1/ops/knowledge/benchmark/run", headers=headers, json={"trigger": "ops"})
    assert r.status_code == 202
    body = r.json()
    assert body["task_type"] == "knowledge.benchmark"
    assert body["source"] == "ops.knowledge"
    assert body["status"] == "completed"
    assert body["run_id"] == 42
