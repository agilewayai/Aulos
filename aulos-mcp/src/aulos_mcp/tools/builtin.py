"""Built-in MCP tool implementations (pure, offline-safe)."""

from __future__ import annotations

from datetime import datetime, timezone


def echo_message(message: str) -> str:
    return f"echo: {message}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def aulos_status() -> dict[str, str]:
    return {
        "project": "aulos-mcp",
        "role": "agents integration via Model Context Protocol",
        "status": "ready",
    }
