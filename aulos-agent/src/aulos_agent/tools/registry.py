"""Tool registry — central place to declare tools available to the graph."""

from __future__ import annotations

from langchain_core.tools import BaseTool

from aulos_agent.tools.builtin import echo_text, get_current_utc_time


def default_tools() -> list[BaseTool]:
    return [get_current_utc_time, echo_text]


def get_tools(extra: list[BaseTool] | None = None) -> list[BaseTool]:
    tools = list(default_tools())
    if extra:
        tools.extend(extra)
    return tools
