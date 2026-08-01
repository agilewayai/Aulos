"""KB-BENCH-001 — benchmark API and scoring."""

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


def test_benchmark_suite_metadata(client: TestClient) -> None:
    suite = client.get("/v1/kb/benchmark/suite").json()
    assert suite["case_count"] >= 3
    assert suite["required_case_count"] >= 2
    ids = {c["id"] for c in suite["cases"]}
    assert "cello-suites-filter" in ids


def test_benchmark_run_persists_report(client: TestClient) -> None:
    _seed_corpus(client)
    run = client.post("/v1/admin/benchmark/run", headers=AUTH_HEADERS).json()
    assert run["id"] >= 1
    assert 0 <= run["overall_score"] <= 100
    assert run["grade"] in {"A", "B", "C", "D", "F"}
    assert "dimensions" in run
    assert "retrieval" in run["dimensions"]
    assert run["dimensions"]["retrieval"]["total"] >= 2
    assert run["markdown"].startswith("# Knowledge benchmark report")
    assert "cello-suites-filter" in run["markdown"]

    runs = client.get("/v1/admin/benchmark/runs", headers=AUTH_HEADERS).json()
    assert runs
    assert runs[0]["id"] == run["id"]

    detail = client.get(f"/v1/admin/benchmark/runs/{run['id']}", headers=AUTH_HEADERS).json()
    assert detail["overall_score"] == run["overall_score"]
    assert detail["dimensions"]["corpus"]["published"] >= 5


def test_benchmark_requires_admin(client: TestClient) -> None:
    r = client.post("/v1/admin/benchmark/run")
    assert r.status_code == 401


def test_benchmark_async_returns_202(client: TestClient, monkeypatch) -> None:
    _seed_corpus(client)
    monkeypatch.setenv("AULOS_KNOWLEDGE_SYNC_JOBS", "false")
    from aulos_knowledge.config import get_settings

    get_settings.cache_clear()
    r = client.post("/v1/admin/benchmark/run?async=true", headers=AUTH_HEADERS)
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "queued"
    assert body["id"] >= 1
    assert body.get("task_type") == "knowledge.benchmark"

    import time

    deadline = time.time() + 30
    detail = body
    while time.time() < deadline:
        detail = client.get(f"/v1/admin/benchmark/runs/{body['id']}", headers=AUTH_HEADERS).json()
        if detail["status"] in ("succeeded", "failed"):
            break
        time.sleep(0.2)
    assert detail["status"] == "succeeded"
    assert detail.get("overall_score") is not None
    get_settings.cache_clear()


def test_benchmark_dashboard_report(client: TestClient) -> None:
    _seed_corpus(client)
    client.post("/v1/admin/benchmark/run", headers=AUTH_HEADERS)
    dash = client.get("/v1/kb/benchmark/dashboard").json()
    assert dash["health_status"] in {"healthy", "watch", "critical", "no_data"}
    assert dash["latest_run"]
    assert len(dash["dimensions"]) == 5
    assert dash["markdown_summary"].startswith("# Knowledge performance dashboard")
    assert isinstance(dash["insights"], list) and dash["insights"]
