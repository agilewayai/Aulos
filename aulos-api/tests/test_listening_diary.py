"""SPEC-019 / SPEC-020 listening diary + plaza SNS — mocked Discogs, no live network."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

DIARY_RELEASE: dict[str, Any] = {
    "id": 700123,
    "title": "Glenn Gould - The Goldberg Variations",
    "artists": [{"name": "Glenn Gould", "role": ""}],
    "extraartists": [
        {"name": "Johann Sebastian Bach", "role": "Composed By"},
        {"name": "Glenn Gould", "role": "Piano"},
        {"name": "Columbia Symphony Orchestra", "role": "Orchestra"},
    ],
    "tracklist": [
        {"position": "A1", "title": "Aria", "type_": "track", "duration": "3:05"},
        {"position": "A2", "title": "Variation 1 a 1 Clav.", "type_": "track", "duration": "1:10"},
    ],
    "labels": [{"name": "Columbia Masterworks", "catno": "ML 5060"}],
    "year": 1956,
    "uri": "/release/700123-Glenn-Gould-The-Goldberg-Variations",
    "genres": ["Classical"],
    "styles": ["Baroque"],
    "formats": [{"name": "Vinyl", "descriptions": ["LP"]}],
    "images": [
        {
            "type": "primary",
            "uri": "https://i.discogs.com/cover-700123.jpg",
            "resource_url": "https://i.discogs.com/cover-700123.jpg",
        }
    ],
    "thumb": "https://i.discogs.com/thumb-700123.jpg",
    "country": "US",
}


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "diary.db"
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


def _register_verify_login(client: TestClient, email: str, name: str = "Listener") -> str:
    from aulos_api.services.mailgun import get_fake_mailbox

    client.post(
        "/v1/auth/register",
        json={"email": email, "password": "UserPass123!", "display_name": name},
    )
    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    login = client.post("/v1/auth/login", json={"email": email, "password": "UserPass123!"})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _mock_discogs(monkeypatch: pytest.MonkeyPatch, raw: dict[str, Any] | None = None) -> None:
    from aulos_api.services import discogs as discogs_mod

    payload = {"kind": "release", "id": int((raw or DIARY_RELEASE)["id"]), "raw": raw or DIARY_RELEASE}

    def fake_fetch(entity_id, *, client=None, db=None):  # noqa: ANN001
        return payload

    monkeypatch.setattr(discogs_mod, "fetch_discogs_entity", fake_fetch)


def test_build_diary_snapshot_extracts_cover_tracklist_ensemble() -> None:
    from aulos_api.services.discogs import build_diary_snapshot

    snap = build_diary_snapshot({"kind": "release", "id": 700123, "raw": DIARY_RELEASE})
    assert snap["provider"] == "discogs"
    assert snap["external_id"] == "700123"
    assert snap["source_kind"] == "vinyl"
    assert "Goldberg" in snap["title"]
    assert snap["cover_image_url"].endswith("cover-700123.jpg")
    assert snap["composers"] == ["Johann Sebastian Bach"]
    assert "Glenn Gould" in snap["performers"]
    assert "Columbia Symphony Orchestra" in snap["ensembles"]
    assert snap["catno"] == "ML 5060"
    assert snap["tracklist"][0]["title"] == "Aria"
    assert snap["tracklist"][0]["position"] == "A1"


def test_diary_draft_crud_publish_plaza_social(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_discogs(monkeypatch)
    token_a = _register_verify_login(client, "a@example.com", "Alice")
    token_b = _register_verify_login(client, "b@example.com", "Bob")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    bad = client.post(
        "/v1/listening-diary",
        headers=headers_a,
        json={"provider": "netease", "external_id": "1"},
    )
    assert bad.status_code == 400

    created = client.post(
        "/v1/listening-diary",
        headers=headers_a,
        json={
            "provider": "discogs",
            "external_id": "700123",
            "listening_note": "Tonight: Aria first.",
        },
    )
    assert created.status_code == 201, created.text
    post = created.json()
    assert post["status"] == "draft"
    assert post["title"]
    assert post["cover_image_url"]
    assert post["snapshot"]["tracklist"]
    post_id = post["id"]

    listed = client.get("/v1/listening-diary", headers=headers_a)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0].get("snapshot")
    assert listed.json()[0]["snapshot"].get("composers") is not None or listed.json()[0]["snapshot"].get("tracklist")

    denied = client.get(f"/v1/listening-diary/{post_id}", headers=headers_b)
    assert denied.status_code == 404

    feed_empty = client.get("/v1/plaza/feed")
    assert feed_empty.status_code == 200
    assert feed_empty.json()["items"] == []

    published = client.post(f"/v1/listening-diary/{post_id}/publish", headers=headers_a)
    assert published.status_code == 200, published.text
    assert published.json()["published"] is True
    slug = published.json()["share_slug"]
    assert slug

    feed = client.get("/v1/plaza/feed")
    assert len(feed.json()["items"]) == 1
    assert feed.json()["items"][0]["author"]["display_name"] == "Alice"

    public = client.get(f"/v1/plaza/posts/{slug}")
    assert public.status_code == 200
    assert public.json()["listening_note"] == "Tonight: Aria first."

    unpublished = client.post(f"/v1/listening-diary/{post_id}/unpublish", headers=headers_a)
    assert unpublished.status_code == 200
    assert unpublished.json()["published"] is False
    assert client.get(f"/v1/plaza/posts/{slug}").status_code == 404
    assert client.get("/v1/plaza/feed").json()["items"] == []

    client.post(f"/v1/listening-diary/{post_id}/publish", headers=headers_a)

    # Bob creates + publishes another post
    other = client.post(
        "/v1/listening-diary",
        headers=headers_b,
        json={"provider": "discogs", "external_id": "700123", "listening_note": "Bob listens"},
    )
    bob_id = other.json()["id"]
    client.post(f"/v1/listening-diary/{bob_id}/publish", headers=headers_b)

    me = client.get("/v1/auth/me", headers=headers_a).json()
    bob_me = client.get("/v1/auth/me", headers=headers_b).json()

    self_follow = client.post(f"/v1/social/follows/{me['id']}", headers=headers_a)
    assert self_follow.status_code == 400

    followed = client.post(f"/v1/social/follows/{bob_me['id']}", headers=headers_a)
    assert followed.status_code == 200

    home = client.get("/v1/plaza/home", headers=headers_a)
    assert home.status_code == 200
    assert len(home.json()["items"]) == 1
    assert home.json()["items"][0]["author"]["display_name"] == "Bob"

    blog = client.get(f"/v1/social/users/{bob_me['id']}")
    assert blog.status_code == 200
    assert len(blog.json()["posts"]) == 1

    liked = client.post(f"/v1/plaza/posts/{bob_id}/likes", headers=headers_a)
    assert liked.status_code == 200
    assert liked.json()["like_count"] == 1
    liked2 = client.post(f"/v1/plaza/posts/{bob_id}/likes", headers=headers_a)
    assert liked2.json()["like_count"] == 1

    commented = client.post(
        f"/v1/plaza/posts/{bob_id}/comments",
        headers=headers_a,
        json={"body": "Beautiful pressing."},
    )
    assert commented.status_code == 201
    comments = client.get(f"/v1/plaza/posts/{bob_id}/comments")
    assert len(comments.json()["items"]) == 1

    unliked = client.delete(f"/v1/plaza/posts/{bob_id}/likes", headers=headers_a)
    assert unliked.json()["like_count"] == 0

    client.delete(f"/v1/social/follows/{bob_me['id']}", headers=headers_a)
    assert client.get("/v1/plaza/home", headers=headers_a).json()["items"] == []

    deleted = client.delete(f"/v1/listening-diary/{post_id}", headers=headers_a)
    assert deleted.status_code == 204
