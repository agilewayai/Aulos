"""MCP server factory for aulos agent integrations."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aulos_mcp.config import get_settings
from aulos_mcp.tools import aulos_status, echo_message, skills_list, skills_run, utc_now


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

    @mcp.tool()
    def skills_list_tool(layer: str = "") -> list[dict]:
        """List Aulos skill packs (optionally filter by layer, e.g. domain-runtime)."""
        return skills_list(layer=layer or None)

    @mcp.tool()
    def skills_run_tool(trigger: str, message: str = "", work_hint: str = "") -> dict:
        """Run a skill trigger (e.g. listening.intake) or listening.chain for full 导赏."""
        return skills_run(trigger=trigger, message=message, work_hint=work_hint)

    return mcp
