# CLAUDE.md

Mirror of `AGENTS.md` for Claude-compatible agents.

## Project

`aulos-api` is the Aulos HTTP API gateway under aries-harness governance.

## Project root

Work inside `aulos-api/` (this directory).

## Coding rules

- Prefer extending `routes/` and `services/`.
- Fake agent mode must keep tests offline-green.
- Update `.aries_harness/` when intent/architecture/acceptance changes.
- Loop: Inspect → Plan → Edit → Verify → Summarize.

## Key paths

- `.aries_harness/decisions/architecture/ARCH-001-api-gateway-architecture.md`
- `.aries_harness/references/specs/SPEC-001-api-gateway.md`
- `src/aulos_api/`
