"""Graph node implementations."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode

from aulos_agent.graph.state import AgentState
from aulos_agent.prompts.templates import build_system_message


def make_agent_node(
    model: BaseChatModel,
    tools: list[BaseTool],
    system_message: SystemMessage | None = None,
):
    """Create the agent reasoning node with tools bound to the chat model."""

    bound = model.bind_tools(tools) if tools else model
    system = system_message or build_system_message()

    def agent_node(state: AgentState) -> dict[str, Any]:
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [system, *messages]
        response = bound.invoke(messages)
        return {"messages": [response]}

    return agent_node


def make_tools_node(tools: list[BaseTool]) -> ToolNode:
    return ToolNode(tools)
