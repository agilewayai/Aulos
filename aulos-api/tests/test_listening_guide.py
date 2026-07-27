"""Listening guide MVP workflow tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "listening.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("AULOS_REDIS_URL", "")

    from aulos_api.config import get_settings
    from aulos_api.db import session as db_session
    from aulos_api.services.mailgun import clear_fake_mailbox
    from aulos_api.services.listening_queue import reset_listening_worker_for_tests

    get_settings.cache_clear()
    db_session.reset_engine()
    clear_fake_mailbox()
    reset_listening_worker_for_tests()

    from aulos_api.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    clear_fake_mailbox()
    get_settings.cache_clear()
    db_session.reset_engine()
    reset_listening_worker_for_tests()


def _user_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/v1/auth/register",
        json={"email": "listener@example.com", "password": "ListenPass123!", "display_name": "Listener"},
    )
    from aulos_api.services.mailgun import get_fake_mailbox

    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    login = client.post(
        "/v1/auth/login",
        json={"email": "listener@example.com", "password": "ListenPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_goldberg_listening_guide_workflow(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Architecture gate: product path must not orchestrate SkillRuntime.iter_listening_chain
    import aulos_skills.runtime as rt

    def _boom(*_a, **_k):  # noqa: ANN001
        raise AssertionError("API must not call SkillRuntime.iter_listening_chain")

    monkeypatch.setattr(rt.SkillRuntime, "iter_listening_chain", _boom)

    headers = _user_headers(client)
    res = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={
            "message": "I'm beginning to listen to Bach Goldberg Variations — help me learn this masterwork"
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert "Goldberg" in body["work_title"]
    assert body["status"] == "completed"
    assert len(body["steps"]) >= 5
    assert "intake" in [s["id"] for s in body["steps"]]
    assert all(s.get("skill_id") for s in body["steps"] if s["id"] != "route" or s.get("skill_id"))
    # all completed steps from runtime should cite skills
    assert any(s.get("skill_id") == "aulos-listening-corpus" for s in body["steps"])
    assert body.get("skill_versions")
    assert "aulos-listening-depth" in body["skill_versions"]
    assert "<!DOCTYPE html>" in body["guide_html"]
    assert "Listening map" in body["guide_html"]
    assert body.get("source") in {"agent-skills", "skills", "skills+fake"} or "agent" in str(body.get("source"))
    assert "Wide research" in body["guide_html"]

    listed = client.get("/v1/listening-guides", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
    got = client.get(f"/v1/listening-guides/{body['id']}", headers=headers)
    assert got.status_code == 200
    assert got.json()["id"] == body["id"]


def test_listening_guide_requires_auth(client: TestClient) -> None:
    res = client.post("/v1/listening-guides", json={"message": "Bach Goldberg Variations"})
    assert res.status_code == 401


def test_listening_guide_stream_sse(client: TestClient) -> None:
    headers = _user_headers(client)
    with client.stream(
        "POST",
        "/v1/listening-guides/stream",
        headers=headers,
        json={"message": "I'm listening to Bach Goldberg Variations"},
    ) as res:
        assert res.status_code == 200, res.text
        assert "text/event-stream" in res.headers.get("content-type", "")
        body = "".join(res.iter_text())
    assert "event: step" in body
    assert "event: done" in body
    assert "aulos-listening-corpus" in body


def test_publish_guide_is_publicly_readable_without_auth(client: TestClient) -> None:
    headers = _user_headers(client)
    created = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "Bach Goldberg Variations listening guide"},
    )
    assert created.status_code == 201, created.text
    guide_id = created.json()["id"]
    assert created.json().get("published") is False

    # unpublished → public 404
    assert client.get("/v1/public/guides/not-a-real-slug").status_code == 404

    published = client.post(f"/v1/listening-guides/{guide_id}/publish", headers=headers)
    assert published.status_code == 200, published.text
    body = published.json()
    assert body["published"] is True
    slug = body["share_slug"]
    assert slug
    assert body["share_path"] == f"/g/{slug}"

    # public HTML — no Authorization header
    page = client.get(f"/v1/public/guides/{slug}")
    assert page.status_code == 200
    assert "text/html" in page.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in page.text
    assert "Goldberg" in page.text or "Bach" in page.text

    meta = client.get(f"/v1/public/guides/{slug}/meta")
    assert meta.status_code == 200
    assert meta.json()["share_slug"] == slug
    assert "steps" not in meta.json()

    # unpublish hides public page; slug path 404
    hidden = client.post(f"/v1/listening-guides/{guide_id}/unpublish", headers=headers)
    assert hidden.status_code == 200
    assert hidden.json()["published"] is False
    assert client.get(f"/v1/public/guides/{slug}").status_code == 404

    # re-publish keeps same slug
    again = client.post(f"/v1/listening-guides/{guide_id}/publish", headers=headers)
    assert again.status_code == 200
    assert again.json()["share_slug"] == slug
    assert client.get(f"/v1/public/guides/{slug}").status_code == 200


def test_public_guide_gets_share_chrome_patch_without_recompose(client: TestClient) -> None:
    """Style/chrome fixes apply at serve time — stored HTML need not be recomposed."""
    headers = _user_headers(client)
    created = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "Bach Goldberg Variations listening guide"},
    )
    assert created.status_code == 201, created.text
    guide_id = created.json()["id"]
    # Simulate an older stored page that still has owner-toolbar script + expanded ambient
    from aulos_api.db.session import SessionLocal, get_engine
    from aulos_api.db.models import ListeningGuide

    get_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        row = db.query(ListeningGuide).filter(ListeningGuide.id == guide_id).one()
        row.guide_html = """<!DOCTYPE html><html><head><title>Old</title></head><body>
