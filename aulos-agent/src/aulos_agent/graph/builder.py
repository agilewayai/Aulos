"""Compile the LangGraph agent runtime."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from aulos_agent.config.settings import Settings, get_settings
from aulos_agent.graph.nodes import make_agent_node, make_tools_node
from aulos_agent.graph.state import AgentState
from aulos_agent.llm.factory import create_chat_model
from aulos_agent.memory.checkpointer import create_checkpointer
from aulos_agent.observability.tracing import configure_tracing
from aulos_agent.prompts.templates import build_system_message
from aulos_agent.tools.registry import get_tools


def _route_after_agent(state: AgentState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


def build_graph(
    *,
    settings: Settings | None = None,
    model: BaseChatModel | None = None,
    tools: list[BaseTool] | None = None,
    checkpointer: Any | None = None,
) -> CompiledStateGraph:
    """Build and compile the ReAct-style tool-calling agent graph."""

    cfg = settings or get_settings()
    configure_tracing(cfg)

    chat_model = model or create_chat_model(cfg)
    tool_list = tools if tools is not None else get_tools()
    saver = checkpointer if checkpointer is not None else create_checkpointer()

    agent_node = make_agent_node(chat_model, tool_list, build_system_message(cfg))
    tools_node = make_tools_node(tool_list)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _route_after_agent, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=saver)
