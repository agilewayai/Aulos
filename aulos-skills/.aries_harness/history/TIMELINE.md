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
generated_at: "2026-07-27T11:49:07+00:00"
effective_status: "generated"
effective_since: "2026-07-27T11:49:07+00:00"
content_fingerprint: "sha256:fa193aa44b50f016d7edfe200b71aea6e7b39caf6eb40545d949173a4d2cfb2a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-27T11:49:07+00:00`

## Journal milestones

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

### 2026-07-27T08:52:00Z

- AUDIT-009 remediation slice (security + verification):
- F1: removed tracked JWT/bootstrap defaults from `deploy/systemd/user/aulos-api.service`; `deploy/start-host.sh` now requires non-default secrets in `.run/host.env` including `AULOS_KNOWLEDGE_ADMIN_TOKEN`.
- F4/F8/F9: API full suite green (`89 passed`); worker shutdown/join + `tests/conftest.py` isolation; web-research freshness uses provenance only (not `doc.updated_at`).
- F5: `aulos-knowledge` `/v1/admin/*` requires bearer token; API proxy forwards `AULOS_KNOWLEDGE_ADMIN_TOKEN`.
- F2/F7: guide iframe drops `allow-same-origin`; public guide CSP + security headers; deploy static host headers.
- F6/F12: `aulos-knowledge` in root inventory + `AGENTS.md`/`MISSION`/`EVAL`; ops lint warning-free.
- Residual: F3 HttpOnly session auth; operator must rotate live secrets.

### 2026-07-27T08:36:49Z

- Completed workspace-wide architecture/code review as `AUDIT-009`.
- Verdict: not ready for production signoff; F1 fixed deploy JWT/bootstrap defaults, F2/F3 guide HTML + browser token exposure, F4 red API suite, and F5 knowledge-plane direct admin auth are the priority blockers.
- Verification snapshot: API full suite red (`87 passed, 1 failed, 1 error`); skills/agent/MCP/knowledge/deploy tests and web/ops builds passed; ops lint still has one hook dependency warning.

## Recent git commits

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

- `M` `AGENTS.md`
- `M` `CLAUDE.md`
- `M` `aulos-api/.aries_harness/JOURNAL.md`
- `M` `aulos-api/.aries_harness/references/REG-001-artifact-register.md`
- `M` `aulos-api/src/aulos_api/services/dev_blog.py`
- `M` `aulos-api/tests/test_dev_blog.py`
- `M` `aulos-knowledge/.aries_harness/EVAL.md`
- `M` `aulos-knowledge/.aries_harness/JOURNAL.md`
- `M` `aulos-knowledge/.aries_harness/STATE.md`
- `M` `aulos-knowledge/.aries_harness/TASK_STACK.md`
- `M` `aulos-knowledge/.aries_harness/decisions/adrs/ADR-006-allowlisted-sources-provenance.md`
- `M` `aulos-knowledge/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