<aside class="ambient"><div class="ambient-copy">
<p class="ambient-kicker">主题在场</p>
<p class="ambient-title">Aria</p>
<p class="ambient-credit">Ishizaka CC0</p>
<p class="ambient-hint">hint</p></div>
<div class="ambient-controls"><button class="ambient-toggle">播放主题</button>
<audio id="aulos-ambient"></audio></div></aside>
<script>(function(){ var x='aulos-owner-bar'; })();</script>
</body></html>"""
        row.share_slug = "testsharechrome01"
        from aulos_api.services.listening_guide import utcnow

        row.published_at = utcnow()
        db.add(row)
        db.commit()
        slug = row.share_slug
    finally:
        db.close()

    page = client.get(f"/v1/public/guides/{slug}")
    assert page.status_code == 200
    assert "aulos-share-chrome" in page.text
    assert "aulos-ambient-failover" in page.text
    assert "aulos-owner-bar" not in page.text or "display:none" in page.text
    assert "aulos-mobile-harden" in page.text
    assert "说明" in page.text or "Info" in page.text or "录音说明" in page.text
    assert "wipeOwnerChrome" in page.text


def test_ops_disable_skill_skips_step(client: TestClient) -> None:
    # superadmin login via bootstrap
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert login.status_code == 200, login.text
    admin = {"Authorization": f"Bearer {login.json()['access_token']}"}
    toggled = client.patch(
        "/v1/ops/skills/aulos-listening-eval",
        headers=admin,
        json={"enabled": False},
    )
    assert toggled.status_code == 200, toggled.text
    assert toggled.json()["enabled"] is False

    headers = _user_headers(client)
    res = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "Bach Goldberg Variations listening guide please"},
    )
    assert res.status_code == 201, res.text
    steps = res.json()["steps"]
    eval_step = next(s for s in steps if s["id"] == "eval")
    assert eval_step["status"] == "skipped"


def test_research_cached_and_knowledge_search(client: TestClient) -> None:
    headers = _user_headers(client)
    res = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "Bach Goldberg Variations listening guide"},
    )
    assert res.status_code == 201, res.text
    guide_id = res.json()["id"]
    from aulos_api.db.session import SessionLocal, get_engine
    from aulos_api.db.models import ListeningGuide, KnowledgeChunk

    get_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        row = db.query(ListeningGuide).filter(ListeningGuide.id == guide_id).one()
        research = __import__("json").loads(row.research_json or "{}")
        assert research.get("corpus_dossier") or research.get("corpus_hit") is not None
        assert db.query(KnowledgeChunk).count() >= 1
    finally:
        db.close()

    search = client.get(
        "/v1/knowledge/search",
        headers=headers,
        params={"q": "Goldberg Variations Aria bass", "work_hint": "Goldberg"},
    )
    assert search.status_code == 200, search.text
    body = search.json()
    assert body["rag_mode"] in {"lexical", "vector", "empty", "fastembed", "openai", "no_match"}
    assert body.get("stats", {}).get("documents", 0) >= 1
    assert isinstance(body.get("hits"), list)


def test_recompose_keeps_share_slug_and_updates_html(client: TestClient) -> None:
    headers = _user_headers(client)
    created = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "Bach Goldberg Variations listening guide"},
    )
    assert created.status_code == 201, created.text
    guide_id = created.json()["id"]
    published = client.post(f"/v1/listening-guides/{guide_id}/publish", headers=headers)
    assert published.status_code == 200
    slug = published.json()["share_slug"]
    assert slug

    ownership = client.get(f"/v1/listening-guides/by-share/{slug}", headers=headers)
    assert ownership.status_code == 200
    assert ownership.json()["id"] == guide_id

    # other user cannot claim ownership
    client.post(
        "/v1/auth/register",
        json={"email": "other@example.com", "password": "OtherPass123!", "display_name": "Other"},
    )
    from aulos_api.services.mailgun import get_fake_mailbox

    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    other_login = client.post(
        "/v1/auth/login",
        json={"email": "other@example.com", "password": "OtherPass123!"},
    )
    other = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    assert client.get(f"/v1/listening-guides/by-share/{slug}", headers=other).status_code == 404

    with client.stream(
        "POST",
        f"/v1/listening-guides/{guide_id}/recompose/stream",
        headers=headers,
        json={},
    ) as res:
        assert res.status_code == 200, res.text
        body = "".join(res.iter_text())
    assert "event: done" in body
    assert "event: step" in body

    got = client.get(f"/v1/listening-guides/{guide_id}", headers=headers)
    assert got.status_code == 200
    assert got.json()["share_slug"] == slug
    assert got.json()["published"] is True
    html = got.json()["guide_html"]
    assert "aulos-ambient" in html or "Goldberg" in html
    assert "aulos-owner-bar" not in html
    assert "Re-compose" not in html

    page = client.get(f"/v1/public/guides/{slug}")
    assert page.status_code == 200
    assert "Goldberg" in page.text or "Bach" in page.text

    updated = client.post(f"/v1/listening-guides/{guide_id}/update-publish", headers=headers)
    assert updated.status_code == 200
    assert updated.json()["share_slug"] == slug
    assert updated.json()["published"] is True
