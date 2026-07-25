"""S3: disabled source enqueue + connector failure status."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "knowledge.db"
    art = tmp_path / "artifacts"
    art.mkdir()
    monkeypatch.setenv("AULOS_KNOWLEDGE_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_KNOWLEDGE_ARTIFACT_ROOT", str(art))
    monkeypatch.setenv("AULOS_KNOWLEDGE_SYNC_JOBS", "true")
    from aulos_knowledge.config import get_settings

    get_settings.cache_clear()
    from aulos_knowledge.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def test_disabled_source_enqueue_returns_400(client: TestClient) -> None:
    r = client.patch("/v1/admin/sources/catalog-local", json={"enabled": False})
    assert r.status_code == 200
    assert r.json()["enabled"] is False
    bad = client.post("/v1/admin/jobs", json={"source_id": "catalog-local", "params": {}})
    assert bad.status_code == 400
    assert "disabled" in bad.json()["detail"].lower()


def test_connector_failure_sets_job_failed(client: TestClient) -> None:
    with patch(
        "aulos_knowledge.jobs.run_connector",
        side_effect=RuntimeError("simulated connector boom"),
    ):
        r = client.post("/v1/admin/jobs", json={"source_id": "catalog-local", "params": {}})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "simulated connector boom" in (body.get("error") or "")
