"""Audit/proofread document APIs used by OPS Knowledge tab."""

from __future__ import annotations

from pathlib import Path

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


def test_document_detail_and_publish_restore(client: TestClient) -> None:
    job = client.post("/v1/admin/jobs", json={"source_id": "catalog-local", "params": {}}).json()
    assert job["status"] == "succeeded"
    docs = client.get("/v1/admin/documents").json()
    assert docs
    doc_id = docs[0]["id"]
    detail = client.get(f"/v1/admin/documents/{doc_id}").json()
    assert detail["body"]
    assert "body_preview" in detail
    q = client.post(f"/v1/admin/documents/{doc_id}/quarantine")
    assert q.status_code == 200
    assert q.json()["status"] == "quarantine"
    p = client.post(f"/v1/admin/documents/{doc_id}/publish")
    assert p.status_code == 200
    assert p.json()["status"] == "published"
    composers = client.get("/v1/admin/composers").json()
    assert isinstance(composers, list)
    filtered = client.get("/v1/admin/documents", params={"status": "published", "q": "Bach"}).json()
    assert isinstance(filtered, list)
