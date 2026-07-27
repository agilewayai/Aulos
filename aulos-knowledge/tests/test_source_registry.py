"""REQ-008 Authority Source Registry gates."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aulos_knowledge.db import SourceAuthority
from aulos_knowledge.fetch_policy import assert_url_allowed, url_allowed
from aulos_knowledge.publish_policy import document_status_for_source
from conftest import AUTH_HEADERS


def test_registry_seeds_verified_sources(client: TestClient) -> None:
    rows = client.get("/v1/admin/sources", headers=AUTH_HEADERS).json()
    by_id = {r["id"]: r for r in rows}
    assert "catalog-local" in by_id
    assert by_id["catalog-local"]["verification_status"] == "verified"
    assert by_id["catalog-local"]["origin_class"] == "identity_seed"
    assert by_id["wikidata"]["verification_status"] == "verified"
    assert by_id["musicbrainz"]["enabled"] is True
    # S2/S3 connectors registered + verified
    for sid in ("wikipedia", "imslp", "rism"):
        assert by_id[sid]["verification_status"] == "verified"
        assert by_id[sid]["enabled"] is True
        assert by_id[sid]["connector_registered"] is True
    # Grove remains candidate without connector
    assert by_id["grove"]["verification_status"] == "candidate"
    assert by_id["grove"]["connector_registered"] is False


def test_unverified_source_cannot_enqueue(client: TestClient) -> None:
    # register candidate with fake connector name that isn't registered
    created = client.post(
        "/v1/admin/sources",
        headers=AUTH_HEADERS,
        json={
            "id": "test-candidate",
            "name": "Test",
            "connector": "wikidata",
            "base_urls": ["https://www.wikidata.org/"],
            "enabled": True,
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["verification_status"] == "candidate"
    assert body["enabled"] is False  # not verified → forced off on create when we set enabled

    bad = client.post(
        "/v1/admin/jobs",
        headers=AUTH_HEADERS,
        json={"source_id": "test-candidate", "params": {"qids": ["Q1339"]}},
    )
    assert bad.status_code == 400
    assert "not verified" in bad.json()["detail"].lower() or "verified" in bad.json()["detail"].lower()


def test_verify_then_enqueue_catalog(client: TestClient) -> None:
    job = client.post(
        "/v1/admin/jobs",
        headers=AUTH_HEADERS,
        json={"source_id": "catalog-local", "params": {}},
    )
    assert job.status_code == 200
    assert job.json()["status"] == "succeeded"
    docs = client.get("/v1/admin/documents", headers=AUTH_HEADERS).json()
    assert docs
    # tier S verified identity_seed → auto-published
    assert any(d["status"] == "published" for d in docs)


def test_reject_and_suspend(client: TestClient) -> None:
    client.post(
        "/v1/admin/sources",
        headers=AUTH_HEADERS,
        json={"id": "tmp-src", "name": "Tmp", "connector": "wikidata", "base_urls": ["https://www.wikidata.org/"]},
    )
    v = client.post("/v1/admin/sources/tmp-src/verify", headers=AUTH_HEADERS, json={"by": "tester"})
    assert v.status_code == 200
    assert v.json()["verification_status"] == "verified"
    assert v.json()["verified_by"] == "tester"

    # enable after verify
    en = client.patch("/v1/admin/sources/tmp-src", headers=AUTH_HEADERS, json={"enabled": True})
    assert en.status_code == 200
    assert en.json()["enabled"] is True

    sus = client.post("/v1/admin/sources/tmp-src/suspend", headers=AUTH_HEADERS)
    assert sus.status_code == 200
    assert sus.json()["verification_status"] == "suspended"
    assert sus.json()["enabled"] is False

    client.post(
        "/v1/admin/sources",
        headers=AUTH_HEADERS,
        json={"id": "tmp-rej", "name": "Rej", "connector": "wikidata", "base_urls": ["https://www.wikidata.org/"]},
    )
    rej = client.post("/v1/admin/sources/tmp-rej/reject", headers=AUTH_HEADERS)
    assert rej.json()["verification_status"] == "rejected"


def test_fetch_policy_url_allowlist() -> None:
    src = SourceAuthority(
        id="wikidata",
        base_urls_json='["https://www.wikidata.org/"]',
        allowed_path_prefixes_json="[]",
    )
    assert url_allowed(src, "https://www.wikidata.org/wiki/Special:EntityData/Q1.json")
    assert not url_allowed(src, "https://evil.example/wiki/Q1")
    try:
        assert_url_allowed(src, "https://evil.example/")
        raise AssertionError("expected FetchPolicyError")
    except Exception as exc:
        assert "not allowed" in str(exc)


def test_publish_policy_quarantine_for_unverified() -> None:
    src = SourceAuthority(id="x", tier="S", verification_status="candidate", origin_class="encyclopedia")
    assert document_status_for_source(src) == "quarantine"
    src.verification_status = "verified"
    assert document_status_for_source(src) == "published"
    src.origin_class = "media"
    assert document_status_for_source(src) == "quarantine"
    # tier A encyclopedia stays quarantine even when verified (Wikipedia)
    src.tier = "A"
    src.origin_class = "encyclopedia"
    assert document_status_for_source(src) == "quarantine"


def test_cannot_verify_without_connector(client: TestClient) -> None:
    client.post(
        "/v1/admin/sources",
        headers=AUTH_HEADERS,
        json={
            "id": "no-conn",
            "name": "No connector",
            "connector": "",
            "base_urls": ["https://example.org/"],
        },
    )
    v = client.post("/v1/admin/sources/no-conn/verify", headers=AUTH_HEADERS, json={})
    assert v.status_code == 400
    assert "connector" in v.json()["detail"].lower()
