# AGENTS.md

## Project

`aulos-web` is the Aulos operator web GUI under aries-harness governance.

## Project root

Work inside `aulos-web/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Coding rules

- Keep the chat console as the primary surface; route all agent I/O through `aulos-api`.
- Prefer extending `src/api.ts` + `src/App.tsx` over adding parallel client stacks.
- Dev proxy targets local gateway (`vite.config.ts`); do not hardcode secrets.
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow Inspect → Plan → Edit → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-web-gui-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-web-gui.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- App: `src/App.tsx`, `src/api.ts`

## Approval boundaries

- Production deploy / secret handling: ask the operator first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
