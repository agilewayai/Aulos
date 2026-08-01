"""API person entity — multi-source aggregate orchestration (REQ-012)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "entities.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("AULOS_KNOWLEDGE_PLANE_ENABLED", "true")
    monkeypatch.setenv("AULOS_DISCOGS_TOKEN", "test-discogs-token")

    from aulos_api.config import get_settings
    from aulos_api.db import session as db_session
    from aulos_api.services.mailgun import clear_fake_mailbox

    get_settings.cache_clear()
    db_session.reset_engine()
    clear_fake_mailbox()

    from aulos_api.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    clear_fake_mailbox()
    get_settings.cache_clear()
    db_session.reset_engine()


def test_entities_person_returns_bilingual_local(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    card: dict[str, Any] = {
        "name": "Bach",
        "kind": "composer",
        "person_id": "js-bach",
        "display_name": "约翰·塞巴斯蒂安·巴赫",
        "display_name_en": "Johann Sebastian Bach",
        "display_name_zh": "约翰·塞巴斯蒂安·巴赫",
        "summary": "巴洛克时期德国作曲家。",
        "summary_en": "German Baroque composer and musician of the late Baroque period.",
        "summary_zh": "巴洛克时期德国作曲家与音乐家，晚期巴洛克代表人物之一。",
        "summary_en_origin": "wikipedia",
        "summary_zh_origin": "wikipedia",
        "lifespan": "1685–1750",
        "era": "Baroque",
        "portrait_url": "",
        "external_ids": {"wikidata": "Q1339"},
        "snippets": [],
        "sources": [],
        "source": "knowledge",
        "matched": True,
        "locale_default": "zh",
        "provenance": [],
    }

    async def fake_proxy(method: str, path: str, **kwargs):  # noqa: ANN003
        assert path == "/v1/kb/entities/person/resolve"
        return 200, card, {"content-type": "application/json"}

    monkeypatch.setattr(
        "aulos_api.routes.entities.proxy_knowledge",
        AsyncMock(side_effect=fake_proxy),
    )

    resp = client.get("/v1/entities/person", params={"name": "Bach", "kind": "composer", "locale": "zh"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["person_id"] == "js-bach"
    assert data["summary_zh"]
    assert data["summary_en"]
    assert "巴赫" in data["display_name"]


def test_entities_person_aggregates_discogs_and_remote(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    unresolved = {
        "name": "Mauro Giuliani",
        "kind": "composer",
        "person_id": "",
        "display_name": "Mauro Giuliani",
        "summary": "",
        "summary_en": "",
        "summary_zh": "",
        "source": "unresolved",
        "matched": False,
        "snippets": [],
        "provenance": [],
        "external_ids": {},
    }
    aggregated = {
        "name": "Mauro Giuliani",
        "kind": "composer",
        "person_id": "mauro-giuliani",
        "display_name": "毛罗·朱利亚尼",
        "display_name_en": "Mauro Giuliani",
        "display_name_zh": "毛罗·朱利亚尼",
        "summary": "毛罗·朱利亚尼是意大利古典吉他演奏家、作曲家。",
        "summary_en": "Mauro Giuliani was an Italian guitarist, cellist, singer, and composer of the early nineteenth century.",
        "summary_zh": "毛罗·朱利亚尼是意大利古典吉他演奏家、作曲家。",
        "summary_en_origin": "wikipedia",
        "summary_zh_origin": "wikipedia",
        "lifespan": "1781–1829",
        "portrait_url": "https://example.test/d.jpg",
        "external_ids": {"discogs": "999", "wikidata": "Q379560"},
        "sources": [
            {"source_id": "discogs", "role": "catalog_profile", "url": "https://www.discogs.com/artist/999"},
            {"source_id": "wikidata", "role": "identity", "url": "https://www.wikidata.org/wiki/Q379560"},
            {"source_id": "wikipedia", "role": "encyclopedia", "url": "", "lang": "en"},
        ],
        "source": "aggregated",
        "matched": True,
        "locale_default": "zh",
        "snippets": [],
        "provenance": [],
    }
    calls: list[str] = []

    async def fake_proxy(method: str, path: str, **kwargs):  # noqa: ANN003
        calls.append(path)
        if path.endswith("/resolve"):
            return 200, unresolved, {"content-type": "application/json"}
        if path.endswith("/aggregate"):
            body = kwargs.get("json_body") or {}
            assert body.get("fragments")
            assert body["fragments"][0].get("source_id") == "discogs"
            return 200, aggregated, {"content-type": "application/json"}
        return 404, {"detail": "no"}, {}

    monkeypatch.setattr(
        "aulos_api.routes.entities.proxy_knowledge",
        AsyncMock(side_effect=fake_proxy),
    )
    monkeypatch.setattr(
        "aulos_api.services.discogs.resolve_discogs_artist_card",
        lambda name, kind="person", **_k: {
            "name": name,
            "kind": kind,
            "display_name": "Mauro Giuliani",
            "summary": "Italian guitarist and composer, active early 19th century.",
            "portrait_url": "https://example.test/d.jpg",
            "external_ids": {"discogs": "999"},
            "provenance": [{"source_id": "discogs", "url": "https://www.discogs.com/artist/999"}],
            "source": "enriched",
            "authority": "discogs",
        },
    )

    resp = client.get("/v1/entities/person", params={"name": "Mauro Giuliani", "kind": "composer", "locale": "zh"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["source"] == "aggregated"
    assert data["external_ids"]["discogs"] == "999"
    assert data["external_ids"]["wikidata"] == "Q379560"
    assert data["summary_zh"]
    assert data["summary_en"]
    assert "/v1/kb/entities/person/aggregate" in calls
