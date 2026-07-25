"""Tool registry — central place to declare tools available to the graph."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from aulos_agent.tools.builtin import echo_text, get_current_utc_time


def default_tools() -> list[BaseTool]:
    tools: list[BaseTool] = [get_current_utc_time, echo_text]
    try:
        from aulos_agent.tools.skills import list_aulos_skills, run_listening_skill_chain

        tools.extend([list_aulos_skills, run_listening_skill_chain])
    except Exception:  # noqa: BLE001 — optional sibling skills package
        pass
    return tools


def get_tools(extra: list[BaseTool] | None = None) -> list[BaseTool]:
    tools = list(default_tools())
    if extra:
        tools.extend(extra)
    return tools
