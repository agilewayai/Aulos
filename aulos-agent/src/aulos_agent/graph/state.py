"""Agent graph state."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state flowing through the LangGraph nodes."""

    messages: Annotated[list[BaseMessage], add_messages]
