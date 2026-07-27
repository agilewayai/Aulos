"""SPEC-008 /discogs release analysis — mocked Discogs, no live network."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient


GOLD_RELEASE: dict[str, Any] = {
    "id": 700123,
    "title": "Glenn Gould - The Goldberg Variations",
    "artists": [{"name": "Glenn Gould", "role": ""}],
    "extraartists": [
        {"name": "Johann Sebastian Bach", "role": "Composed By"},
        {"name": "Glenn Gould", "role": "Piano"},
    ],
    "tracklist": [
        {"position": "A1", "title": "Aria", "type_": "track"},
        {"position": "A2", "title": "Variation 1 a 1 Clav.", "type_": "track"},
    ],
    "labels": [{"name": "Columbia Masterworks", "catno": "ML 5060"}],
    "year": 1956,
    "uri": "/release/700123-Glenn-Gould-The-Goldberg-Variations",
    "genres": ["Classical"],
    "styles": ["Baroque"],
}


def test_parse_discogs_command() -> None:
    from aulos_skills.intake_parse import parse_discogs_command

    assert parse_discogs_command("/discogs #700123") == {
        "release_id": "700123",
        "command": "discogs",
        "ref_kind": "release",
    }
    assert parse_discogs_command("/discogs 700123")["release_id"] == "700123"
    assert parse_discogs_command("please /discogs #99 now")["release_id"] == "99"
    cat = parse_discogs_command("/discogs #423-287-1")
    assert cat == {"catno": "423-287-1", "command": "discogs", "ref_kind": "catno"}
    assert parse_discogs_command("/discogs 423-287-1")["catno"] == "423-287-1"
    assert parse_discogs_command("/discog #700123") is None
    assert parse_discogs_command("I'm listening to Bach") is None


def test_analyze_discogs_release_extracts_composer_and_performers() -> None:
    from aulos_api.services.discogs import analyze_discogs_release

    out = analyze_discogs_release({"kind": "release", "id": 700123, "raw": GOLD_RELEASE})
    assert out["composer"] == "Johann Sebastian Bach"
    assert "Glenn Gould" in out["performers"]
    assert "Johann Sebastian Bach" not in out["performers"]
    assert "Goldberg" in out["work_title"] or "Aria" in out["work_title"]
    assert out["uri"].startswith("https://www.discogs.com/")
    seed = out["kb_seed"]
    assert seed["interpretations"][0]["discogs_url"]
    assert "/discogs" in seed["interpretations"][0]["why_listen"]
    assert "700123" in seed["vinyl_and_discography"][0]["note"]
    assert "Discogs release 700123" in out["listening_intent"]


def test_catno_423_287_1_resolves_via_search(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke fixture: DG catno 423-287-1 must not truncate to release 423."""
    from aulos_api.services import discogs as discogs_mod
    from aulos_api.services.discogs import analyze_discogs_release, resolve_discogs_message

    horowitz = {
        "id": 4084139,
        "title": "Horowitz Plays Mozart (Piano Concerto No. 23 K. 488 • Piano Sonata K. 333)",
        "artists": [
            {"name": "Vladimir Horowitz"},
            {"name": "Wolfgang Amadeus Mozart"},
            {"name": "Orchestra Del Teatro Alla Scala"},
            {"name": "Carlo Maria Giulini"},
        ],
        "extraartists": [
            {"name": "Wolfgang Amadeus Mozart", "role": "Composed By"},
            {"name": "Vladimir Horowitz", "role": "Piano"},
            {"name": "Carlo Maria Giulini", "role": "Conductor"},
        ],
        "tracklist": [
            {"title": "Piano Concerto No. 23 In A Major, K. 488", "type_": "track"},
            {"title": "Piano Sonata In B Flat Major, K. 333", "type_": "track"},
        ],
        "labels": [{"name": "Deutsche Grammophon", "catno": "423 287-1"}],
        "year": 1987,
        "uri": "/release/4084139",
        "genres": ["Classical"],
        "master_id": 498229,
    }

    def fake_search(catno: str, *, client=None, db=None):  # noqa: ANN001
        assert "423" in catno and "287" in catno
        return {
            "kind": "release",
            "id": 4084139,
            "raw": horowitz,
            "resolved_from": "catno",
            "catno_query": catno,
            "catno_match": "423 287-1",
        }

    monkeypatch.setattr(discogs_mod, "search_discogs_by_catno", fake_search)
    out = resolve_discogs_message("/discogs #423-287-1")
    assert out is not None
    assert out["release_id"] == 4084139
    assert "Mozart" in out["composer"]
    assert "Horowitz" in ",".join(out["performers"])
    assert "Mozart" not in out["performers"]
    assert "Concerto" in out["work_title"] or "K. 488" in out["work_title"]
    assert "423" in str(out.get("catno_query") or "")


def test_fetch_release_then_master_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services.discogs import DiscogsError, fetch_discogs_entity

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url.path))
        if request.url.path.endswith("/releases/42"):
            return httpx.Response(404, json={"message": "Not Found"})
        if request.url.path.endswith("/masters/42"):
            return httpx.Response(
                200,
                json={
                    "id": 42,
                    "title": "Goldberg Variations",
                    "main_release": 700123,
                    "artists": [{"name": "Glenn Gould"}],
                    "tracklist": [{"title": "Aria"}],
                },
            )
        if request.url.path.endswith("/releases/700123"):
            return httpx.Response(200, json=GOLD_RELEASE)
        return httpx.Response(404, json={})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, headers={"User-Agent": "test"}) as client:
        payload = fetch_discogs_entity(42, client=client)
    assert payload["kind"] == "master"
    assert payload["raw"]["id"] == 700123
    assert "/releases/42" in calls[0] or calls[0].endswith("/releases/42")

    def all_404(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={})

    with httpx.Client(transport=httpx.MockTransport(all_404)) as client:
        with pytest.raises(DiscogsError) as ei:
            fetch_discogs_entity(999, client=client)
    assert ei.value.status_code == 404


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "discog.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")

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


