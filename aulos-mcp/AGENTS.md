# AGENTS.md

## Project

`aulos-mcp` is the Aulos MCP integration server under aries-harness governance.

## Project root

Work inside `aulos-mcp/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Operating defaults (fleet)

- Work under **aries-harness** for product design, system architecture, spec development, `history-refresh`, `well-organized`, and devops.
- Coding loop is **TDD** (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize.
- For UI/UX design or changes, apply the **`ui-ux-pro-max`** skill.
- Canonical policy: `aulos-skills/skills/aulos-operating-defaults/SKILL.md` (and workspace `AGENTS.md`).

## Coding rules

- Prefer extending `tools/` and registering them in `server/` over parallel MCP stacks.
- Keep transport/config in `config/settings.py`.
- Offline tool unit tests must pass without a live MCP host.
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow TDD coding loop (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-mcp-integration-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-mcp-integration.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- Package: `src/aulos_mcp/`

## Approval boundaries

- Tools with irreversible external side effects: ask the operator first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
