"""S3: disabled source enqueue + connector failure status."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from conftest import AUTH_HEADERS


def test_disabled_source_enqueue_returns_400(client: TestClient) -> None:
    r = client.patch(
        "/v1/admin/sources/catalog-local",
        json={"enabled": False},
        headers=AUTH_HEADERS,
    )
    assert r.status_code == 200
    assert r.json()["enabled"] is False
    bad = client.post(
        "/v1/admin/jobs",
        json={"source_id": "catalog-local", "params": {}},
        headers=AUTH_HEADERS,
    )
    assert bad.status_code == 400
    assert "disabled" in bad.json()["detail"].lower()


def test_connector_failure_sets_job_failed(client: TestClient) -> None:
    with patch(
        "aulos_knowledge.jobs.run_connector",
        side_effect=RuntimeError("simulated connector boom"),
    ):
        r = client.post(
            "/v1/admin/jobs",
            json={"source_id": "catalog-local", "params": {}},
            headers=AUTH_HEADERS,
        )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "simulated connector boom" in (body.get("error") or "")
