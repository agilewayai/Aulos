# AGENTS.md

## Project

`aulos-knowledge` is the Aulos professional music knowledge plane under aries-harness governance.

## Project root

Work inside `aulos-knowledge/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Aries Harness (mandatory default)

**Aries Harness is the forced default process for this project.** Soft preference is not enough — follow harness norms unless the operator explicitly waives them in the current turn.

1. Keep this project's `.aries_harness/` current (`MISSION` / `STATE` / `TASK_STACK` / `JOURNAL`).
2. Behavior changes: REQ/SPEC (or SPEC delta) **before** broad coding; update acceptance in `EVAL.md` when gates change.
3. Coding loop: **TDD** Red → Green → Refactor inside Inspect → Plan → Verify → Summarize.
4. Closeout: journal + `history-refresh`; promote insights/skills when future runs must change.
5. **Chat-only fixes without harness artifacts are incomplete.**

Also: UI/UX → **`ui-ux-pro-max`**. Canonical policy: `../aulos-skills/skills/aulos-operating-defaults/SKILL.md` (workspace `AGENTS.md` / `CLAUDE.md`).

## Coding rules

- Keep public retrieve APIs separate from `/v1/admin/*` mutation routes.
- Enforce `AULOS_KNOWLEDGE_ADMIN_TOKEN` on admin routes; API gateway proxy attaches the bearer token.
- Prefer extending `routes.py`, `jobs.py`, and `retrieve.py` over parallel services.
- Offline pytest must pass without network.
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow TDD coding loop (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-005-knowledge-plane.md`
- Spec: `.aries_harness/references/specs/SPEC-009-knowledge-api-and-data.md`
- Package: `src/aulos_knowledge/`

## Approval boundaries

- Direct production exposure of admin routes without service token: never.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
