"""SPEC-031 promote-to-production API (case-agnostic)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "promote_prod.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")

    catalog = tmp_path / "catalog"
    craft = tmp_path / "craft"
    staging = craft / "staging"
    (catalog / "composers").mkdir(parents=True)
    (catalog / "works").mkdir(parents=True)
    staging.mkdir(parents=True)
    (catalog / "index.yaml").write_text("composers: []\nworks: []\n", encoding="utf-8")

    monkeypatch.setattr(
        "aulos_skills.promote_staging.staging_craft_root",
        lambda: staging,
    )
    monkeypatch.setattr(
        "aulos_skills.promote_production.default_catalog_root",
        lambda: catalog,
    )
    monkeypatch.setattr(
        "aulos_skills.promote_production.craft_packs_root",
        lambda: craft,
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


def test_stage_then_promote_production_generic(client: TestClient, tmp_path: Path) -> None:
    from aulos_api.db.models import ListeningGuide, User
    from aulos_api.db.session import SessionLocal

    research = {
        "synthesize_source": "archetype:chamber-generic+dimension:strings+quartet",
        "facet_classification": {
            "archetype_id": "chamber-generic",
            "confidence": 0.55,
            "instruments": ["strings"],
            "forms": ["quartet"],
        },
        "promote_candidate": {
            "schema": "aulos.promote_candidate/v1",
            "dry_run": True,
            "suggested_work_id": "bartok.string-quartet-no-4",
            "family_id": "chamber-generic",
            "facets": {
                "instruments": ["strings"],
                "forms": ["quartet"],
                "era": "modern",
            },
            "craft_draft": {
                "listening_thesis": (
                    "Hear the quartet as four-voice argument — lock which voice owns "
                    "the opening claim before chasing massed color."
                ),
                "listening_map": [
                    {"label": "Opening", "cue": "voice ownership"},
                    {"label": "Middle", "cue": "argument"},
                    {"label": "Close", "cue": "return"},
                ],
                "zh": {"listening_thesis": "把四重奏听成四声部论辩。"},
            },
            "gates": {"chamber_floor": True},
        },
        "corpus_dossier": {
            "listening_thesis": (
                "Hear the quartet as four-voice argument — lock which voice owns "
                "the opening claim before chasing massed color."
            ),
            "listening_map": [
                {"label": "Opening", "cue": "voice ownership"},
                {"label": "Middle", "cue": "argument"},
                {"label": "Close", "cue": "return"},
            ],
            "width_points": ["a", "b", "c"],
            "depth_points": ["d1", "d2", "d3"],
            "zh": {"listening_thesis": "把四重奏听成四声部论辩。"},
        },
    }
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        row = ListeningGuide(
            user_id=admin.id,
            work_title="Béla Bartók — String Quartet No. 4",
            composer="Béla Bartók",
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
    # Must stage first
    bad = client.post(
        f"/v1/ops/listening-guides/{gid}/promote-production",
        headers=headers,
        json={"overwrite": True},
    )
    assert bad.status_code == 400

    staged = client.post(
        f"/v1/ops/listening-guides/{gid}/promote-stage",
        headers=headers,
        json={"overwrite": True},
    )
    assert staged.status_code == 200, staged.text

    prod = client.post(
        f"/v1/ops/listening-guides/{gid}/promote-production",
        headers=headers,
        json={"overwrite": True},
    )
    assert prod.status_code == 200, prod.text
    body = prod.json()
    assert body["ok"] is True
    report = body["report"]
    assert report["work_id"] == "bartok.string-quartet-no-4"
    assert Path(report["craft_path"]).is_file()
    assert Path(report["catalog_work_path"]).is_file()
    assert body["promote_candidate"]["status"] == "production"

    # Same pipeline must not be a Chopin/Mendelssohn case branch
    craft_text = Path(report["craft_path"]).read_text(encoding="utf-8")
    assert "chopin.nocturne" not in craft_text
    assert "mendelssohn.lieder" not in craft_text
