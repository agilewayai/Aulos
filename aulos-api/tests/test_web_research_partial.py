"""SPEC-034Δ — web research force + partial on verify_failed."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_force_action_bypasses_fresh_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services import web_research as wr

    monkeypatch.setattr(
        wr,
        "load_web_research_config",
        lambda _db: {"enabled": True, "brave_api_key": "", "max_sources": 5, "agent_reach_enabled": False},
    )
    monkeypatch.setattr(
        wr,
        "decide_web_research",
        lambda *a, **k: {"action": "skip", "reason": "fresh", "richness": 10},
    )
    monkeypatch.setattr(
        wr,
        "gather_web_sources",
        lambda **k: [{"provider": "brave", "title": "BWV 1041", "snippet": "ritornello"}],
    )
    monkeypatch.setattr(
        wr,
        "verify_sources_to_dossier",
        AsyncMock(return_value={"listening_thesis": "ok"}),
    )
    monkeypatch.setattr(wr, "persist_web_dossier", lambda *a, **k: [1])

    out = await wr.run_web_research(
        db=None,  # type: ignore[arg-type]
        work_title="Concerto In A Minor BWV 1041",
        composer="Bach",
        force_action="cold_fill",
    )
    assert out.get("skipped") is False
    assert out.get("decision", {}).get("reason") == "forced_program_iteration"


@pytest.mark.asyncio
async def test_verify_failed_keeps_rag_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services import web_research as wr

    monkeypatch.setattr(
        wr,
        "load_web_research_config",
        lambda _db: {"enabled": True, "brave_api_key": "", "max_sources": 5, "agent_reach_enabled": False},
    )
    monkeypatch.setattr(
        wr,
        "decide_web_research",
        lambda *a, **k: {"action": "refresh", "reason": "no_web_provenance", "richness": 10},
    )
    monkeypatch.setattr(
        wr,
        "gather_web_sources",
        lambda **k: [{"provider": "brave", "title": "BWV 1041", "snippet": "A-minor concerto"}],
    )
    monkeypatch.setattr(wr, "verify_sources_to_dossier", AsyncMock(return_value={}))

    out = await wr.run_web_research(
        db=None,  # type: ignore[arg-type]
        work_title="Violin Concertos",
        composer="Bach",
    )
    assert out.get("skipped") is False
    assert out.get("partial") is True
    assert out.get("reason") == "verify_failed"
    assert out.get("rag_hits")
