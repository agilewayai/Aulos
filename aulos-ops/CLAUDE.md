# CLAUDE.md

Mirror of `AGENTS.md` for Claude-compatible agents.

## Project

`aulos-ops` is the Aulos admin and ops portal under aries-harness governance.

## Project root

Work inside `aulos-ops/` (this directory).

## Operating defaults (fleet)

- Work under **aries-harness** for product design, system architecture, spec development, `history-refresh`, `well-organized`, and devops.
- Coding loop is **TDD** (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize.
- For UI/UX design or changes, apply the **`ui-ux-pro-max`** skill.
- Canonical policy: `aulos-skills/skills/aulos-operating-defaults/SKILL.md` (and workspace `AGENTS.md`).

## Coding rules

- Fleet health / ops visibility only; chat stays in `aulos-web`.
- Prefer `src/api.ts` + `src/App.tsx` extensions.
- Update `.aries_harness/` when intent/architecture/acceptance changes.
- Loop: Inspect → Plan → Edit → Verify → Summarize.

## Key paths

- `.aries_harness/decisions/architecture/ARCH-001-ops-portal-architecture.md`
- `.aries_harness/references/specs/SPEC-001-ops-portal.md`
- `src/App.tsx`
