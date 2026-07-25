# CLAUDE.md

Mirror of `AGENTS.md` for Claude-compatible agents.

## Project

`aulos-web` is the Aulos operator web GUI under aries-harness governance.

## Project root

Work inside `aulos-web/` (this directory).

## Operating defaults (fleet)

- Work under **aries-harness** for product design, system architecture, spec development, `history-refresh`, `well-organized`, and devops.
- Coding loop is **TDD** (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize.
- For UI/UX design or changes, apply the **`ui-ux-pro-max`** skill.
- Canonical policy: `aulos-skills/skills/aulos-operating-defaults/SKILL.md` (and workspace `AGENTS.md`).

## Coding rules

- Chat console → `aulos-api` only.
- Prefer `src/api.ts` + `src/App.tsx` extensions.
- Update `.aries_harness/` when intent/architecture/acceptance changes.
- Loop: Inspect → Plan → Edit → Verify → Summarize.

## Key paths

- `.aries_harness/decisions/architecture/ARCH-001-web-gui-architecture.md`
- `.aries_harness/references/specs/SPEC-001-web-gui.md`
- `src/App.tsx`
