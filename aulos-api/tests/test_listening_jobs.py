"""SPEC-013: durable jobs + library delete/search/favorite/tags."""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "jobs.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("AULOS_REDIS_URL", "")  # force thread fallback for jobs

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


def _headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/v1/auth/register",
        json={"email": "jobs@example.com", "password": "ListenPass123!", "display_name": "Jobs"},
    )
    from aulos_api.services.mailgun import get_fake_mailbox

    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    login = client.post("/v1/auth/login", json={"email": "jobs@example.com", "password": "ListenPass123!"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _wait_completed(client: TestClient, headers: dict[str, str], guide_id: int, timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    last = {}
    while time.time() < deadline:
        res = client.get(f"/v1/listening-guides/{guide_id}", headers=headers)
        assert res.status_code == 200, res.text
        last = res.json()
        if last["status"] in {"completed", "failed"}:
            return last
        time.sleep(0.15)
    raise AssertionError(f"job {guide_id} did not finish: {last}")


def test_enqueue_job_survives_without_client_stream(client: TestClient) -> None:
    headers = _headers(client)
    res = client.post(
        "/v1/listening-guides/jobs",
        headers=headers,
        json={"message": "I'm beginning to listen to Bach Goldberg Variations"},
    )
    assert res.status_code == 202, res.text
    body = res.json()
    assert body["status"] == "queued"
    assert body["id"] > 0
    # No event stream attached — worker must still finish.
    done = _wait_completed(client, headers, body["id"])
    assert done["status"] == "completed"
    assert "Goldberg" in done["work_title"] or done["guide_html"]


def test_list_filters_favorite_tags_and_delete(client: TestClient) -> None:
    headers = _headers(client)
    # Seed via sync create for stable completed rows
    a = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "I'm beginning to listen to Bach Goldberg Variations"},
    )
    assert a.status_code == 201, a.text
    b = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "I'm beginning to listen to Beethoven Op. 69 cello sonata"},
    )
    assert b.status_code == 201, b.text
    aid, bid = a.json()["id"], b.json()["id"]

    fav = client.post(f"/v1/listening-guides/{aid}/favorite", headers=headers)
    assert fav.status_code == 200
    assert fav.json()["favorited"] is True

    tags = client.patch(
        f"/v1/listening-guides/{aid}/tags",
        headers=headers,
        json={"tags": ["Salon", "teach", "salon"]},
    )
    assert tags.status_code == 200
    assert tags.json()["tags"] == ["salon", "teach"]

    listed = client.get("/v1/listening-guides?q=Goldberg", headers=headers)
    assert listed.status_code == 200
    ids = [row["id"] for row in listed.json()]
    assert aid in ids
    assert bid not in ids

    favs = client.get("/v1/listening-guides?favorited=1", headers=headers)
    assert [row["id"] for row in favs.json()] == [aid]

    by_tag = client.get("/v1/listening-guides?tag=salon", headers=headers)
    assert [row["id"] for row in by_tag.json()] == [aid]

    client.delete(f"/v1/listening-guides/{aid}/favorite", headers=headers)
    unfav = client.get(f"/v1/listening-guides/{aid}", headers=headers).json()
    assert unfav["favorited"] is False

    deleted = client.delete(f"/v1/listening-guides/{bid}", headers=headers)
    assert deleted.status_code == 204
    missing = client.get(f"/v1/listening-guides/{bid}", headers=headers)
    assert missing.status_code == 404


def test_job_events_sse_reaches_done(client: TestClient) -> None:
    headers = _headers(client)
    res = client.post(
        "/v1/listening-guides/jobs",
        headers=headers,
        json={"message": "I'm beginning to listen to Bach Goldberg Variations"},
    )
    assert res.status_code == 202, res.text
    guide_id = res.json()["id"]
    # Plan is seeded at enqueue for countable progress.
    seeded = client.get(f"/v1/listening-guides/{guide_id}", headers=headers).json()
    assert len(seeded["steps"]) >= 7
    assert seeded["steps"][0].get("index") == 1
    with client.stream("GET", f"/v1/listening-guides/{guide_id}/events", headers=headers) as stream:
        assert stream.status_code == 200
        buf = ""
        for chunk in stream.iter_text():
            buf += chunk
            if "event: done" in buf or "event: error" in buf:
                break
    assert "event: progress" in buf
    assert "event: done" in buf


def test_retry_failed_job(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _headers(client)
    res = client.post(
        "/v1/listening-guides/jobs",
        headers=headers,
        json={"message": "I'm beginning to listen to Bach Goldberg Variations"},
    )
    assert res.status_code == 202, res.text
    guide_id = res.json()["id"]
    done = _wait_completed(client, headers, guide_id)
    # Force failed state then retry
    from aulos_api.db import session as db_session
    from aulos_api.db.models import ListeningGuide

    db = db_session.SessionLocal()
    try:
        row = db.query(ListeningGuide).filter(ListeningGuide.id == guide_id).one()
        row.status = "failed"
        row.error_detail = "injected failure"
        db.add(row)
        db.commit()
    finally:
        db.close()

    retried = client.post(f"/v1/listening-guides/{guide_id}/retry", headers=headers)
    assert retried.status_code == 202, retried.text
    assert retried.json()["status"] in {"queued", "running"}
    again = _wait_completed(client, headers, guide_id)
    assert again["status"] == "completed"


def test_failed_eval_report_is_not_persisted_completed() -> None:
    from aulos_api.db.models import ListeningGuide
    from aulos_api.services.listening_guide import _apply_report_to_row

    row = ListeningGuide(user_id=1, status="running")
    report = SimpleNamespace(
        work_title="Trios Für Klavier, Flöte Und Violoncello",
        composer="Unknown composer",
        summary="Thin generic summary.",
        guide_html="<article><h1>Thin guide</h1></article>",
        steps=[],
        skill_versions={"aulos-listening-synthesize": "test"},
        eval_pass=False,
        eval_score=7,
        context={
            "process_scorecard": {
                "rollup": {"hard_fail": True, "pct": 58},
                "gates": {"eval_pass": False, "ambient_ok": False},
                "hard_flaws": [{"code": "ambient_missing", "note": "ambient required"}],
            }
        },
    )

    out = _apply_report_to_row(row, report=report, source="test")
    assert out.status == "failed"
    assert "eval_pass=false" in out.error_detail
    assert "ambient_ok=false" in out.error_detail
    assert out.guide_html