def _user_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/v1/auth/register",
        json={"email": "discog@example.com", "password": "ListenPass123!", "display_name": "Disc"},
    )
    from aulos_api.services.mailgun import get_fake_mailbox

    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    login = client.post(
        "/v1/auth/login",
        json={"email": "discog@example.com", "password": "ListenPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_listening_guide_from_discogs_command(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services import discogs as discogs_mod

    def fake_resolve(
        message: str,
        *,
        client: httpx.Client | None = None,
        db: Any = None,
    ) -> dict[str, Any] | None:
        from aulos_skills.intake_parse import parse_discogs_command
        from aulos_api.services.discogs import analyze_discogs_release

        cmd = parse_discogs_command(message)
        if not cmd:
            return None
        return analyze_discogs_release({"kind": "release", "id": 700123, "raw": GOLD_RELEASE})

    monkeypatch.setattr(discogs_mod, "resolve_discogs_message", fake_resolve)
    monkeypatch.setattr(
        "aulos_api.services.listening_guide.resolve_discogs_message",
        fake_resolve,
    )

    headers = _user_headers(client)
    res = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "/discogs #700123"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == "completed"
    assert "Goldberg" in body["work_title"]
    assert "Bach" in (body.get("composer") or "")
    assert "<!DOCTYPE html>" in body["guide_html"]

    from aulos_api.db.session import SessionLocal
    from aulos_api.db.models import ListeningGuide
    import json

    with SessionLocal() as db:
        row = db.query(ListeningGuide).filter(ListeningGuide.id == body["id"]).one()
        research = json.loads(row.research_json or "{}")
    assert research.get("discogs", {}).get("release_id") == 700123
    assert "discogs.com" in str(research.get("discogs", {}).get("uri") or "")


def test_suggest_discogs_releases_autocomplete(monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services.discogs import suggest_discogs_releases

    search_calls: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/database/search"):
            params = dict(request.url.params)
            search_calls.append(params)
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": 4084139,
                            "title": "Vladimir Horowitz - Horowitz Plays Mozart",
                            "catno": "423 287-1",
                            "year": "1987",
                            "label": ["Deutsche Grammophon"],
                            "genre": ["Classical"],
                            "country": "Germany",
                            "thumb": "https://example.com/t.jpg",
                            "uri": "/release/4084139",
                        },
                        {
                            "id": 99,
                            "title": "Some Pop Album",
                            "catno": "POP-1",
                            "year": "2000",
                            "label": ["Other"],
                            "genre": ["Pop"],
                            "uri": "/release/99",
                        },
                    ]
                },
            )
        return httpx.Response(404, json={})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        short = suggest_discogs_releases("a", client=http)
        assert short == []

        hits = suggest_discogs_releases("423-287-1", client=http, limit=10)
    assert len(hits) >= 1
    assert hits[0]["id"] == 4084139  # Classical first
    assert hits[0]["catno"] == "423 287-1"
    assert hits[0]["label"] == "Deutsche Grammophon"
    assert any(c.get("catno") for c in search_calls)
    assert any(c.get("q") == "423-287-1" for c in search_calls)


def test_discogs_search_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services import discogs as discogs_mod

    def fake_suggest(query: str, *, client=None, db=None, limit: int = 10):  # noqa: ANN001
        assert "423" in query
        return [
            {
                "id": 4084139,
                "title": "Horowitz Plays Mozart",
                "catno": "423 287-1",
                "year": "1987",
                "label": "Deutsche Grammophon",
                "country": "Germany",
                "thumb": "",
                "genres": ["Classical"],
                "resource_url": "",
                "uri": "https://www.discogs.com/release/4084139",
            }
        ]

    monkeypatch.setattr(discogs_mod, "suggest_discogs_releases", fake_suggest)

    unauth = client.get("/v1/discogs/search", params={"q": "423-287-1"})
    assert unauth.status_code == 401

    headers = _user_headers(client)

    res = client.get("/v1/discogs/search", headers=headers, params={"q": "423-287-1", "limit": 5})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["query"] == "423-287-1"
    assert body["results"][0]["id"] == 4084139
    assert "Mozart" in body["results"][0]["title"]


def test_ops_discogs_token_config(client: TestClient) -> None:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    g = client.get("/v1/ops/discogs", headers=headers)
    assert g.status_code == 200, g.text
    assert g.json()["enabled"] is True
    assert g.json()["user_token_set"] is False

    p = client.put(
        "/v1/ops/discogs",
        headers=headers,
        json={"user_token": "discogs-test-token-xyz", "enabled": True},
    )
    assert p.status_code == 200, p.text
    assert p.json()["user_token_set"] is True
    assert p.json()["auth_source"] == "ops"
    assert p.json()["authenticated"] is True

    keep = client.put("/v1/ops/discogs", headers=headers, json={"enabled": True})
    assert keep.json()["user_token_set"] is True

    cleared = client.put(
        "/v1/ops/discogs",
        headers=headers,
        json={"clear_user_token": True},
    )
    assert cleared.json()["user_token_set"] is False

    from aulos_api.db.session import SessionLocal
    from aulos_api.services.discogs import _auth_params, save_discogs_config

    with SessionLocal() as db:
        save_discogs_config(db, user_token="from-ops")
        assert _auth_params(db) == {"token": "from-ops"}
