"""Agent listening orchestration tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _fake_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AULOS_LLM_PROVIDER", "fake")
    from aulos_agent.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_registry_includes_listening_skill_tools() -> None:
    from aulos_agent.tools.registry import get_tools

    names = {t.name for t in get_tools()}
    assert "list_aulos_skills" in names
    assert "run_listening_skill" in names
    assert "finalize_listening_guide" in names
    assert "run_listening_skill_chain" not in names


def test_run_listening_via_agent_goldberg() -> None:
    from aulos_agent.listening.service import run_listening_via_agent

    report = run_listening_via_agent(
        message="I'm beginning to listen to Bach Goldberg Variations — help me learn"
    )
    assert report.work_title
    assert "Goldberg" in report.work_title or "BWV" in report.work_title
    assert len(report.steps) >= 5
    assert any(s.get("skill_id") for s in report.steps)
    assert report.guide_html.startswith("<!DOCTYPE html>") or "<html" in report.guide_html.lower()
    assert "data-ambient-player" in report.guide_html or "aulos-ambient" in report.guide_html
    assert report.source == "agent-skills"
    assert report.skill_versions
