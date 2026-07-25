"""MCP server factory for aulos agent integrations."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aulos_mcp.config import get_settings
from aulos_mcp.tools import aulos_status, echo_message, utc_now


def create_server() -> FastMCP:
    settings = get_settings()
    mcp = FastMCP(settings.server_name)

    @mcp.tool()
    def echo(message: str) -> str:
        """Echo a message back to the caller."""
        return echo_message(message)

    @mcp.tool()
    def now_utc() -> str:
        """Return the current UTC timestamp in ISO-8601 form."""
        return utc_now()

    @mcp.tool()
    def status() -> dict[str, str]:
        """Return Aulos MCP integration status."""
        return aulos_status()

    return mcp
