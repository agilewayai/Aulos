"""S2/S3 connectors (Wikipedia / IMSLP / RISM) with mocked HTTP."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from conftest import AUTH_HEADERS


def _wiki_payload(title: str = "Johann Sebastian Bach", extract: str = "German composer.") -> dict:
    return {
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "title": title,
                    "extract": extract,
                }
            }
        }
    }


def _mock_response(payload: dict, content_type: str = "application/json") -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    resp.headers = {"content-type": content_type}
    return resp


def test_wikipedia_connector_quarantines_and_chunks(client: TestClient) -> None:
    with patch("aulos_knowledge.connectors.wikipedia.httpx.Client") as client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.get.return_value = _mock_response(_wiki_payload())
        client_cls.return_value = mock_client

        job = client.post(
            "/v1/admin/jobs",
            headers=AUTH_HEADERS,
            json={
                "source_id": "wikipedia",
                "params": {
                    "title": "Johann Sebastian Bach",
                    "langs": ["en"],
                    "composer_id": "johann-sebastian-bach",
                },
            },
        )
    assert job.status_code == 200, job.text
    assert job.json()["status"] == "succeeded"

    docs = client.get(
        "/v1/admin/documents",
        headers=AUTH_HEADERS,
        params={"source_id": "wikipedia"},
    ).json()
    assert docs
    doc = docs[0]
    assert doc["status"] == "quarantine"  # tier A → quarantine
    assert "CC BY-SA" in (doc.get("body_preview") or "") or doc["license_class"] == "CC-BY-SA"

    detail = client.get(f"/v1/admin/documents/{doc['id']}", headers=AUTH_HEADERS).json()
    assert detail["chunks"]
    chunk_id = detail["chunks"][0]["id"]

    prov = client.get(f"/v1/admin/provenance/{doc['id']}", headers=AUTH_HEADERS).json()
    assert prov["source"]["id"] == "wikipedia"
    assert prov["chunks"]
    assert prov["artifact"]["content_hash"]

    chunk_prov = client.get(f"/v1/admin/chunks/{chunk_id}/provenance", headers=AUTH_HEADERS).json()
    assert chunk_prov["chunk"]["id"] == chunk_id
    assert chunk_prov["chunk"]["section"] == "wikipedia-en"
    assert chunk_prov["document"]["id"] == doc["id"]
    assert chunk_prov["source"]["id"] == "wikipedia"
    assert "German composer" in chunk_prov["chunk"]["text"]


def test_imslp_connector(client: TestClient) -> None:
    with patch("aulos_knowledge.connectors.imslp.httpx.Client") as client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.get.return_value = _mock_response(
            _wiki_payload(title="Category:Bach, Johann Sebastian", extract="Works by Bach.")
        )
        client_cls.return_value = mock_client

        job = client.post(
            "/v1/admin/jobs",
            headers=AUTH_HEADERS,
            json={
                "source_id": "imslp",
                "params": {"title": "Category:Bach, Johann Sebastian", "composer_id": "johann-sebastian-bach"},
            },
        )
    assert job.status_code == 200, job.text
    assert job.json()["status"] == "succeeded"
    docs = client.get("/v1/admin/documents", headers=AUTH_HEADERS, params={"source_id": "imslp"}).json()
    assert docs
    assert docs[0]["status"] == "quarantine"
    assert docs[0]["extractor_version"].startswith("imslp/")


def test_rism_connector(client: TestClient) -> None:
    payload = {
        "items": [
            {"id": "people/30000285", "label": "Bach, Johann Sebastian", "dating": "1685-1750"},
            {"id": "people/30000286", "label": "Bach, Carl Philipp Emanuel"},
        ]
    }
    with patch("aulos_knowledge.connectors.rism.httpx.Client") as client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.get.return_value = _mock_response(payload, content_type="application/ld+json")
        client_cls.return_value = mock_client

        job = client.post(
            "/v1/admin/jobs",
            headers=AUTH_HEADERS,
            json={"source_id": "rism", "params": {"q": "Bach", "mode": "people", "limit": 2}},
        )
    assert job.status_code == 200, job.text
    assert job.json()["status"] == "succeeded"
    docs = client.get("/v1/admin/documents", headers=AUTH_HEADERS, params={"source_id": "rism"}).json()
    assert len(docs) >= 2
    assert all(d["status"] == "quarantine" for d in docs)
    detail = client.get(f"/v1/admin/documents/{docs[0]['id']}", headers=AUTH_HEADERS).json()
    assert detail["chunks"]
    assert detail["chunks"][0]["section"] == "rism"


def test_chunk_provenance_404(client: TestClient) -> None:
    r = client.get("/v1/admin/chunks/999999/provenance", headers=AUTH_HEADERS)
    assert r.status_code == 404
