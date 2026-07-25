"""Listening job runner — Agent + skill tools (product orchestration entry)."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, ToolMessage

from aulos_agent.config.settings import Settings, get_settings
from aulos_agent.graph.builder import build_graph
from aulos_agent.llm.factory import create_chat_model
from aulos_agent.llm.listening_fake import ListeningPlaybookFakeModel
from aulos_agent.prompts.templates import build_listening_system_message
from aulos_agent.tools.registry import get_tools


@dataclass
class ListeningAgentReport:
    steps: list[dict[str, Any]] = field(default_factory=list)
    guide_html: str = ""
    summary: str = ""
    work_title: str = ""
    composer: str = ""
    eval_pass: bool = True
    eval_score: int = 0
    skill_versions: dict[str, str] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    source: str = "agent-skills"

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": self.steps,
            "guide_html": self.guide_html,
            "summary": self.summary,
            "work_title": self.work_title,
            "composer": self.composer,
            "eval_pass": self.eval_pass,
            "eval_score": self.eval_score,
            "skill_versions": self.skill_versions,
            "context": self.context,
            "source": self.source,
        }


def _job_payload(
    *,
    message: str,
    work_hint: str | None = None,
    llm_enrichment: str | None = None,
    llm_dossier: dict[str, Any] | None = None,
    kb_dossier: dict[str, Any] | None = None,
    rag_hits: list[str] | None = None,
    rag_mode: str | None = None,
    disabled_skill_ids: list[str] | set[str] | None = None,
) -> str:
    return json.dumps(
        {
            "message": message,
            "work_hint": work_hint or "",
            "llm_enrichment": llm_enrichment or "",
            "llm_dossier": dict(llm_dossier or {}),
            "kb_dossier": dict(kb_dossier or {}),
            "rag_hits": list(rag_hits or []),
            "rag_mode": rag_mode or "",
            "disabled_skill_ids": list(disabled_skill_ids or []),
        },
        ensure_ascii=False,
    )


def _extract_report(messages: list[Any]) -> ListeningAgentReport:
    steps: list[dict[str, Any]] = []
    final: dict[str, Any] | None = None
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        try:
            payload = json.loads(str(msg.content))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if "step" in payload and isinstance(payload["step"], dict):
            steps.append(payload["step"])
        if "guide_html" in payload and "eval_pass" in payload:
            final = payload
    if final is None:
        # Fallback: build from last context
        context: dict[str, Any] = {}
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                try:
                    payload = json.loads(str(msg.content))
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict) and isinstance(payload.get("context"), dict):
                    context = payload["context"]
                    break
        return ListeningAgentReport(
            steps=list(context.get("_agent_steps") or steps),
            guide_html=str(context.get("guide_html") or ""),
            summary=str(context.get("summary") or ""),
            work_title=str(context.get("work_title") or ""),
            composer=str(context.get("composer") or context.get("composer_guess") or ""),
            eval_pass=bool(context.get("pass", True)),
            eval_score=int(context.get("eval_score") or 0),
            skill_versions=dict(context.get("skill_versions") or {}),
            context={k: v for k, v in context.items() if k != "_agent_steps"},
            source="agent-skills",
        )
    return ListeningAgentReport(
        steps=list(final.get("steps") or steps),
        guide_html=str(final.get("guide_html") or ""),
        summary=str(final.get("summary") or ""),
        work_title=str(final.get("work_title") or ""),
        composer=str(final.get("composer") or ""),
        eval_pass=bool(final.get("eval_pass", True)),
        eval_score=int(final.get("eval_score") or 0),
        skill_versions=dict(final.get("skill_versions") or {}),
        context=dict(final.get("context") or {}),
        source=str(final.get("source") or "agent-skills"),
    )


def run_listening_via_agent(
    *,
    message: str,
    work_hint: str | None = None,
    llm_enrichment: str | None = None,
    llm_dossier: dict[str, Any] | None = None,
    kb_dossier: dict[str, Any] | None = None,
    rag_hits: list[str] | None = None,
    rag_mode: str | None = None,
    disabled_skill_ids: list[str] | set[str] | None = None,
    settings: Settings | None = None,
    on_step: Callable[[dict[str, Any]], None] | None = None,
) -> ListeningAgentReport:
    """Product entry: Agent graph + skill tools produce the listening report."""
    cfg = settings or get_settings()
    tools = get_tools()
    if cfg.llm_provider == "fake":
        model = ListeningPlaybookFakeModel()
    else:
        model = create_chat_model(cfg)

    # Use listening-specific system prompt
    from aulos_agent.graph.nodes import make_agent_node, make_tools_node
    from aulos_agent.graph.state import AgentState
    from aulos_agent.memory.checkpointer import create_checkpointer
    from langgraph.graph import END, START, StateGraph

    from aulos_agent.graph.builder import _route_after_agent

    system = build_listening_system_message(cfg)
    agent_node = make_agent_node(model, tools, system)
    tools_node = make_tools_node(tools)
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _route_after_agent, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    compiled = graph.compile(checkpointer=create_checkpointer())

    payload = _job_payload(
        message=message,
        work_hint=work_hint,
        llm_enrichment=llm_enrichment,
        llm_dossier=llm_dossier,
        kb_dossier=kb_dossier,
        rag_hits=rag_hits,
        rag_mode=rag_mode,
        disabled_skill_ids=disabled_skill_ids,
    )
    thread_id = str(uuid.uuid4())
    seen_steps = 0
    result = compiled.invoke(
        {"messages": [HumanMessage(content=payload)]},
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": max(cfg.recursion_limit, 40),
        },
    )
    messages = list(result.get("messages") or [])
    if on_step is not None:
        for msg in messages:
            if not isinstance(msg, ToolMessage):
                continue
            try:
                payload_obj = json.loads(str(msg.content))
            except json.JSONDecodeError:
                continue
            step = payload_obj.get("step") if isinstance(payload_obj, dict) else None
            if isinstance(step, dict):
                seen_steps += 1
                on_step(step)
    return _extract_report(messages)


def iter_listening_via_agent(
    *,
    message: str,
    work_hint: str | None = None,
    llm_enrichment: str | None = None,
    llm_dossier: dict[str, Any] | None = None,
    kb_dossier: dict[str, Any] | None = None,
    rag_hits: list[str] | None = None,
    rag_mode: str | None = None,
    disabled_skill_ids: list[str] | set[str] | None = None,
    settings: Settings | None = None,
) -> Iterator[dict[str, Any] | ListeningAgentReport]:
    """Yield step dicts then the final ListeningAgentReport (for SSE adapters)."""
    steps_buf: list[dict[str, Any]] = []

    def _on_step(step: dict[str, Any]) -> None:
        steps_buf.append(step)

    # Run once collecting steps — yield them then report
    # For true streaming we'd use stream_mode; playbook is fast enough offline.
    report = run_listening_via_agent(
        message=message,
        work_hint=work_hint,
        llm_enrichment=llm_enrichment,
        llm_dossier=llm_dossier,
        kb_dossier=kb_dossier,
        rag_hits=rag_hits,
        rag_mode=rag_mode,
        disabled_skill_ids=disabled_skill_ids,
        settings=settings,
        on_step=_on_step,
    )
    for step in report.steps or steps_buf:
        yield {"event": "step", "data": step}
    yield report
