"""SPEC-030 promote staging API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "promote.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")

    staging = tmp_path / "staging"
    monkeypatch.setattr(
        "aulos_skills.promote_staging.staging_craft_root",
        lambda: staging,
    )

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


def test_list_and_stage_promote_candidate(client: TestClient, tmp_path: Path) -> None:
    from aulos_api.db.models import ListeningGuide, User
    from aulos_api.db.session import SessionLocal

    research = {
        "synthesize_source": "archetype:lyric-piano-miniatures",
        "facet_classification": {
            "archetype_id": "lyric-piano-miniatures",
            "confidence": 0.7,
            "instruments": ["piano"],
            "forms": ["nocturne"],
        },
        "promote_candidate": {
            "schema": "aulos.promote_candidate/v1",
            "dry_run": True,
            "suggested_work_id": "schumann.nocturne-in-f-major",
            "family_id": "lyric-piano-miniatures",
            "facets": {"instruments": ["piano"], "forms": ["nocturne"], "era": "romantic"},
            "craft_draft": {
                "listening_thesis": (
                    "Hear the nocturne as one lyric piano room — lock cantabile and gait."
                ),
                "listening_map": [
                    {"label": "Opening", "cue": "song"},
                    {"label": "Middle", "cue": "tint"},
                    {"label": "Close", "cue": "return"},
                ],
                "zh": {"listening_thesis": "把夜曲当作抒情钢琴之室。"},
            },
            "gates": {"chamber_floor": True},
        },
        "corpus_dossier": {
            "listening_thesis": (
                "Hear the nocturne as one lyric piano room — lock cantabile and gait."
            ),
            "listening_map": [
                {"label": "Opening", "cue": "song"},
                {"label": "Middle", "cue": "tint"},
                {"label": "Close", "cue": "return"},
            ],
            "width_points": ["a", "b", "c"],
            "depth_points": ["d1", "d2", "d3"],
            "zh": {"listening_thesis": "把夜曲当作抒情钢琴之室。"},
        },
        "product_scorecard": {
            "band": "solid",
            "dimensions": {"asset_depth": 1},
        },
    }
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        row = ListeningGuide(
            user_id=admin.id,
            work_title="Clara Schumann — Nocturne in F major",
            composer="Clara Schumann",
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
    listed = client.get("/v1/ops/listening-guides/promote-candidates?limit=10", headers=headers)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] >= 1
    hit = next(i for i in body["items"] if i["guide_id"] == gid)
    assert hit["promote_candidate"]["suggested_work_id"] == "schumann.nocturne-in-f-major"

    scorecards = client.get("/v1/ops/listening-guides/scorecards?limit=10", headers=headers)
    assert scorecards.status_code == 200
    sc = next(i for i in scorecards.json()["items"] if i["guide_id"] == gid)
    assert sc["has_promote_candidate"] is True
    assert "archetype:" in str(sc.get("synthesize_source") or "")

    staged = client.post(
        f"/v1/ops/listening-guides/{gid}/promote-stage",
        headers=headers,
        json={"overwrite": False},
    )
    assert staged.status_code == 200, staged.text
    out = staged.json()
    assert out["ok"] is True
    assert out["suggested_work_id"] == "schumann.nocturne-in-f-major"
    path = Path(out["staged_path"])
    assert path.is_file()
    assert path.parent.name == "staging"

    trace = client.get(f"/v1/ops/listening-guides/{gid}/trace", headers=headers)
    assert trace.status_code == 200
    tj = trace.json()
    assert tj["promote_candidate"]["status"] == "staged"
    assert tj["synthesize_source"]
    assert tj["product_scorecard"]["band"] == "solid"

    conflict = client.post(
        f"/v1/ops/listening-guides/{gid}/promote-stage",
        headers=headers,
        json={"overwrite": False},
    )
    assert conflict.status_code == 409
