"""SPEC-019 process scorecard API surfaces."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "scorecard.db"
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

    get_settings.cache_clear()
    db_session.reset_engine()

    from aulos_api.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    db_session.reset_engine()


def _admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_list_guide_scorecard_summaries_and_trace(client: TestClient) -> None:
    from aulos_api.db.models import ListeningGuide, User
    from aulos_api.db.session import SessionLocal

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        research = {
            "eval_pass": True,
            "eval_score": 9,
            "process_scorecard": {
                "schema": "aulos.process_scorecard/v1",
                "nodes": [{"trigger": "listening.intake", "pct": 100, "band": "strong"}],
                "product": {"pct": 80, "band": "solid"},
                "rollup": {"earned": 40, "max_possible": 50, "pct": 80.0, "band": "solid", "hard_fail": False},
                "gates": {"eval_pass": True, "review_failed": False, "ambient_ok": True},
            },
        }
        row = ListeningGuide(
            user_id=admin.id,
            work_title="Piano Concerto K.488",
            composer="Mozart",
            status="ready",
            source="agent-skills",
            summary="test",
            guide_html="<html></html>",
            steps_json="[]",
            skill_versions_json="{}",
            research_json=json.dumps(research),
            message="test",
        )
        db.add(row)
        db.commit()
        gid = row.id
    finally:
        db.close()

    headers = _admin_headers(client)
    listed = client.get("/v1/ops/listening-guides/scorecards?limit=10", headers=headers)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] >= 1
    hit = next(i for i in body["items"] if i["guide_id"] == gid)
    assert hit["band"] == "solid"
    assert hit["pct"] == 80.0
    assert hit["has_scorecard"] is True

    trace = client.get(f"/v1/ops/listening-guides/{gid}/trace", headers=headers)
    assert trace.status_code == 200, trace.text
    assert trace.json()["process_scorecard"]["rollup"]["band"] == "solid"
