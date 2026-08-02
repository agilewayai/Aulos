"""Ops LLM completer wiring for Intent Critic / external review."""

from __future__ import annotations

from aulos_agent.tools.skills import _attach_external_review_expert, _attach_intent_critic


def test_attach_intent_critic_uses_review_role() -> None:
    ctx: dict = {"review_llm_enabled": True}
    _attach_intent_critic(ctx)
    assert callable(ctx.get("llm_critic_complete"))
    first = ctx["llm_critic_complete"]
    _attach_intent_critic(ctx)
    assert ctx["llm_critic_complete"] is first


def test_attach_external_review_expert_uses_review_role() -> None:
    ctx: dict = {"review_llm_enabled": True}
    _attach_external_review_expert(ctx)
    assert callable(ctx.get("llm_external_review_complete"))


def test_review_llms_skip_when_disabled() -> None:
    ctx: dict = {"review_llm_enabled": False}
    _attach_intent_critic(ctx)
    _attach_external_review_expert(ctx)
    assert "llm_critic_complete" not in ctx
    assert "llm_external_review_complete" not in ctx
