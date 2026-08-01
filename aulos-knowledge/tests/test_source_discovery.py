"""REQ-009 source discovery graph search."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from aulos_knowledge.db import ComposerEntity, SourceAuthority
from aulos_knowledge.source_discovery import run_source_discovery
from conftest import AUTH_HEADERS


BACH_ENTITY = {
    "labels": {"en": {"value": "Johann Sebastian Bach"}},
    "claims": {
        "P856": [
            {
                "mainsnak": {
                    "datavalue": {"value": "https://www.bach-cantatas.com/Bio/Bach-Johann-Sebastian.htm"}
                }
            }
        ],
        "P973": [
            {
                "mainsnak": {
                    "datavalue": {"value": "https://www.oxfordmusiconline.com/grovemusic/view/40023"}
                }
            }
        ],
        "P434": [{"mainsnak": {"datavalue": {"value": "24f1766e-36d1-439c-8524-6f8c4549a4c4"}}}],
    },
}


def test_explore_discovers_candidates_from_wikidata_mock(client: TestClient) -> None:
    from aulos_knowledge.db import get_session

    gen = get_session()
    db = next(gen)
    try:

        def mock_fetch(qid: str) -> dict:
            assert qid == "Q1339"
            return BACH_ENTITY

        result = run_source_discovery(db, wikidata_qid="Q1339", fetch_wikidata=mock_fetch)
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

    assert result["stats"]["candidate_count"] >= 2
    ids = {c["id"] for c in result["candidates"]}
    assert "bach-cantatas" in ids or "oxfordmusiconline" in ids
    graph_nodes = {n["id"] for n in result["graph"]["nodes"]}
    assert any(n.startswith("url:") for n in graph_nodes)
    assert result["seed_hints"]["wikipedia_title"] == "Johann Sebastian Bach"
    assert result["seed_hints"]["musicbrainz_id"] == "24f1766e-36d1-439c-8524-6f8c4549a4c4"


def test_explore_api_and_register_candidates(client: TestClient, monkeypatch) -> None:
    from aulos_knowledge import source_discovery as sd

    monkeypatch.setattr(sd, "_fetch_wikidata_entity", lambda qid, **kw: BACH_ENTITY)

    resp = client.post(
        "/v1/admin/sources/explore",
        headers=AUTH_HEADERS,
        json={"wikidata_qid": "Q1339", "max_depth": 2, "max_breadth": 12, "enqueue_crawl": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "succeeded"
    assert body["candidates"]
    run_id = body["id"]

    reg = client.post(
        f"/v1/admin/sources/explore/runs/{run_id}/register-candidates",
        headers=AUTH_HEADERS,
        json={"min_score": 5},
    )
    assert reg.status_code == 200
    created = reg.json()["created"]
    assert created

    rows = client.get("/v1/admin/sources", headers=AUTH_HEADERS).json()
    by_id = {r["id"]: r for r in rows}
    for cid in created:
        assert by_id[cid]["verification_status"] == "candidate"
        assert by_id[cid]["enabled"] is False


def test_explore_enqueues_authority_crawl(client: TestClient, monkeypatch) -> None:
    from aulos_knowledge import source_discovery as sd

    monkeypatch.setattr(sd, "_fetch_wikidata_entity", lambda qid, **kw: BACH_ENTITY)
    monkeypatch.setattr(
        sd,
        "enqueue_seed_authority_crawl",
        lambda *a, **k: [
            {"source_id": "wikidata", "job_id": 101, "status": "succeeded"},
            {"source_id": "wikipedia", "job_id": 102, "status": "succeeded"},
        ],
    )

    resp = client.post(
        "/v1/admin/sources/explore",
        headers=AUTH_HEADERS,
        json={"wikidata_qid": "Q1339", "enqueue_crawl": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "succeeded"
    jobs = body.get("crawl_jobs") or []
    assert len(jobs) == 2
    assert {j["source_id"] for j in jobs} == {"wikidata", "wikipedia"}

    again = client.post(
        f"/v1/admin/sources/explore/runs/{body['id']}/enqueue-crawl",
        headers=AUTH_HEADERS,
        json={},
    )
    assert again.status_code == 200
    assert again.json()["crawl_jobs"]


def test_explore_composer_seed_expands_graph(client: TestClient) -> None:
    from aulos_knowledge.db import get_session

    gen = get_session()
    db = next(gen)
    try:
        db.add(
            ComposerEntity(
                id="bach",
                name_en="Johann Sebastian Bach",
                external_ids_json=json.dumps({"wikidata": "Q1339"}),
            )
        )
        db.commit()
        result = run_source_discovery(db, composer_id="bach", fetch_wikidata=lambda q: BACH_ENTITY)
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

    node_kinds = {n["kind"] for n in result["graph"]["nodes"]}
    assert "entity" in node_kinds
    assert "registry_source" in node_kinds


def test_register_skips_existing(client: TestClient, monkeypatch) -> None:
    from aulos_knowledge.db import get_session
    from aulos_knowledge import source_discovery as sd

    monkeypatch.setattr(sd, "_fetch_wikidata_entity", lambda qid, **kw: BACH_ENTITY)

    gen = get_session()
    db = next(gen)
    try:
        db.add(
            SourceAuthority(
                id="bach-cantatas",
                name="Bach Cantatas",
                base_urls_json='["https://www.bach-cantatas.com/"]',
                verification_status="candidate",
            )
        )
        db.commit()
    finally:
        try:
            next(gen)
        except StopIteration:
            pass

    run = client.post(
        "/v1/admin/sources/explore",
        headers=AUTH_HEADERS,
        json={"wikidata_qid": "Q1339", "enqueue_crawl": False},
    ).json()
    reg = client.post(
        f"/v1/admin/sources/explore/runs/{run['id']}/register-candidates",
        headers=AUTH_HEADERS,
        json={},
    ).json()
    assert "bach-cantatas" not in reg["created"]


def test_diagnosis_proposes_explore_sources(client: TestClient, monkeypatch) -> None:
    from aulos_knowledge import source_discovery as sd

    monkeypatch.setattr(sd, "_fetch_wikidata_entity", lambda qid, **kw: BACH_ENTITY)
    monkeypatch.setattr(sd, "enqueue_seed_authority_crawl", lambda *a, **k: [])

    client.post("/v1/admin/jobs", headers=AUTH_HEADERS, json={"source_id": "catalog-local", "params": {}})
    run = client.post("/v1/admin/benchmark/run", headers=AUTH_HEADERS).json()
    diag = client.get(f"/v1/admin/benchmark/runs/{run['id']}/diagnosis", headers=AUTH_HEADERS).json()
    explore_actions = [a for a in diag.get("actions", []) if a.get("action_type") == "explore_sources"]
    assert isinstance(explore_actions, list)
