"""Explore seed catalog — A–Z composers + famous badges (META-001 §3.4)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aulos_knowledge.famous_composers import FAMOUS_COMPOSERS
from conftest import AUTH_HEADERS


def test_explore_seeds_az_and_famous(client: TestClient) -> None:
    resp = client.get("/v1/admin/sources/explore/seeds", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["stats"]["famous"] >= 10
    assert body["letters"]
    assert "B" in body["letters"]  # Bach
    ids = {s["id"] for s in body["seeds"]}
    assert "johann-sebastian-bach" in ids
    bach = next(s for s in body["seeds"] if s["id"] == "johann-sebastian-bach")
    assert bach["famous"] is True
    assert bach["featured"] is True
    assert bach["wikidata_qid"] == "Q1339"
    assert bach["short_name"] == "Bach"
    assert body["featured"]
    assert body["featured"][0]["short_name"]


def test_famous_roster_covers_many_letters() -> None:
    letters = {c["letter"] for c in FAMOUS_COMPOSERS}
    assert len(letters) >= 15
    assert "B" in letters and "M" in letters and "V" in letters


def test_prepare_seeds_endpoint(client: TestClient, monkeypatch) -> None:
    from aulos_knowledge import routes as routes_mod

    monkeypatch.setattr(
        routes_mod,
        "prepare_famous_seed_crawls",
        lambda db, **kw: {"ok": True, "jobs": [{"job_id": 1}], "enqueued": 1, "composers": 1},
    )
    resp = client.post(
        "/v1/admin/sources/explore/prepare-seeds",
        headers=AUTH_HEADERS,
        json={"limit": 2, "sync": False},
    )
    assert resp.status_code == 200
    assert resp.json()["enqueued"] == 1
