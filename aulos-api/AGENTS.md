# AGENTS.md

## Project

`aulos-api` is the Aulos HTTP API gateway under aries-harness governance.

## Project root

Work inside `aulos-api/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Aries Harness (mandatory default)

**Aries Harness is the forced default process for this project.** Soft preference is not enough — follow harness norms unless the operator explicitly waives them in the current turn.

1. Keep this project's `.aries_harness/` current (`MISSION` / `STATE` / `TASK_STACK` / `JOURNAL`).
2. Behavior changes: REQ/SPEC (or SPEC delta) **before** broad coding; update acceptance in `EVAL.md` when gates change.
3. Coding loop: **TDD** Red → Green → Refactor inside Inspect → Plan → Verify → Summarize.
4. Closeout: journal + `history-refresh`; promote insights/skills when future runs must change.
5. **Chat-only fixes without harness artifacts are incomplete.**

Also: UI/UX → **`ui-ux-pro-max`**. Canonical policy: `../aulos-skills/skills/aulos-operating-defaults/SKILL.md` (workspace `AGENTS.md` / `CLAUDE.md`).

## Coding rules

- Prefer extending `routes/` and `services/` over inventing parallel gateways.
- Keep backend selection in `config/settings.py` + `services/agent_proxy.py`.
- Offline tests must pass with fake agent mode (`AULOS_API_FAKE_AGENT=true`).
- Timestamps: store/emit UTC via `aulos_api.timefmt.to_utc_iso` (SPEC-007); never return naive local wall-clock.
- Listening: delegate to `AgentProxy.run_listening` (agent skill tools); do not call `SkillRuntime.iter_listening_chain` from the API.
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow TDD coding loop (Red → Green → Refactor) inside Inspect → Plan → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-api-gateway-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-api-gateway.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- Package: `src/aulos_api/`

## Approval boundaries

- Live upstream agent/MCP side effects: ask the operator first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
