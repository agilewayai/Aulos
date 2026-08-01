"""META-001 §3.3 — crawl jobs async queue."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from conftest import AUTH_HEADERS


def test_create_job_async_returns_queued(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AULOS_KNOWLEDGE_SYNC_JOBS", "false")
    from aulos_knowledge.config import get_settings

    get_settings.cache_clear()

    # Force async via query even if settings cached oddly
    r = client.post(
        "/v1/admin/jobs?async=true",
        headers=AUTH_HEADERS,
        json={"source_id": "catalog-local", "params": {}},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["status"] in {"queued", "running", "succeeded"}
    assert body["async"] is True
    job_id = body["id"]

    # Background thread should finish catalog import quickly
    deadline = time.time() + 30
    status = body["status"]
    while time.time() < deadline and status in {"queued", "running"}:
        time.sleep(0.2)
        status = client.get(f"/v1/admin/jobs/{job_id}", headers=AUTH_HEADERS).json()["status"]
    assert status == "succeeded"

    get_settings.cache_clear()


def test_create_job_sync_escape_hatch(client: TestClient) -> None:
    # conftest sets SYNC_JOBS=true
    r = client.post(
        "/v1/admin/jobs",
        headers=AUTH_HEADERS,
        json={"source_id": "catalog-local", "params": {}},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "succeeded"
