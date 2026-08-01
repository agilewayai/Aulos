"""REQ-012 — multi-source merge + bilingual card (offline mocks)."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

from conftest import AUTH_HEADERS


class _FakeResp:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> Any:
        return self._payload


def test_merge_fragments_field_precedence() -> None:
    from aulos_knowledge.person_aggregate import merge_fragments

    card = merge_fragments(
        name="Mauro Giuliani",
        kind="composer",
        fragments=[
            {
                "source_id": "discogs",
                "display_name_en": "Mauro Giuliani",
                "summary_en": "Italian guitarist and composer from Discogs profile text that is long enough.",
                "summary_en_origin": "discogs",
                "portrait_url": "https://example.test/discogs.jpg",
                "external_ids": {"discogs": "1"},
                "aliases": ["Giuliani"],
                "provenance": [{"source_id": "discogs", "url": "https://www.discogs.com/artist/1"}],
                "fields": ["summary_en", "portrait_url"],
                "role": "catalog_profile",
            },
            {
                "source_id": "wikidata",
                "display_name_en": "Mauro Giuliani",
                "display_name_zh": "毛罗·朱利亚尼",
                "summary_en": "Italian guitarist",
                "summary_zh": "意大利吉他演奏家",
                "summary_en_origin": "wikidata",
                "summary_zh_origin": "wikidata",
                "lifespan": "1781–1829",
                "external_ids": {"wikidata": "Q379560", "zhwiki": "毛罗·朱利亚尼"},
                "aliases": [],
                "provenance": [{"source_id": "wikidata", "url": "https://www.wikidata.org/wiki/Q379560"}],
                "fields": ["lifespan", "names"],
                "role": "identity",
            },
            {
                "source_id": "wikipedia",
                "lang": "en",
                "summary_en": "Mauro Giuseppe Sergio Pantaleo Giuliani was an Italian guitarist, cellist, singer, and composer.",
                "summary_en_origin": "wikipedia",
                "portrait_url": "https://example.test/wiki.jpg",
                "external_ids": {"enwiki": "Mauro Giuliani"},
                "aliases": [],
                "provenance": [{"source_id": "wikipedia", "url": "https://en.wikipedia.org/wiki/Mauro_Giuliani"}],
                "fields": ["summary_en"],
                "role": "encyclopedia",
            },
            {
                "source_id": "wikipedia",
                "lang": "zh",
                "display_name_zh": "毛罗·朱利亚尼",
                "summary_zh": "毛罗·朱利亚尼是意大利古典吉他演奏家、作曲家。",
                "summary_zh_origin": "wikipedia",
                "external_ids": {"zhwiki": "毛罗·朱利亚尼"},
                "aliases": [],
                "provenance": [{"source_id": "wikipedia", "url": "https://zh.wikipedia.org/wiki/毛罗·朱利亚尼"}],
                "fields": ["summary_zh"],
                "role": "encyclopedia",
            },
        ],
    )
    assert card["source"] == "aggregated"
    assert card["lifespan"] == "1781–1829"  # wikidata
    assert card["summary_en_origin"] == "wikipedia"
    assert "guitarist, cellist" in card["summary_en"]
    assert card["summary_zh_origin"] == "wikipedia"
    assert "意大利" in card["summary_zh"]
    assert card["portrait_url"] == "https://example.test/discogs.jpg"  # discogs wins portrait
    assert card["external_ids"]["wikidata"] == "Q379560"
    assert card["external_ids"]["discogs"] == "1"
    assert card["display_name_zh"] == "毛罗·朱利亚尼"
    assert any(s["source_id"] == "discogs" for s in card["sources"])


def test_aggregate_endpoint_with_discogs_fragment(client, monkeypatch) -> None:
    search_payload = {
        "search": [
            {
                "id": "Q379560",
                "label": "Mauro Giuliani",
                "description": "Italian guitarist and composer",
                "match": {"type": "label", "language": "en", "text": "Mauro Giuliani"},
            }
        ]
    }
    entity_payload = {
        "entities": {
            "Q379560": {
                "labels": {
                    "en": {"value": "Mauro Giuliani"},
                    "zh": {"value": "毛罗·朱利亚尼"},
                },
                "descriptions": {
                    "en": {"value": "Italian guitarist and composer"},
                    "zh": {"value": "意大利吉他演奏家、作曲家"},
                },
                "sitelinks": {
                    "enwiki": {"title": "Mauro Giuliani"},
                    "zhwiki": {"title": "毛罗·朱利亚尼"},
                },
                "claims": {
                    "P569": [
                        {
                            "mainsnak": {
                                "datavalue": {
                                    "value": {"time": "+1781-07-27T00:00:00Z"},
                                    "type": "time",
                                }
                            }
                        }
                    ],
                    "P570": [
                        {
                            "mainsnak": {
                                "datavalue": {
                                    "value": {"time": "+1829-05-08T00:00:00Z"},
                                    "type": "time",
                                }
                            }
                        }
                    ],
                },
            }
        }
    }
    wiki_en = {
        "title": "Mauro Giuliani",
        "extract": "Mauro Giuseppe Sergio Pantaleo Giuliani was an Italian guitarist, cellist, singer, and composer.",
        "thumbnail": {"source": "https://example.test/wiki.jpg"},
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Mauro_Giuliani"}},
    }
    wiki_zh = {
        "title": "毛罗·朱利亚尼",
        "extract": "毛罗·朱利亚尼是意大利古典吉他演奏家、作曲家。",
        "content_urls": {"desktop": {"page": "https://zh.wikipedia.org/wiki/毛罗·朱利亚尼"}},
    }

    def fake_get(url: str, params: dict | None = None, **_kwargs):  # noqa: ANN001
        u = str(url)
        if params and params.get("action") == "wbsearchentities":
            return _FakeResp(search_payload)
        if "EntityData" in u:
            return _FakeResp(entity_payload)
        if "zh.wikipedia.org" in u:
            return _FakeResp(wiki_zh)
        if "en.wikipedia.org" in u:
            return _FakeResp(wiki_en)
        return _FakeResp({}, status_code=404)

    fake_client = MagicMock()
    fake_client.get.side_effect = fake_get

    import aulos_knowledge.person_aggregate as pa

    monkeypatch.setattr(pa.httpx, "Client", lambda **_k: fake_client)

    resp = client.post(
        "/v1/kb/entities/person/aggregate",
        json={
            "name": "Mauro Giuliani",
            "kind": "composer",
            "fragments": [
                {
                    "source_id": "discogs",
                    "authority": "discogs",
                    "display_name": "Mauro Giuliani",
                    "summary": "Discogs profile: Italian guitarist and composer (1781–1829).",
                    "portrait_url": "https://example.test/discogs.jpg",
                    "external_ids": {"discogs": "872577"},
                    "provenance": [{"source_id": "discogs", "url": "https://www.discogs.com/artist/872577"}],
                }
            ],
            "fetch_remote": True,
            "persist": True,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["source"] == "aggregated"
    assert data["lifespan"].startswith("1781")
    assert data["summary_en_origin"] in {"wikipedia", "discogs"}
    assert data["summary_zh"]
    assert data["display_name_zh"]
    assert data["external_ids"].get("discogs") == "872577"
    assert data["external_ids"].get("wikidata") == "Q379560"
    assert data["portrait_url"] == "https://example.test/discogs.jpg"

    # Second local resolve should be knowledge / bilingual
    again = client.post(
        "/v1/kb/entities/person/resolve",
        json={"name": "Mauro Giuliani", "kind": "composer", "enrich": False},
    )
    assert again.status_code == 200
    body = again.json()
    assert body.get("summary_en") or body.get("summary")
    assert body.get("person_id")


def test_persist_famous_locks_wikidata_qid(client) -> None:
    from aulos_knowledge.db import ComposerEntity, SessionLocal
    from aulos_knowledge.person_aggregate import persist_bilingual_card

    db = SessionLocal()
    try:
        card = {
            "source": "aggregated",
            "person_id": "wolfgang-amadeus-mozart",
            "name": "Wolfgang Amadeus Mozart",
            "kind": "composer",
            "display_name_en": "Franz Xaver Wolfgang Mozart",
            "display_name_zh": "弗朗兹",
            "summary_en": "Wrong relative biography that should not steal the famous QID.",
            "summary_zh": "",
            "lifespan": "1791–1844",
            "era": "Classical",
            "external_ids": {"wikidata": "Q156023", "discogs": "95546"},
            "aliases": [],
            "sources": [],
        }
        persist_bilingual_card(db, card)
        db.commit()
        row = db.get(ComposerEntity, "wolfgang-amadeus-mozart")
        assert row is not None
        ext = json.loads(row.external_ids_json or "{}")
        assert ext.get("wikidata") == "Q254"
        assert row.name_en == "Wolfgang Amadeus Mozart"
    finally:
        db.close()
