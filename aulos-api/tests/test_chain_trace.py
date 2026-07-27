"""SPEC-012 chain diagnostic log tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import clear_session
from aulos_api.services.chain_trace import SCHEMA, ChainTraceBuilder, _names_overlap


def test_names_overlap_and_weak_tokens() -> None:
    assert _names_overlap("Wolfgang Amadeus Mozart", "Mozart")
    assert not _names_overlap("Wolfgang Amadeus Mozart", "Ludwig van Beethoven")
    # Only shared weak form words should not prove overlap for drift
    assert _names_overlap("Piano Sonata", "Piano Concerto")  # only weak → True (no flag)


def test_chain_trace_builder_discogs_lock_and_family_signal() -> None:
    b = ChainTraceBuilder(message="/discogs #6280908", work_hint="")
    b.milestone(
        "discogs.resolve",
        summary="Resolved Discogs release",
        facts={"release_id": 6280908, "composer": "Wolfgang Amadeus Mozart"},
    )
    b.note_identity(
        stage="discogs",
        composer="Wolfgang Amadeus Mozart",
        work_title="Piano Concerto No. 23 K. 488",
    )
    b.note_identity(
        stage="locked",
        composer="Wolfgang Amadeus Mozart",
        work_title="Piano Concerto No. 23 K. 488",
    )
    b.ingest_skill_context(
        {
            "identity_status": "unknown",
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "synthesize_hit": True,
            "synthesize_source": "kb-rag+family:duo-cello-piano",
            "work_id": None,
        }
    )
    # Simulate pollution outcome
    trace = b.finalize(
        work_title="Ludwig van Beethoven — Cello Sonatas",
        composer="Ludwig van Beethoven",
    )
    assert trace["schema"] == SCHEMA
    assert trace["trace_id"]
    assert any(m["id"] == "discogs.resolve" for m in trace["milestones"])
    assert any(m["id"] == "skill.synthesize" for m in trace["milestones"])
    codes = {d["code"] for d in trace["deviations"]}
    assert "family_without_work_id" in codes
    assert "composer_drift" in codes
    assert "title_drift" in codes


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "trace.db"
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
        json={"email": "trace@example.com", "password": "ListenPass123!", "display_name": "Trace"},
    )
    from aulos_api.services.mailgun import get_fake_mailbox

    token = get_fake_mailbox()[-1]["verification_token"]
    client.post("/v1/auth/verify-email", json={"token": token})
    login = client.post(
        "/v1/auth/login",
        json={"email": "trace@example.com", "password": "ListenPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_compose_persists_chain_trace_and_owner_get(client: TestClient) -> None:
    headers = _user_headers(client)
    res = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "I'm listening to Bach Goldberg Variations"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    guide_id = body["id"]

    from aulos_api.db.session import SessionLocal
    from aulos_api.db.models import ListeningGuide
    import json

    with SessionLocal() as db:
        row = db.query(ListeningGuide).filter(ListeningGuide.id == guide_id).one()
        research = json.loads(row.research_json or "{}")
    trace = research.get("chain_trace")
    assert isinstance(trace, dict)
    assert trace.get("schema") == SCHEMA
    assert len(trace.get("milestones") or []) >= 1
    assert any(a.get("stage") == "final" for a in trace.get("identity_arc") or [])

    got = client.get(f"/v1/listening-guides/{guide_id}/trace", headers=headers)
    assert got.status_code == 200, got.text
    payload = got.json()
    assert payload["guide_id"] == guide_id
    assert payload["chain_trace"]["trace_id"] == trace["trace_id"]

    clear_session(client)
    unauth = client.get(f"/v1/listening-guides/{guide_id}/trace")
    assert unauth.status_code == 401


def test_ops_chain_trace_route(client: TestClient) -> None:
    headers = _user_headers(client)
    res = client.post(
        "/v1/listening-guides",
        headers=headers,
        json={"message": "I'm listening to Bach Goldberg Variations"},
    )
    guide_id = res.json()["id"]

    admin = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert admin.status_code == 200
    ops_headers = {"Authorization": f"Bearer {admin.json()['access_token']}"}
    got = client.get(f"/v1/ops/listening-guides/{guide_id}/trace", headers=ops_headers)
    assert got.status_code == 200, got.text
    assert got.json()["chain_trace"]["schema"] == SCHEMA
