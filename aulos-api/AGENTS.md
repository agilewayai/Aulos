# AGENTS.md

## Project

`aulos-api` is the Aulos HTTP API gateway under aries-harness governance.

## Project root

Work inside `aulos-api/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Coding rules

- Prefer extending `routes/` and `services/` over inventing parallel gateways.
- Keep backend selection in `config/settings.py` + `services/agent_proxy.py`.
- Offline tests must pass with fake agent mode (`AULOS_API_FAKE_AGENT=true`).
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow Inspect → Plan → Edit → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-api-gateway-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-api-gateway.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- Package: `src/aulos_api/`

## Approval boundaries

- Live upstream agent/MCP side effects: ask the operator first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
