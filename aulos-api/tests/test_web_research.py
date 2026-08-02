"""Web research → KB persist loop (generic, no composer branches)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from aulos_api.services.web_research import (
    decide_web_research,
    persist_web_dossier,
    rag_is_thin,
    run_web_research,
    save_web_research_config,
)


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "web.db"
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


def _admin_token(client: TestClient) -> str:
    r = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_query_variants_broaden_opus() -> None:
    from aulos_api.services.web_search import _query_variants, _search_query

    cleaned = _search_query("Schubert Impromptu Op. 90 No. 3 listening guide", "")
    assert "listening" not in cleaned.lower()
    variants = _query_variants(cleaned)
    assert variants[0].startswith("Schubert")
    assert any("Op" not in v and "90" not in v for v in variants)


def test_rag_is_thin_heuristic() -> None:
    assert rag_is_thin({"rag_hits": [], "kb_dossier": {}})
    assert rag_is_thin({"rag_hits": ["a", "b"], "kb_dossier": {"listening_thesis": "x"}})
    rich = {
        "rag_hits": ["1", "2", "3", "4"],
        "kb_dossier": {
            "listening_thesis": "t",
            "composer_profile": {"summary": "s"},
            "genesis": {"year": "1"},
            "sound_world": {"original_instrument": "p"},
            "depth_points": ["a", "b", "c"],
            "interpretations": [{"artist": "x"}],
            "composer_portrait": {"image_url": "http://x"},
            "historical_stature": {"reasons": ["r"]},
        },
    }
    assert not rag_is_thin(rich)


def test_persist_web_dossier_indexes_chunks(client: TestClient) -> None:
    from aulos_api.db.session import SessionLocal
    from aulos_api.db.models import KnowledgeDocument, KnowledgeChunk

    dossier = {
        "work_title": "Test Composer — Character dances",
        "composer": "Test Composer",
        "work_id": "test.character-dances",
        "listening_thesis": "Hear the gait first.",
        "width_points": ["Accent literacy", "Ternary rooms"],
        "depth_points": ["Lock opening accent", "Track return"],
        "_provenance": {
            "method": "web_search+llm",
            "verified": True,
            "sources": [{"title": "Wiki", "url": "https://example.com", "snippet": "Dance character."}],
        },
    }
    with SessionLocal() as db:
        ids = persist_web_dossier(db, dossier=dossier, user_id=1, persist_global=True)
        assert len(ids) == 2
        docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.title.contains("Character dances")).all()
        assert len(docs) >= 2
        chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id.in_([d.id for d in docs])).count()
        assert chunks >= 2


@pytest.mark.asyncio
async def test_run_web_research_cold_fill_then_skip_when_fresh(client: TestClient) -> None:
    from datetime import datetime, timezone

    from aulos_api.db.session import SessionLocal

    sources = [
        {
            "provider": "wikipedia",
            "title": "Mazurka",
            "url": "https://en.wikipedia.org/wiki/Mazurka",
            "snippet": "The mazurka is a Polish folk dance in triple meter.",
        }
    ]
    now = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)
    verified_at = "2026-07-25T11:00:00Z"
    with SessionLocal() as db:
        with patch(
            "aulos_api.services.web_research.gather_web_sources",
            return_value=sources,
        ):
            with patch(
                "aulos_api.services.web_research.verify_sources_to_dossier",
                new_callable=AsyncMock,
                return_value={
                    "work_title": "Frédéric Chopin — Mazurkas",
                    "composer": "Frédéric Chopin",
                    "work_id": "chopin.mazurkas",
                    "listening_thesis": "Gait first.",
                    "width_points": ["Accent"],
                    "_provenance": {
                        "method": "web_search+llm",
                        "verified": True,
                        "verified_at": verified_at,
                        "sources": sources,
                    },
                },
            ):
                first = await run_web_research(
                    db,
                    work_title="Frédéric Chopin — Mazurkas",
                    composer="Frédéric Chopin",
                    work_id="chopin.mazurkas",
                    user_id=1,
                    rag={"rag_hits": [], "kb_dossier": {}},
                )
        assert first.get("skipped") is False
        assert first.get("action") == "cold_fill"
        assert first.get("persisted_doc_ids")

        rich_dossier = {
            **first["dossier"],
            "composer_profile": {"summary": "s"},
            "genesis": {"year": "1"},
            "sound_world": {"original_instrument": "p"},
            "depth_points": ["1", "2", "3"],
            "interpretations": [{"artist": "x"}],
            "composer_portrait": {"image_url": "http://x"},
            "historical_stature": {"reasons": ["r"]},
            "_provenance": {
                "method": "web_search+llm",
                "verified": True,
                "verified_at": verified_at,
                "sources": sources,
            },
        }
        rich_rag = {"rag_hits": ["a", "b", "c", "d"], "kb_dossier": rich_dossier}
        # Fresh within TTL → skip
        decision = decide_web_research(
            db,
            work_title="Frédéric Chopin — Mazurkas",
            composer="Frédéric Chopin",
            user_id=1,
            rag=rich_rag,
            cfg={"min_rag_hits": 3, "min_dossier_richness": 5, "refresh_after_hours": 168},
            now=now,
        )
        assert decision["action"] == "skip"
        assert decision["reason"] == "fresh"

        # decide uses real now — set TTL huge via config so second skips
        save_web_research_config(db, refresh_after_hours=24 * 365)
        second = await run_web_research(
            db,
            work_title="Frédéric Chopin — Mazurkas",
            composer="Frédéric Chopin",
            work_id="chopin.mazurkas",
            user_id=1,
            rag=rich_rag,
        )
        assert second.get("skipped") is True
        assert second.get("reason") == "fresh"

        # Stale TTL → refresh (merge)
        save_web_research_config(db, refresh_after_hours=1)
        with patch(
            "aulos_api.services.web_research.gather_web_sources",
            return_value=sources,
        ):
            with patch(
                "aulos_api.services.web_research.verify_sources_to_dossier",
                new_callable=AsyncMock,
                return_value={
                    "work_title": "Frédéric Chopin — Mazurkas",
                    "composer": "Frédéric Chopin",
                    "listening_thesis": "Updated gait thesis.",
                    "width_points": ["New accent note"],
                    "_provenance": {
                        "method": "web_search+llm",
                        "verified": True,
                        "verified_at": "2026-07-25T18:00:00Z",
                        "sources": sources,
                    },
                },
            ):
                # Force stale by old verified_at in rag + short TTL; wall clock is now
                # so age from 11:00Z on same day with refresh_after_hours=1 may or may not
                # be stale depending on real now. Use decide with explicit now instead.
                stale_decision = decide_web_research(
                    db,
                    work_title="Frédéric Chopin — Mazurkas",
                    composer="Frédéric Chopin",
                    user_id=1,
                    rag=rich_rag,
                    cfg={"min_rag_hits": 3, "min_dossier_richness": 5, "refresh_after_hours": 1},
                    now=datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc),
                )
                assert stale_decision["action"] == "refresh"
                assert stale_decision["reason"] == "stale"

                # refresh_after_hours=0 means always refresh when not thin
                always = decide_web_research(
                    db,
                    work_title="Frédéric Chopin — Mazurkas",
                    composer="Frédéric Chopin",
                    user_id=1,
                    rag=rich_rag,
                    cfg={"min_rag_hits": 3, "min_dossier_richness": 5, "refresh_after_hours": 0},
                    now=now,
                )
                assert always["action"] == "refresh"


def test_ops_web_research_config(client: TestClient) -> None:
    token = _admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    g = client.get("/v1/ops/web-research", headers=headers)
    assert g.status_code == 200
    assert g.json()["enabled"] is True
    assert "refresh_after_hours" in g.json()
    assert g.json().get("agent_reach_enabled") is True
    p = client.put(
        "/v1/ops/web-research",
        headers=headers,
        json={
            "enabled": False,
            "min_rag_hits": 2,
            "refresh_after_hours": 48,
            "agent_reach_enabled": False,
        },
    )
    assert p.status_code == 200
    assert p.json()["enabled"] is False
    assert p.json()["min_rag_hits"] == 2
    assert p.json()["refresh_after_hours"] == 48
    assert p.json()["agent_reach_enabled"] is False
    # restore
    client.put(
        "/v1/ops/web-research",
        headers=headers,
        json={"enabled": True, "refresh_after_hours": 168, "agent_reach_enabled": True},
    )


def test_agent_reach_jina_deepen_and_ssrf_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services import web_search as ws

    class _Resp:
        status_code = 200
        text = (
            "Title: Dumky. This is a long enough classical program-note excerpt "
            "about Dvorak piano trio character dances and folk rhythm."
        )

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            assert url.startswith("https://r.jina.ai/")
            return _Resp()

    monkeypatch.setattr(ws.httpx, "Client", _Client)
    assert ws.fetch_jina_reader(url="http://127.0.0.1/secret") is None
    assert ws.fetch_jina_reader(url="not-a-url") is None
    row = ws.fetch_jina_reader(url="https://en.wikipedia.org/wiki/Dumky")
    assert row is not None
    assert row["provider"] == "agent-reach-jina"
    assert row["enabler"] == "enabler-agent-reach"
    sources = [{"provider": "wikipedia", "url": "https://en.wikipedia.org/wiki/Dumky", "snippet": "short"}]
    ws.deepen_with_agent_reach(sources, max_pages=1)
    assert sources[0]["deepened_by"] == "agent-reach-jina"
    assert "Dvorak" in sources[0]["snippet"] or "classical" in sources[0]["snippet"]
