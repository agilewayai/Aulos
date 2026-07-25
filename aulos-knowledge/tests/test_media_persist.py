"""Media asset persistence under durable artifact root."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from aulos_knowledge.artifacts import write_media_file
from aulos_knowledge.media_fetch import _host_allowed


def test_host_allowlist() -> None:
    assert _host_allowed("https://upload.wikimedia.org/wikipedia/commons/a/a0/x.jpg")
    assert _host_allowed("https://coverartarchive.org/release-group/x/front")
    assert not _host_allowed("https://evil.example/steal.bin")


def test_write_media_file_durable_layout(tmp_path: Path) -> None:
    digest, rel, abs_path = write_media_file(
        root=tmp_path,
        kind="image",
        source_id="wikidata",
        entity_id="johann-sebastian-bach",
        payload=b"fake-image-bytes",
        filename="Bach.jpg",
    )
    assert digest
    assert rel.startswith("media/image/wikidata/")
    assert abs_path.is_file()
    assert abs_path.read_bytes() == b"fake-image-bytes"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "knowledge.db"
    art = tmp_path / "persist" / "artifacts"
    art.mkdir(parents=True)
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


def test_media_list_endpoint_empty(client: TestClient) -> None:
    r = client.get("/v1/admin/media")
    assert r.status_code == 200
    assert r.json() == []
    stats = client.get("/v1/kb/stats").json()
    assert stats["media_assets"] == 0
