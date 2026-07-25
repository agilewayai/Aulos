"""S2: knowledge plane retrieve must honor Catalog work_id."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def knowledge_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "knowledge.db"
    art = tmp_path / "artifacts"
    art.mkdir()
    monkeypatch.setenv("AULOS_KNOWLEDGE_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_KNOWLEDGE_ARTIFACT_ROOT", str(art))
    monkeypatch.setenv("AULOS_KNOWLEDGE_SYNC_JOBS", "true")
    from aulos_knowledge.config import get_settings

    get_settings.cache_clear()
    from aulos_knowledge.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def test_cello_work_id_excludes_goldberg_docs(knowledge_client: TestClient) -> None:
    knowledge_client.post("/v1/admin/jobs", json={"source_id": "catalog-local", "params": {}})
    cello = knowledge_client.post(
        "/v1/kb/retrieve",
        json={
            "query": "Bach BWV cello",
            "work_id": "bach.cello-suites.bwv-1007-1012",
            "k": 10,
        },
    ).json()
    assert cello["hits"]
    for h in cello["hits"]:
        assert h.get("aulos_work_id") == "bach.cello-suites.bwv-1007-1012"
        title = (h.get("title") or "").lower()
        assert "goldberg" not in title
        assert "988" not in title


def test_resolve_identity_work_id_for_rag_helper() -> None:
    from aulos_skills.identity import resolve_identity

    ident = resolve_identity("我准备开始欣赏巴赫的大提琴无伴奏组曲")
    assert ident.work_id == "bach.cello-suites.bwv-1007-1012"
