# AGENTS.md

## Project

`aulos-mcp` is the Aulos MCP integration server under aries-harness governance.

## Project root

Work inside `aulos-mcp/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Coding rules

- Prefer extending `tools/` and registering them in `server/` over parallel MCP stacks.
- Keep transport/config in `config/settings.py`.
- Offline tool unit tests must pass without a live MCP host.
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow Inspect → Plan → Edit → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-mcp-integration-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-mcp-integration.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- Package: `src/aulos_mcp/`

## Approval boundaries

- Tools with irreversible external side effects: ask the operator first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
