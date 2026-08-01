"""REQ-010 — Composer dossier: life events + works tree from mocked Wikidata."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from conftest import AUTH_HEADERS

BACH_QID = "Q1339"
BACH_ID = "johann-sebastian-bach"

BACH_ENTITY = {
    "entities": {
        BACH_QID: {
            "labels": {
                "en": {"value": "Johann Sebastian Bach"},
                "zh-hans": {"value": "约翰·塞巴斯蒂安·巴赫"},
            },
            "descriptions": {
                "en": {"value": "German composer and musician of the Baroque period"},
                "zh-hans": {"value": "巴洛克时期德国作曲家"},
            },
            "sitelinks": {
                "enwiki": {"title": "Johann Sebastian Bach"},
                "zhwiki": {"title": "约翰·塞巴斯蒂安·巴赫"},
            },
            "claims": {
                "P569": [
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {"time": "+1685-03-21T00:00:00Z", "precision": 11},
                                "type": "time",
                            }
                        }
                    }
                ],
                "P570": [
                    {
                        "mainsnak": {
                            "datavalue": {
                                "value": {"time": "+1750-07-28T00:00:00Z", "precision": 11},
                                "type": "time",
                            }
                        }
                    }
                ],
                "P19": [
                    {
                        "mainsnak": {
                            "datavalue": {"value": {"id": "Q7077"}, "type": "wikibase-entityid"}
                        }
                    }
                ],
                "P20": [
                    {
                        "mainsnak": {
                            "datavalue": {"value": {"id": "Q2079"}, "type": "wikibase-entityid"}
                        }
                    }
                ],
                "P39": [
                    {
                        "mainsnak": {
                            "datavalue": {"value": {"id": "Q123"}, "type": "wikibase-entityid"}
                        },
                        "qualifiers": {
                            "P580": [
                                {
                                    "datavalue": {
                                        "value": {"time": "+1723-00-00T00:00:00Z", "precision": 9}
                                    }
                                }
                            ]
                        },
                    }
                ],
                "P800": [
                    {
                        "mainsnak": {
                            "datavalue": {"value": {"id": "Q155217"}, "type": "wikibase-entityid"}
                        },
                        "qualifiers": {
                            "P580": [
                                {
                                    "datavalue": {
                                        "value": {"time": "+1721-00-00T00:00:00Z", "precision": 9}
                                    }
                                }
                            ]
                        },
                    }
                ],
            },
        }
    }
}

PLACE_ENTITIES = {
    "Q7077": {"entities": {"Q7077": {"labels": {"en": {"value": "Eisenach"}}}}},
    "Q2079": {"entities": {"Q2079": {"labels": {"en": {"value": "Leipzig"}}}}},
    "Q123": {"entities": {"Q123": {"labels": {"en": {"value": "Thomaskantor"}}}}},
}

SPARQL_WORKS = {
    "results": {
        "bindings": [
            {
                "work": {"value": "http://www.wikidata.org/entity/Q155217"},
                "workLabel": {"value": "Brandenburg Concertos"},
                "inception": {"value": "1721-01-01T00:00:00Z"},
                "genreLabel": {"value": "concerto grosso"},
                "partOf": {"value": ""},
                "partOfLabel": {"value": ""},
                "catalog": {"value": "BWV 1046–1051"},
            },
            {
                "work": {"value": "http://www.wikidata.org/entity/Q210455"},
                "workLabel": {"value": "Brandenburg Concerto No. 1"},
                "inception": {"value": "1721-01-01T00:00:00Z"},
                "genreLabel": {"value": "concerto"},
                "partOf": {"value": "http://www.wikidata.org/entity/Q155217"},
                "partOfLabel": {"value": "Brandenburg Concertos"},
                "catalog": {"value": "BWV 1046"},
            },
            {
                "work": {"value": "http://www.wikidata.org/entity/Q11985"},
                "workLabel": {"value": "Mass in B minor"},
                "inception": {"value": "1749-01-01T00:00:00Z"},
                "genreLabel": {"value": "mass"},
                "catalog": {"value": "BWV 232"},
            },
        ]
    }
}


def _mock_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    resp.headers = {"content-type": "application/json"}
    return resp


def _http_get(url: str, *args, **kwargs):
    u = str(url)
    if "Special:EntityData/Q1339" in u:
        return _mock_response(BACH_ENTITY)
    for qid, payload in PLACE_ENTITIES.items():
        if f"Special:EntityData/{qid}" in u:
            return _mock_response(payload)
    if "query.wikidata.org" in u:
        return _mock_response(SPARQL_WORKS)
    # Commons / unexpected — empty
    return _mock_response({"entities": {}, "query": {"pages": {}}})


def test_build_dossier_upserts_timeline_and_works(client: TestClient) -> None:
    with patch("aulos_knowledge.composer_dossier.httpx.Client") as client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client.get.side_effect = _http_get
        client_cls.return_value = mock_client

        with patch("aulos_knowledge.composer_dossier.fetch_wikidata_media_claims", return_value=[]):
            job = client.post(
                f"/v1/admin/composers/{BACH_ID}/build-dossier",
                headers=AUTH_HEADERS,
                json={"qid": BACH_QID},
            )

    assert job.status_code == 200, job.text
    body = job.json()
    assert body["status"] == "succeeded"
    assert body["composer_id"] == BACH_ID
    assert body["qid"] == BACH_QID

    dossier = client.get(f"/v1/admin/composers/{BACH_ID}/dossier", headers=AUTH_HEADERS)
    assert dossier.status_code == 200, dossier.text
    data = dossier.json()
    assert data["composer"]["name_en"] == "Johann Sebastian Bach"
    assert data["composer"]["famous"] is True
    assert "Baroque" in (data["composer"]["era"] or "") or data["composer"]["era"]

    types = {e["event_type"] for e in data["timeline"]}
    assert "birth" in types
    assert "death" in types
    assert data["events_count"] >= 2

    birth = next(e for e in data["timeline"] if e["event_type"] == "birth")
    assert birth["date_start"].startswith("1685")
    assert birth["significance"] == "major"

    assert data["works_count"] >= 3
    # Brandenburg cycle should nest No.1 under collection when P361 present
    titles = []

    def walk(nodes: list) -> None:
        for n in nodes:
            titles.append(n["title_en"])
            walk(n.get("children") or [])

    walk(data["works_tree"])
    assert any("Brandenburg" in t for t in titles)
    parent = next(n for n in data["works_tree"] if "Brandenburg Concertos" in n["title_en"])
    assert parent["work_kind"] in {"collection", "cycle", "work"}
    child_titles = [c["title_en"] for c in parent.get("children") or []]
    assert any("No. 1" in t for t in child_titles)

    kb = client.get(f"/v1/kb/composers/{BACH_ID}/dossier", headers=AUTH_HEADERS)
    assert kb.status_code == 200
    assert kb.json()["events_count"] == data["events_count"]


def test_dossier_missing_composer_404(client: TestClient) -> None:
    r = client.get("/v1/admin/composers/not-a-real-composer/dossier", headers=AUTH_HEADERS)
    assert r.status_code == 404


def test_build_dossier_requires_qid(client: TestClient) -> None:
    r = client.post(
        "/v1/admin/composers/unknown-nobody/build-dossier",
        headers=AUTH_HEADERS,
        json={},
    )
    assert r.status_code == 400


def test_extract_life_events_unit() -> None:
    from aulos_knowledge.composer_dossier import extract_life_events

    claims = BACH_ENTITY["entities"][BACH_QID]["claims"]
    events = extract_life_events(
        composer_id=BACH_ID,
        qid=BACH_QID,
        claims=claims,
        place_labels={"Q7077": "Eisenach", "Q2079": "Leipzig", "Q123": "Thomaskantor"},
        source_id="wikidata",
        artifact_id=1,
        job_id=1,
    )
    by_type = {e["event_type"]: e for e in events}
    assert by_type["birth"]["place_label"] == "Eisenach"
    assert by_type["death"]["date_start"].startswith("1750")
    assert any(e["event_type"] == "composition_milestone" for e in events)
