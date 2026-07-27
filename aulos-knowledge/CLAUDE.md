# CLAUDE.md

Mirror of `AGENTS.md` for Claude-compatible agents.

## Project

`aulos-knowledge` is the Aulos professional music knowledge plane under aries-harness governance.

## Project root

Work inside `aulos-knowledge/` (this directory).

## Aries Harness (mandatory default)

**Aries Harness is the forced default process for this project.** Soft preference is not enough — follow harness norms unless the operator explicitly waives them in the current turn.

1. Keep this project's `.aries_harness/` current (`MISSION` / `STATE` / `TASK_STACK` / `JOURNAL`).
2. Behavior changes: REQ/SPEC (or SPEC delta) **before** broad coding; update acceptance in `EVAL.md` when gates change.
3. Coding loop: **TDD** Red → Green → Refactor inside Inspect → Plan → Verify → Summarize.
4. Closeout: journal + `history-refresh`; promote insights/skills when future runs must change.
5. **Chat-only fixes without harness artifacts are incomplete.**

Also: UI/UX → **`ui-ux-pro-max`**. Canonical policy: `../aulos-skills/skills/aulos-operating-defaults/SKILL.md` (workspace `AGENTS.md` / `CLAUDE.md`).

## Key paths

- `.aries_harness/decisions/architecture/ARCH-005-knowledge-plane.md`
- `.aries_harness/references/specs/SPEC-009-knowledge-api-and-data.md`
- `src/aulos_knowledge/`
