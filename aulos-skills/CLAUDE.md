# CLAUDE.md

Mirror of `AGENTS.md` for Claude-compatible agents.

## Project

`aulos-skills` is the Aulos main harness skills pack under aries-harness governance.

## Project root

Work inside `aulos-skills/` (this directory).

## Operating defaults (fleet)

- Work under **aries-harness** for product design, system architecture, spec development, `history-refresh`, `well-organized`, and devops.
- Coding loop is **TDD** (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize.
- For UI/UX design or changes, apply the **`ui-ux-pro-max`** skill.
- Canonical policy: `aulos-skills/skills/aulos-operating-defaults/SKILL.md` (and workspace `AGENTS.md`).

## Coding rules

- Add skills under `skills/<id>/` with `skill.yaml` + `SKILL.md`.
- Keep registry/CLI seams thin and offline-testable.
- Update `.aries_harness/` when intent/architecture/acceptance changes.
- Loop: Inspect → Plan → Edit → Verify → Summarize.

## Key paths

- `.aries_harness/decisions/architecture/ARCH-001-skills-harness-architecture.md`
- `skills/`
- `src/aulos_skills/`
