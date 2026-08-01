---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "history-timeline"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:05Z"
generated_at: "2026-08-01T06:31:13+00:00"
effective_status: "generated"
effective_since: "2026-08-01T06:31:13+00:00"
content_fingerprint: "sha256:5d11ac2e32b22a7a883224abbd2ac875529c95decc48beb355c068c816c9dc5c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-08-01T06:31:13+00:00`

## Journal milestones

### 2026-08-01T06:35:00Z

- Honeycomb closeout after META-001 §3.4 Meta Play Simple promotion + knowledge/ops console ship.

### 2026-07-27T16:40:00Z

- **META-001 v4 §3.4 Product interaction — Meta Play Simple:** human nouns first, progressive disclosure,

### 2026-07-27T11:20:00Z

- Promoted **Authority Source Registry** into META-001 §4 + insights (aulos-knowledge REQ-008 / ADR-006 / REG-SRC-001).

### 2026-07-27T10:50:00Z

- **META-001 v2** — promoted insights →纲领: data-over-heuristics, multi-stage validate, harness forced + facility, deploy-in-delivery, LLM coerce, hard-fail gates, architecture boundaries (agent / knowledge / identity→RAG).
- `docs/insights.md` entries tagged `↑ META-001 §…` or `→ operating-defaults/SPEC` (domain stays out of META).

### 2026-07-27T10:45:00Z

- **META-001** Meta Principles (纲领层): root-cause thinking, asset synchronization, engineering craft / anti-smells.
- Registered in REG-001; MetaDefineLayer manifest; promoted to workspace `AGENTS.md`, `CLAUDE.md`, `aulos-operating-defaults`.

### 2026-07-27T09:45:00Z

- Fleet DevOps control plane:
- `deploy/aulos-ctl.sh` — unified commands: `deploy`, `build`, `restart`, `status`, `smoke`, `logs`, `doctor`, `secrets {init|check}`, `units install`, `ingress apply`, `test`.
- Shared libs under `deploy/lib/`; `start-host.sh` → thin `aulos-ctl deploy` wrapper.
- Canonical runbook `deploy/OPS.md` (architecture, secrets, gates, rollback).
- Promoted into `AGENTS.md`, `README.md`, `CLAUDE.md`, `aulos-operating-defaults/SKILL.md`, `deploy/README.md`.
- Verify: `aulos-ctl doctor`, `test` (5 passed), `smoke` all green.

### 2026-07-27T09:30:00Z

- AUDIT-009 continuation — F2 / F10 / F11 (F1 deferred per operator):
- F11: `ADR-008-plaintext-systemsetting-secrets-sprint1.md` accepts Sprint-1 plaintext secrets with compensating controls.
- F2: `SPEC-015` guide HTML security; `guide_html_security.sanitize_guide_html` + public CSP tests; web `guideHtml.ts` sandbox selftest (no `allow-same-origin`).
- F10: `SPEC-016` seams — extracted `guide_html_security.py`, `ops_mail.py`, `ops_integrations.py`, `SkillsPanel.tsx`, `guideHtml.ts`. Line cuts: `listening.py` 801→522, `ops.py` 971→621, ops `App.tsx` 1677→1491.
- Verify: API `94 passed`; web/ops builds + ops lint green; `guideHtml.selftest` ok.

### 2026-07-27T09:10:00Z

- AUDIT-009 continuation slice — F3 + F2 follow-up:
- SPEC-014: login sets HttpOnly `aulos_session`; logout clears it; `get_current_user` accepts cookie or bearer.
- `aulos-web` / `aulos-ops`: `credentials: 'include'`, removed `localStorage` JWT storage.
- Added `tests/test_guide_security.py` for public guide CSP/security headers.
- Test helper `clear_session()` for cookie-aware unauth assertions.
- Residual: operator secret rotation (F1); F10 module splits; optional Playwright F2 stretch.

## Recent git commits

- `491b042` 2026-07-27 Ship authority source registry, OPS knowledge console, and refresh fleet honeycomb.
- `5633e94` 2026-07-27 Ship Ops task queue, dev blog v2, and refresh fleet honeycomb.
- `c3009d2` 2026-07-27 Harden platform security, ship fleet DevOps control, and refresh harness honeycomb.
- `0c8a847` 2026-07-27 Ship Ops daily Dev Blog and web forgot-password reset.
- `6ab1ea3` 2026-07-26 Ship /discogs release and catalog-number listening guides with OPS token UI.
- `53e7437` 2026-07-26 Ship identity catalog, Hans/Hant locales, web research, and knowledge plane.
- `555cf53` 2026-07-26 Ship listening product, mandatory harness, facility layout, and UTC/local time.
- `93c0f6e` 2026-07-25 Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- `7632d9b` 2026-07-25 Add aulos-web, aulos-api, and aulos-mcp sub-projects under aries-harness.
- `0d5cb01` 2026-07-25 Initial commit: Aulos hackathon workspace with LangChain agent runtime.

## Working tree snapshot

- `M` `aulos-api/.aries_harness/JOURNAL.md`
- `M` `aulos-api/.aries_harness/STATE.md`
- `M` `aulos-api/.aries_harness/TASK_STACK.md`
- `M` `aulos-api/.aries_harness/references/specs/SPEC-018-ops-task-queue.md`
- `M` `aulos-api/src/aulos_api/routes/ops.py`
- `M` `aulos-api/src/aulos_api/services/knowledge_proxy.py`
- `M` `aulos-api/src/aulos_api/services/task_queue.py`
- `M` `aulos-knowledge/.aries_harness/INDEX.md`
- `M` `aulos-knowledge/.aries_harness/JOURNAL.md`
- `M` `aulos-knowledge/.aries_harness/STATE.md`
- `M` `aulos-knowledge/.aries_harness/TASK_STACK.md`
- `M` `aulos-knowledge/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
