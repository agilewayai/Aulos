"""SPEC-021 — diary → listening guide queue → review → publish."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from tests.test_listening_diary import DIARY_RELEASE, _mock_discogs, _register_verify_login


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "diary_guides.db"
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


def _fake_queued_guide(db, *, user_id: int, message: str, work_hint: str | None = None):  # noqa: ANN001
    from aulos_api.db.models import ListeningGuide
    import json

    from aulos_api.services.listening_plan import initial_plan_steps

    row = ListeningGuide(
        user_id=user_id,
        work_title="Queued guide",
        composer="",
        status="queued",
        source="pending",
        summary="",
        guide_html="",
        steps_json=json.dumps(initial_plan_steps(), ensure_ascii=False),
        research_json="{}",
        skill_versions_json="{}",
        message=message,
        error_detail="",
        tags_json="[]",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_enqueue_review_publish_diary_guide(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_discogs(monkeypatch)
    monkeypatch.setattr(
        "aulos_api.services.listening_guide.create_queued_guide",
        _fake_queued_guide,
    )

    token = _register_verify_login(client, "guide-author@example.com", "GuideAuthor")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/v1/listening-diary",
        headers=headers,
        json={"provider": "discogs", "external_id": "700123", "listening_note": "Aria night."},
    )
    assert created.status_code == 201, created.text
    post_id = created.json()["id"]

    enq = client.post(
        f"/v1/listening-diary/{post_id}/guides",
        headers=headers,
        json={"aspect": "作品导赏"},
    )
    assert enq.status_code == 202, enq.text
    link = enq.json()
    assert link["status"] == "queued"
    assert link["guide_id"]
    link_id = link["id"]
    guide_id = link["guide_id"]

    tasks = client.get("/v1/listening-diary/guide-tasks", headers=headers)
    assert tasks.status_code == 200
    assert tasks.json()["queued_count"] >= 1

    # Simulate worker completion
    from aulos_api.db import session as db_session
    from aulos_api.db.models import ListeningGuide

    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        g = db.get(ListeningGuide, guide_id)
        assert g is not None
        g.status = "completed"
        g.work_title = "Goldberg Variations"
        g.composer = "Johann Sebastian Bach"
        g.summary = "A listening guide for Gould's Goldberg."
        g.guide_html = "<article><h1>Goldberg</h1><p>Listen to the Aria.</p></article>"
        g.source = "fake"
        db.add(g)
        db.commit()
    finally:
        db.close()

    listed = client.get(f"/v1/listening-diary/{post_id}/guides", headers=headers)
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert items[0]["status"] == "ready_for_review"

    tasks2 = client.get("/v1/listening-diary/guide-tasks", headers=headers)
    assert tasks2.json()["ready_for_review_count"] >= 1

    pub = client.post(f"/v1/listening-diary/guides/{link_id}/publish", headers=headers)
    assert pub.status_code == 200, pub.text
    assert pub.json()["status"] == "published"
    assert pub.json()["guide"]["published"] is True
    assert pub.json()["guide"]["share_path"]

    # Publish diary so plaza can show attached guide
    client.post(f"/v1/listening-diary/{post_id}/publish", headers=headers)
    slug = client.get(f"/v1/listening-diary/{post_id}", headers=headers).json()["share_slug"]
    plaza = client.get(f"/v1/plaza/posts/{slug}")
    assert plaza.status_code == 200
    guides = plaza.json().get("guides") or []
    assert len(guides) == 1
    assert guides[0]["status"] == "published"
    assert guides[0]["guide"]["share_path"]


def test_other_user_cannot_enqueue(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_discogs(monkeypatch)
    monkeypatch.setattr(
        "aulos_api.services.listening_guide.create_queued_guide",
        _fake_queued_guide,
    )
    token_a = _register_verify_login(client, "a2@example.com", "A")
    token_b = _register_verify_login(client, "b2@example.com", "B")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    post_id = client.post(
        "/v1/listening-diary",
        headers=headers_a,
        json={"provider": "discogs", "external_id": "700123"},
    ).json()["id"]
    denied = client.post(
        f"/v1/listening-diary/{post_id}/guides",
        headers=headers_b,
        json={"aspect": "作品导赏"},
    )
    assert denied.status_code == 404


def _complete_guide(guide_id: int) -> None:
    from aulos_api.db import session as db_session
    from aulos_api.db.models import ListeningGuide

    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        g = db.get(ListeningGuide, guide_id)
        assert g is not None
        g.status = "completed"
        g.work_title = "Goldberg Variations"
        g.composer = "Johann Sebastian Bach"
        g.summary = "A listening guide."
        g.guide_html = "<article><h1>Goldberg</h1></article>"
        g.source = "fake"
        db.add(g)
        db.commit()
    finally:
        db.close()


def test_revise_unpublish_delete_lifecycle(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_discogs(monkeypatch)
    monkeypatch.setattr(
        "aulos_api.services.listening_guide.create_queued_guide",
        _fake_queued_guide,
    )
    enqueued: list[dict[str, Any]] = []

    def _fake_targeted(db, *, user_id: int, guide_id: int, review_notes: str, work_hint=None):  # noqa: ANN001
        from aulos_api.db.models import ListeningGuide

        row = db.get(ListeningGuide, guide_id)
        assert row is not None
        row.status = "queued"
        row.error_detail = ""
        db.add(row)
        db.commit()
        db.refresh(row)
        enqueued.append({"guide_id": guide_id, "review_notes": review_notes, "work_hint": work_hint})
        return row

    monkeypatch.setattr(
        "aulos_api.services.listening_guide.enqueue_targeted_revise_guide",
        _fake_targeted,
    )

    token = _register_verify_login(client, "life@example.com", "Life")
    headers = {"Authorization": f"Bearer {token}"}
    post_id = client.post(
        "/v1/listening-diary",
        headers=headers,
        json={"provider": "discogs", "external_id": "700123"},
    ).json()["id"]
    link = client.post(
        f"/v1/listening-diary/{post_id}/guides",
        headers=headers,
        json={"aspect": "作品导赏"},
    ).json()
    link_id = link["id"]
    guide_id = link["guide_id"]
    _complete_guide(guide_id)

    listed = client.get(f"/v1/listening-diary/{post_id}/guides", headers=headers).json()["items"][0]
    assert listed["status"] == "ready_for_review"
    assert listed["actions"]["can_revise"] is True
    assert listed["actions"]["can_publish"] is True

    revised = client.post(
        f"/v1/listening-diary/guides/{link_id}/revise",
        headers=headers,
        json={"notes": "More focus on the Aria ground bass."},
    )
    assert revised.status_code == 202, revised.text
    body = revised.json()
    assert body["status"] == "queued"
    assert body["review_notes"] == "More focus on the Aria ground bass."
    assert body["revised_at"]
    assert enqueued and enqueued[-1]["review_notes"] == "More focus on the Aria ground bass."

    _complete_guide(guide_id)
    pub = client.post(f"/v1/listening-diary/guides/{link_id}/publish", headers=headers)
    assert pub.status_code == 200
    assert pub.json()["status"] == "published"

    client.post(f"/v1/listening-diary/{post_id}/publish", headers=headers)
    slug = client.get(f"/v1/listening-diary/{post_id}", headers=headers).json()["share_slug"]
    assert len(client.get(f"/v1/plaza/posts/{slug}").json().get("guides") or []) == 1

    unpub = client.post(f"/v1/listening-diary/guides/{link_id}/unpublish", headers=headers)
    assert unpub.status_code == 200, unpub.text
    assert unpub.json()["status"] == "ready_for_review"
    assert client.get(f"/v1/plaza/posts/{slug}").json().get("guides") == []

    deleted = client.delete(f"/v1/listening-diary/guides/{link_id}", headers=headers)
    assert deleted.status_code == 204, deleted.text
    assert client.get(f"/v1/listening-diary/{post_id}/guides", headers=headers).json()["items"] == []

    from aulos_api.db import session as db_session
    from aulos_api.db.models import ListeningGuide

    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        assert db.get(ListeningGuide, guide_id) is None
    finally:
        db.close()
