# AGENTS.md

## Project

`aulos-skills` is the Aulos main harness skills pack under aries-harness governance.

## Project root

Work inside `aulos-skills/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Aries Harness (mandatory default)

**Aries Harness is the forced default process for this project.** Soft preference is not enough — follow harness norms unless the operator explicitly waives them in the current turn.

1. Keep this project's `.aries_harness/` current (`MISSION` / `STATE` / `TASK_STACK` / `JOURNAL`).
2. Behavior changes: REQ/SPEC (or SPEC delta) **before** broad coding; update acceptance in `EVAL.md` when gates change.
3. Coding loop: **TDD** Red → Green → Refactor inside Inspect → Plan → Verify → Summarize.
4. Closeout: journal + `history-refresh`; promote insights/skills when future runs must change.
5. **Chat-only fixes without harness artifacts are incomplete.**

Also: UI/UX → **`ui-ux-pro-max`**. Canonical policy: `skills/aulos-operating-defaults/SKILL.md` (workspace `AGENTS.md` / `CLAUDE.md`).

## Coding rules

- Prefer adding skill packs under `skills/<id>/` with `skill.yaml` + `SKILL.md`.
- Keep discovery in `registry.py` and operator UX in `cli.py`.
- Offline pytest must pass without network.
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow TDD coding loop (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.
- **Promote every listening-product iteration into harness assets** (REQ/SPEC/CKPT + skill docs + eval gates + tests). Chat-only fixes are incomplete.

## Listening product gates (SPEC-006)

- Compose must emit bilingual panes (when `zh` exists) **and** floating ambient (`data-ambient-player=v2`).
- Media: cache → proxy → origin; API `Content-Disposition: inline`.
- Synthesize: family lists win on cold path; scrub foreign flagship chambers; KB needs positive title match.
- Eval hard-fails missing ambient.
- After changes: extend `tests/test_runtime.py` / ambient tests, update `EVAL.md`, journal + `history-refresh`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-skills-harness-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-skills-harness.md`
- Ambient/identity: `.aries_harness/references/specs/SPEC-006-ambient-media-and-identity.md`
- Insights: `.aries_harness/docs/insights.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- Skills: `skills/`
- Package: `src/aulos_skills/`

## Approval boundaries

- Publishing or overwriting shared skill packs used by other teams: ask first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
