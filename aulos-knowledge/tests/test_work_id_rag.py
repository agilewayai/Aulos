"""S2: knowledge plane retrieve must honor Catalog work_id."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import AUTH_HEADERS


def test_cello_work_id_excludes_goldberg_docs(client: TestClient) -> None:
    client.post(
        "/v1/admin/jobs",
        json={"source_id": "catalog-local", "params": {}},
        headers=AUTH_HEADERS,
    )
    cello = client.post(
        "/v1/kb/retrieve",
        json={
            "query": "Bach BWV cello",
            "work_id": "bach.cello-suites.bwv-1007-1012",
            "k": 6,
        },
    ).json()
    assert cello["hits"]
    for h in cello["hits"]:
        assert h["aulos_work_id"] == "bach.cello-suites.bwv-1007-1012"
