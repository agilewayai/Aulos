# Aulos Core Harness

Use this skill as the main operating loop for Aulos harness work.

Also load **`aulos-operating-defaults`** for fleet policy: aries-harness for design/spec/history/devops, TDD coding loop, and `ui-ux-pro-max` for UI/UX.

## When to use

- Starting or resuming work in any `aulos-*` sub-project
- Keeping `.aries_harness/` mission, state, and task stack current
- Coordinating cross-service changes (web / api / mcp / agent / ops / skills)

## Default work under aries-harness

| Work type | Do this |
| --- | --- |
| Product design | REQ / STORY under `.aries_harness/references/` |
| System architecture | ARCH / ADR under `.aries_harness/decisions/` |
| Spec development | SPEC before broad implementation |
| Dev-history refresh | `aries-harness.sh history-refresh` / `history-status` |
| Doc organization | `aries-harness.sh well-organized`; keep INDEX/MISSION/STATE tidy |
| DevOps | deploy runbooks + smoke/rollback under `runs/deployments/` |

## Base loop (TDD)

1. Inspect — read MISSION, STATE, TASK_STACK, and related ARCH/SPEC
2. Plan — choose the smallest slice with an explicit done condition
3. **Red** — write/extend failing tests first
4. **Green** — implement the minimum to pass
5. **Refactor** — clean with tests still green
6. Verify — project tests/build + harness history-status as needed
7. Summarize — update STATE, JOURNAL, and verification notes

## UI / UX

- For UI structure, visual design, or UX changes: apply the **`ui-ux-pro-max`** skill
- Keep design decisions traceable in harness REQ/SPEC/ARCH when they change product intent

## Guardrails

- Prefer sibling contracts through `aulos-api` and documented MCP tools
- Never commit secrets or `.env`
- Ask before live external side effects or production deploy actions
