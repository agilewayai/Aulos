# aulos workspace — agent guide

Hackathon monorepo for the Aulos initiative. Sub-projects each have their own `AGENTS.md` / `.aries_harness/`.

## Aries Harness (mandatory default)

**Aries Harness is the forced default process for all Aulos work.** Preferential language is not enough: agents must follow harness norms unless the operator explicitly waives them in the current turn.

1. Work in the relevant sub-project root; keep that project’s `.aries_harness/` current.
2. Before behavior changes: read `MISSION` / `STATE`; write or update REQ/SPEC; update `TASK_STACK`.
3. Coding loop: **TDD** Red → Green → Refactor inside Inspect → Plan → Verify → Summarize.
4. After the slice: `JOURNAL` + `history-refresh`; update `EVAL` / VR when gates change; promote insights when lessons must change future runs.
5. **Chat-only fixes without harness artifacts are incomplete** (see `aulos-skills` AUDIT-001).

Also:

- **UI/UX** — apply the **`ui-ux-pro-max`** skill before visual/UX design changes.
- **Listening-product changes** — promote into `aulos-skills` REQ/SPEC/SKILL/eval/tests + journal.
- **Timestamps** — store UTC on the wire; display OS/browser local time in product UIs (`src/time.ts`).
- **Chinese UI** — 简体 (`zh-Hans`) / 繁体 (`zh-Hant`) only; no regional locale codes in OSS source.
- **Listening identity** — Catalog + IdentityResolver; no composer/work hardcoding in Python.
- **DB closeout** — Postgres is hot; after model changes, ship `schema_patches` + verify PG columns (SQLite pilot ≠ production).

Canonical policy: [`aulos-skills/skills/aulos-operating-defaults/SKILL.md`](aulos-skills/skills/aulos-operating-defaults/SKILL.md)

## Sub-projects

| Path | Role |
| --- | --- |
| `aulos-agent/` | LangGraph agent runtime |
| `aulos-api/` | HTTP API gateway |
| `aulos-web/` | Operator web GUI |
| `aulos-mcp/` | MCP integrations |
| `aulos-skills/` | Main harness skills pack |
| `aulos-knowledge/` | Professional music knowledge plane |
| `aulos-ops/` | Admin / ops portal |

Work inside the relevant sub-project root unless the task is explicitly workspace-wide.

## Live URLs

- https://aulos.purezen.ai
- https://aulos-ops.purezen.ai

## DevOps (host production)

**Canonical entry:** `bash deploy/aulos-ctl.sh` — full control plane for build, deploy, smoke, status, logs, secrets.

| Task | Command |
| --- | --- |
| Production deploy | `bash deploy/aulos-ctl.sh deploy` |
| Preflight | `bash deploy/aulos-ctl.sh doctor` |
| Post-deploy smoke | `bash deploy/aulos-ctl.sh smoke` |
| First-time secrets | `bash deploy/aulos-ctl.sh secrets init` → edit `.run/host.env` |

Runbook: [`deploy/OPS.md`](deploy/OPS.md). Quick reference: [`deploy/README.md`](deploy/README.md).

`deploy/start-host.sh` is a thin alias for `aulos-ctl deploy`. Agents need **explicit operator approval** before production deploy unless requested in the current turn.
