# AGENTS.md

## Project

`aulos-skills` is the Aulos main harness skills pack under aries-harness governance.

## Project root

Work inside `aulos-skills/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Operating defaults (fleet)

- Work under **aries-harness** for product design, system architecture, spec development, `history-refresh`, `well-organized`, and devops.
- Coding loop is **TDD** (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize.
- For UI/UX design or changes, apply the **`ui-ux-pro-max`** skill.
- Canonical policy: `aulos-skills/skills/aulos-operating-defaults/SKILL.md` (and workspace `AGENTS.md`).

## Coding rules

- Prefer adding skill packs under `skills/<id>/` with `skill.yaml` + `SKILL.md`.
- Keep discovery in `registry.py` and operator UX in `cli.py`.
- Offline pytest must pass without network.
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow TDD coding loop (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-skills-harness-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-skills-harness.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- Skills: `skills/`
- Package: `src/aulos_skills/`

## Approval boundaries

- Publishing or overwriting shared skill packs used by other teams: ask first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
