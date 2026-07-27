"""Audit/proofread document APIs used by OPS Knowledge tab."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import AUTH_HEADERS


def test_document_detail_and_publish_restore(client: TestClient) -> None:
    job = client.post(
        "/v1/admin/jobs",
        json={"source_id": "catalog-local", "params": {}},
        headers=AUTH_HEADERS,
    ).json()
    assert job["status"] == "succeeded"
    docs = client.get("/v1/admin/documents", headers=AUTH_HEADERS).json()
    assert docs
    doc_id = docs[0]["id"]
    detail = client.get(f"/v1/admin/documents/{doc_id}", headers=AUTH_HEADERS).json()
    assert detail["body"]
    assert "body_preview" in detail
    q = client.post(f"/v1/admin/documents/{doc_id}/quarantine", headers=AUTH_HEADERS)
    assert q.status_code == 200
    assert q.json()["status"] == "quarantine"
    p = client.post(f"/v1/admin/documents/{doc_id}/publish", headers=AUTH_HEADERS)
    assert p.status_code == 200
    assert p.json()["status"] == "published"
    composers = client.get("/v1/admin/composers", headers=AUTH_HEADERS).json()
    assert isinstance(composers, list)
    filtered = client.get(
        "/v1/admin/documents",
        params={"status": "published", "q": "Bach"},
        headers=AUTH_HEADERS,
    ).json()
    assert isinstance(filtered, list)
