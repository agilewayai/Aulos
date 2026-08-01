"""REQ-011 — person entity resolve: KB first, then mocked Wikidata/Wikipedia enrich."""

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


def test_resolve_local_composer_no_network(client) -> None:
    from aulos_knowledge.db import ComposerEntity, SessionLocal

    assert SessionLocal is not None
    db = SessionLocal()
    try:
        db.add(
            ComposerEntity(
                id="js-bach",
                name_en="Johann Sebastian Bach",
                name_zh="巴赫",
                aliases_json=json.dumps(["Bach"]),
                lifespan="1685–1750",
                era="Baroque",
                summary_en="German Baroque composer.",
                summary_zh="巴洛克时期德国作曲家。",
            )
        )
        db.commit()
    finally:
        db.close()

    resp = client.post(
        "/v1/kb/entities/person/resolve",
        json={"name": "Bach", "kind": "composer", "enrich": False},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["source"] == "knowledge"
    assert data["person_id"] == "js-bach"
    assert "German" in data["summary"] or "巴洛克" in data["summary"]


def test_resolve_enriches_and_persists(client, monkeypatch) -> None:
    search_payload = {
        "search": [
            {
                "id": "Q1339",
                "label": "Johann Sebastian Bach",
                "description": "German composer and musician",
            }
        ]
    }
    entity_payload = {
        "entities": {
            "Q1339": {
                "labels": {"en": {"value": "Johann Sebastian Bach"}},
                "sitelinks": {"enwiki": {"title": "Johann Sebastian Bach"}},
                "claims": {
                    "P569": [
                        {
                            "mainsnak": {
                                "datavalue": {
                                    "value": {"time": "+1685-03-21T00:00:00Z"},
                                    "type": "time",
                                }
                            }
                        }
                    ],
                    "P570": [
                        {
                            "mainsnak": {
                                "datavalue": {
                                    "value": {"time": "+1750-07-28T00:00:00Z"},
                                    "type": "time",
                                }
                            }
                        }
                    ],
                },
            }
        }
    }
    wiki_payload = {
        "title": "Johann Sebastian Bach",
        "extract": "Johann Sebastian Bach was a German composer and musician of the late Baroque period.",
        "thumbnail": {"source": "https://example.test/bach.jpg"},
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Johann_Sebastian_Bach"}},
    }

    def fake_get(url: str, params: dict | None = None, **_kwargs):  # noqa: ANN001
        u = str(url)
        if "wbsearchentities" in u or (params and params.get("action") == "wbsearchentities"):
            return _FakeResp(search_payload)
        if "EntityData" in u:
            return _FakeResp(entity_payload)
        if "wikipedia.org" in u and "summary" in u:
            return _FakeResp(wiki_payload)
        return _FakeResp({}, status_code=404)

    fake_client = MagicMock()
    fake_client.get.side_effect = fake_get
    fake_client.__enter__ = lambda s: s
    fake_client.__exit__ = lambda *_a: False

    import aulos_knowledge.person_entity as pe
    import aulos_knowledge.person_aggregate as pa

    monkeypatch.setattr(pe.httpx, "Client", lambda **_k: fake_client)
    monkeypatch.setattr(pa.httpx, "Client", lambda **_k: fake_client)

    resp = client.post(
        "/v1/kb/entities/person/resolve",
        json={"name": "Johann Sebastian Bach", "kind": "composer", "enrich": True},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["source"] in {"enriched", "aggregated"}
    assert data["external_ids"].get("wikidata") == "Q1339"
    assert "Baroque" in (data.get("summary") or data.get("summary_en") or "")
    assert (data.get("lifespan") or "").startswith("1685")

    from aulos_knowledge.db import ComposerEntity, KnowledgeDocument, SessionLocal

    assert SessionLocal is not None
    db = SessionLocal()
    try:
        row = db.get(ComposerEntity, data["person_id"])
        assert row is not None
        assert row.summary_en
        docs = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.entity_id == data["person_id"])
            .all()
        )
        assert docs
    finally:
        db.close()


def test_resolve_blank_name_400(client) -> None:
    resp = client.post("/v1/kb/entities/person/resolve", json={"name": "  "})
    assert resp.status_code == 400


def test_unrelated_name_does_not_borrow_bach(client) -> None:
    """朱莉亚尼 / Giuliani must not resolve to Bach via soft match or stray RAG hits."""
    from aulos_knowledge.db import ComposerEntity, KnowledgeChunk, KnowledgeDocument, SessionLocal

    assert SessionLocal is not None
    db = SessionLocal()
    try:
        db.add(
            ComposerEntity(
                id="js-bach",
                name_en="Johann Sebastian Bach",
                name_zh="巴赫",
                aliases_json=json.dumps(["Bach", "J.S. Bach"]),
                lifespan="1685–1750",
                era="Baroque",
                summary_en="German Baroque composer.",
                summary_zh="巴洛克时期德国作曲家。",
            )
        )
        doc = KnowledgeDocument(
            source_id="wikidata",
            entity_type="composer",
            entity_id="js-bach",
            title="Wikidata Q1339 — Johann Sebastian Bach",
            body="German composer Johann Sebastian Bach of the Baroque period.",
            status="published",
        )
        db.add(doc)
        db.flush()
        db.add(
            KnowledgeChunk(
                document_id=doc.id,
                section="summary",
                text=doc.body,
                aulos_work_id="",
            )
        )
        db.commit()
    finally:
        db.close()

    for name in ("朱莉亚尼", "朱莉尼", "Mauro Giuliani", "Giuliani"):
        resp = client.post(
            "/v1/kb/entities/person/resolve",
            json={"name": name, "kind": "composer", "enrich": False},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["source"] == "unresolved", name
        assert data.get("person_id") in ("", None)
        assert "Bach" not in (data.get("summary") or "")
        assert "巴赫" not in (data.get("display_name") or "")


def test_ingest_discogs_profile(client) -> None:
    resp = client.post(
        "/v1/kb/entities/person/ingest",
        json={
            "name": "Mauro Giuliani",
            "kind": "composer",
            "display_name": "Mauro Giuliani",
            "summary": "Italian guitarist and composer.",
            "source_id": "discogs",
            "external_ids": {"discogs": "12345"},
            "provenance": [{"source_id": "discogs", "url": "https://www.discogs.com/artist/12345"}],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["source"] == "enriched"
    assert data["person_id"]
    assert "guitarist" in data["summary"]

    again = client.post(
        "/v1/kb/entities/person/resolve",
        json={"name": "Mauro Giuliani", "kind": "composer", "enrich": False},
    )
    assert again.status_code == 200
    assert again.json()["source"] == "knowledge"
    assert "guitarist" in again.json()["summary"]

