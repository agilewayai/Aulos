"""Built-in tools for the bootstrap agent."""

from __future__ import annotations

from datetime import UTC, datetime

from langchain_core.tools import tool


@tool
def get_current_utc_time() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


@tool
def echo_text(text: str) -> str:
    """Echo the provided text back unchanged. Useful for wiring checks."""
    return text
