"""SPEC-034Δ — web research force + partial on verify_failed."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def test_program_deepen_config_defaults_to_fast_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services import web_research as wr
    from aulos_api.services.listening_guide import _program_deepen_config

    monkeypatch.setattr(wr, "load_web_research_config", lambda _db: {})

    cfg = _program_deepen_config(db=None)  # type: ignore[arg-type]
    assert cfg["mode"] == "fast"
    assert cfg["verify_sources"] is False
    assert cfg["per_work_llm"] is False
    assert cfg["album_llm"] is False
    assert cfg["agent_reach_enabled"] is False
    assert cfg["max_sources"] == 4
    assert cfg["budget_seconds"] <= 120


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


@pytest.mark.asyncio
async def test_fast_program_research_bypasses_verify_and_agent_reach(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SPEC-034 latency: default program fan-out uses raw web floor, not full LLM/Jina."""
    from aulos_api.services import web_research as wr

    gather_kwargs: dict[str, object] = {}

    def fake_gather(**kwargs: object) -> list[dict[str, str]]:
        gather_kwargs.update(kwargs)
        return [
            {
                "provider": "wikipedia",
                "title": "Hummel Op. 78",
                "url": "https://example.test/hummel-op78",
                "snippet": "Hummel Op. 78 is a trio for piano, flute and cello.",
            }
        ]

    verify = AsyncMock(return_value={"listening_thesis": "should not be called"})
    monkeypatch.setattr(
        wr,
        "load_web_research_config",
        lambda _db: {"enabled": True, "brave_api_key": "", "max_sources": 10, "agent_reach_enabled": True},
    )
    monkeypatch.setattr(wr, "gather_web_sources", fake_gather)
    monkeypatch.setattr(wr, "verify_sources_to_dossier", verify)
    monkeypatch.setattr(wr, "persist_web_dossier", lambda *a, **k: [])

    out = await wr.run_web_research(
        db=None,  # type: ignore[arg-type]
        work_title="Op. 78 Trio Für Klavier, Violoncello Und Flöte A-dur",
        composer="Johann Nepomuk Hummel",
        force_action="cold_fill",
        verify_sources=False,
        agent_reach_enabled=False,
        max_sources=4,
    )

    verify.assert_not_awaited()
    assert gather_kwargs["agent_reach_enabled"] is False
    assert gather_kwargs["max_sources"] == 4
    assert out.get("partial") is True
    assert out.get("reason") == "web_search_raw_unverified"
    assert out.get("dossier", {}).get("_provenance", {}).get("method") == "web_search_raw"
    assert "piano, flute and cello" in " ".join(out.get("rag_hits") or [])
