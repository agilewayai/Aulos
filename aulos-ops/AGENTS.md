# AGENTS.md

## Project

`aulos-ops` is the Aulos admin and ops portal under aries-harness governance.

## Project root

Work inside `aulos-ops/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Aries Harness (mandatory default)

**Aries Harness is the forced default process for this project.** Soft preference is not enough — follow harness norms unless the operator explicitly waives them in the current turn.

1. Keep this project's `.aries_harness/` current (`MISSION` / `STATE` / `TASK_STACK` / `JOURNAL`).
2. Behavior changes: REQ/SPEC (or SPEC delta) **before** broad coding; update acceptance in `EVAL.md` when gates change.
3. Coding loop: **TDD** Red → Green → Refactor inside Inspect → Plan → Verify → Summarize.
4. Closeout: journal + `history-refresh`; promote insights/skills when future runs must change.
5. **Chat-only fixes without harness artifacts are incomplete.**

Also: UI/UX → **`ui-ux-pro-max`**. Canonical policy: `../aulos-skills/skills/aulos-operating-defaults/SKILL.md` (workspace `AGENTS.md` / `CLAUDE.md`).

## Coding rules

- Keep the portal focused on fleet health and operator visibility; chat UX belongs in `aulos-web`.
- For UI/UX changes, apply the `ui-ux-pro-max` skill before visual edits.
- Prefer extending `src/api.ts` + `src/App.tsx`.
- Timestamps: display via `src/time.ts` (`formatDateTime` / `formatTime`) in OS/browser timezone; wire stays UTC.
- Dev proxy targets local gateway (`vite.config.ts`); do not hardcode secrets.
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow TDD coding loop (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-ops-portal-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-ops-portal.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- App: `src/App.tsx`, `src/api.ts`

## Approval boundaries

- Production deploy / secret handling: ask the operator first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
