# CLAUDE.md

Mirror of workspace `AGENTS.md` for Claude-compatible agents.

## Aries Harness (mandatory default)

**Aries Harness is the forced default process for all Aulos work.** Do not treat it as optional. Skip harness steps only if the operator explicitly waives them.

1. Work in the relevant sub-project; keep `.aries_harness/` current.
2. Behavior changes: REQ/SPEC first; update `STATE` / `TASK_STACK`.
3. Coding: **TDD** Red → Green → Refactor; Inspect → Plan → Verify → Summarize.
4. Closeout: `JOURNAL` + `history-refresh`; promote gates/insights — chat-only is incomplete.

Also: UI/UX → `ui-ux-pro-max`; listening-product → promote into `aulos-skills` harness assets; timestamps → store UTC / display OS local.

**Meta principles (纲领):** `aulos-skills/.aries_harness/references/META-001-meta-principles.md` (v2) — root-cause, asset sync, craft, architecture boundaries.

**DevOps:** `bash deploy/aulos-ctl.sh` — runbook `deploy/OPS.md`. **Honeycomb:** `bash deploy/honeycomb.sh`. Ask before production deploy.

Canonical policy: `aulos-skills/skills/aulos-operating-defaults/SKILL.md`
