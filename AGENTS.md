# aulos workspace — agent guide

Hackathon monorepo for the Aulos initiative. Sub-projects each have their own `AGENTS.md` / `.aries_harness/`.

## Operating defaults (fleet-wide)

1. **Work under aries-harness** for product design, system architecture, spec development, dev-history refresh, doc well-organized, and devops.
2. **TDD for the coding loop** — write/extend failing tests first (Red → Green → Refactor), then verify and summarize into harness state.
3. **UI/UX** — when designing or changing UI/UX, apply the **`ui-ux-pro-max`** skill.

Canonical detail: [`aulos-skills/skills/aulos-operating-defaults/SKILL.md`](aulos-skills/skills/aulos-operating-defaults/SKILL.md)

## Sub-projects

| Path | Role |
| --- | --- |
| `aulos-agent/` | LangGraph agent runtime |
| `aulos-api/` | HTTP API gateway |
| `aulos-web/` | Operator web GUI |
| `aulos-mcp/` | MCP integrations |
| `aulos-skills/` | Main harness skills pack |
| `aulos-ops/` | Admin / ops portal |

Work inside the relevant sub-project root unless the task is explicitly workspace-wide.

## Live URLs

- https://aulos.purezen.ai
- https://aulos-ops.purezen.ai

Host daemons: `bash deploy/start-host.sh` (see `deploy/README.md`).
