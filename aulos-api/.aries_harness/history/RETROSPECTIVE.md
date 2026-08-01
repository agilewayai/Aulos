---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "history-retrospective"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:07:43Z"
generated_at: "2026-08-01T20:59:12+00:00"
effective_status: "generated"
effective_since: "2026-08-01T20:59:12+00:00"
content_fingerprint: "sha256:135110d3cbbdd73d1b4431a2bf13182721ff4e548960746a5b1bd7388f49ecd5"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-01T20:59:12+00:00`

## Recent changes

- **SPEC-031:** `POST …/promote-production` graduates any staged promote_candidate
- **SPEC-030:** `GET …/promote-candidates`, `POST …/{id}/promote-stage`; trace +
- **SPEC-029 companion:** `_research_payload` persists `promote_candidate` +

## What is working

- **SPEC-031:** `POST …/promote-production` graduates any staged promote_candidate
- **SPEC-030:** `GET …/promote-candidates`, `POST …/{id}/promote-stage`; trace +
- **SPEC-029 companion:** `_research_payload` persists `promote_candidate` +

## What needs attention

- working tree is dirty with 330 tracked or untracked change(s)
- no explicit next-up slice is recorded

## Durable reminders

- Source of truth: `git@github.com:agilewayai/aries-harness-skills.git` (not `AriesHarnessStudio` / `aries-studio`).
- Local reference clone: `/home/ubuntu/studio/aries-harness-skills` (keep in sync with origin).
- 导赏 is Agent tool-chain (`run_listening_skill`), not API `iter_listening_chain`.
- See aulos-agent ARCH-002 / ADR-003 / SPEC-002.
- Store/API: UTC ISO with ``Z``. Display (web/ops): OS/browser timezone via ``src/time.ts`` ``formatDateTime`` / ``formatTime``.
- Harness scripts/templates: `.aries_harness/scripts/` + `.aries_harness/templates/` (not project-root `scripts/`/`templates/`).

## Promotion rule

- if a lesson is durable, move it into MEMORY, docs/insights, AGENTS, or a reusable harness asset
- do not let retrospective output become the only place where important operating knowledge lives
