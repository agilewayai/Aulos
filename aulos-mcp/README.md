# Aulos MCP

Model Context Protocol server for Aulos agent integrations. Governed by [aries-harness](.aries_harness/).

## Architecture

```text
MCP host / agent  ──stdio MCP──►  aulos-mcp tools
                                      │
                                      └── optional bridge to aulos-api
```

| Package | Role |
| --- | --- |
| `aulos_mcp.config` | pydantic-settings / env |
| `aulos_mcp.tools` | pure tool implementations |
| `aulos_mcp.server` | FastMCP server factory |
| `aulos_mcp.cli` | `aulos-mcp` stdio entrypoint |

Design source of truth: `.aries_harness/decisions/architecture/ARCH-001-mcp-integration-architecture.md`

## Quick start

```bash
cd aulos-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# Run as MCP stdio server (for MCP-capable hosts)
aulos-mcp
```

Example MCP client config snippet:

```json
{
  "mcpServers": {
    "aulos": {
      "command": "aulos-mcp"
    }
  }
}
```

## Verify

```bash
pytest -q
bash .aries_harness/scripts/aries-harness.sh history-status --project-root .
```

## Harness

Canonical recovery docs live under `.aries_harness/` (`MISSION.md`, `TASK_STACK.md`, `STATE.md`, `INDEX.md`).

Artifact ladder: `REQ-001` → `SPEC-001` → `STORY-001` → `ARCH-001` / `ADR-001`
