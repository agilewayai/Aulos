"""KB-DIAG-001 / KB-IMPROVE-001 tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import AUTH_HEADERS


def _seed_corpus(client: TestClient) -> None:
    r = client.post(
        "/v1/admin/jobs",
        json={"source_id": "catalog-local", "params": {}},
        headers=AUTH_HEADERS,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "succeeded"


def _stub_discovery(monkeypatch) -> None:
    """Avoid live Wikidata/crawl during diagnosis improve actions."""
    from aulos_knowledge import source_discovery as sd

    monkeypatch.setattr(
        sd,
        "_fetch_wikidata_entity",
        lambda qid, **kw: {
            "labels": {"en": {"value": "Johann Sebastian Bach"}},
            "claims": {},
        },
    )
    monkeypatch.setattr(sd, "enqueue_seed_authority_crawl", lambda *a, **k: [])


def test_diagnosis_after_benchmark(client: TestClient) -> None:
    _seed_corpus(client)
    run = client.post("/v1/admin/benchmark/run", headers=AUTH_HEADERS).json()
    assert run["status"] == "succeeded"
    run_id = run["id"]

    diag = client.get(f"/v1/admin/benchmark/runs/{run_id}/diagnosis", headers=AUTH_HEADERS).json()
    assert diag["benchmark_run_id"] == run_id
    assert diag.get("items")
    assert "diagnosis_id" in diag
    assert isinstance(diag.get("actions"), list)

    engineering = diag.get("engineering_tasks") or []
    # may be empty on healthy corpus
    assert isinstance(engineering, list)
    assert diag.get("markdown", "").startswith("# KB-DIAG-001")


def test_execute_safe_actions_and_improve_cycle(client: TestClient, monkeypatch) -> None:
    _stub_discovery(monkeypatch)
    _seed_corpus(client)
    run = client.post("/v1/admin/benchmark/run", headers=AUTH_HEADERS).json()
    run_id = run["id"]
    diag = client.get(f"/v1/admin/benchmark/runs/{run_id}/diagnosis", headers=AUTH_HEADERS).json()
    diagnosis_id = diag["diagnosis_id"]

    safe = [a for a in diag.get("actions", []) if a.get("auto_safe")]
    if safe:
        executed = client.post(
            f"/v1/admin/improvements/execute-safe?diagnosis_id={diagnosis_id}",
            headers=AUTH_HEADERS,
        ).json()
        assert isinstance(executed, list)

    cycle = client.post(
        f"/v1/admin/improve/cycle?benchmark_run_id={run_id}",
        headers=AUTH_HEADERS,
    ).json()
    assert cycle["benchmark_run_id_before"] == run_id
    assert cycle["benchmark_run_id_after"] >= run_id
    assert "score_before" in cycle


def test_diagnosis_can_propose_explore_sources(client: TestClient) -> None:
    _seed_corpus(client)
    run = client.post("/v1/admin/benchmark/run", headers=AUTH_HEADERS).json()
    diag = client.get(f"/v1/admin/benchmark/runs/{run['id']}/diagnosis", headers=AUTH_HEADERS).json()
    types = {a.get("action_type") for a in diag.get("actions", [])}
    # explore_sources appears when corpus/registry/retrieval gaps exist
    assert "explore_sources" in types or "crawl_authority_bundle" in types or "verify_sources" in types
