"""Knowledge plane: sources, catalog import, provenance, retrieve filter."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import AUTH_HEADERS


def test_health_and_seeded_sources(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "aulos-knowledge"
    sources = client.get("/v1/admin/sources", headers=AUTH_HEADERS).json()
    ids = {s["id"] for s in sources}
    assert "catalog-local" in ids
    assert "wikidata" in ids
    assert "musicbrainz" in ids


def test_unknown_source_cannot_enqueue(client: TestClient) -> None:
    r = client.post(
        "/v1/admin/jobs",
        json={"source_id": "not-registered", "params": {}},
        headers=AUTH_HEADERS,
    )
    assert r.status_code == 400


def test_catalog_import_and_provenance(client: TestClient) -> None:
    r = client.post(
        "/v1/admin/jobs",
        json={"source_id": "catalog-local", "params": {}},
        headers=AUTH_HEADERS,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "succeeded"
    stats = client.get("/v1/kb/stats").json()
    assert stats["works"] >= 5
    assert stats["documents_published"] >= 5
    docs = client.get("/v1/admin/documents", headers=AUTH_HEADERS).json()
    assert docs
    doc_id = docs[0]["id"]
    prov = client.get(f"/v1/admin/provenance/{doc_id}", headers=AUTH_HEADERS).json()
    assert prov["source"]["id"] == "catalog-local"
    assert prov["artifact"]["content_hash"]
    assert prov["job"]["id"] == body["id"]


def test_retrieve_filters_by_work_id(client: TestClient) -> None:
    client.post(
        "/v1/admin/jobs",
        json={"source_id": "catalog-local", "params": {}},
        headers=AUTH_HEADERS,
    )
    cello = client.post(
        "/v1/kb/retrieve",
        json={
            "query": "Bach cello suites unaccompanied",
            "work_id": "bach.cello-suites.bwv-1007-1012",
            "k": 6,
        },
    ).json()
    assert cello["hits"]
    for h in cello["hits"]:
        assert h["aulos_work_id"] == "bach.cello-suites.bwv-1007-1012"
        assert "Goldberg" not in (h.get("title") or "") or "988" not in (h.get("title") or "")
