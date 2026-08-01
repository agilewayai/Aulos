---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "history-retrospective"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:06Z"
generated_at: "2026-08-01T20:59:26+00:00"
effective_status: "generated"
effective_since: "2026-08-01T20:59:26+00:00"
content_fingerprint: "sha256:053869a4845e5632f8ec44dcd08051c426a5b5a9da6bb5c1e29ae650b1e8b3fe"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-01T20:59:26+00:00`

## Recent changes

- **SPEC-031:** Guide quality — Promote to production after staging; copy states
- **SPEC-030:** Guide quality panel shows promote candidate + Stage craft (staging
- **Ambient fallback UI:** LLM/Listening settings radio for official Embed vs server

## What is working

- **SPEC-031:** Guide quality — Promote to production after staging; copy states
- **SPEC-030:** Guide quality panel shows promote candidate + Stage craft (staging
- **Ambient fallback UI:** LLM/Listening settings radio for official Embed vs server

## What needs attention

- working tree is dirty with 330 tracked or untracked change(s)
- no explicit next-up slice is recorded

## Durable reminders

- Source of truth: `git@github.com:agilewayai/aries-harness-skills.git` (not `AriesHarnessStudio` / `aries-studio`).
- Local reference clone: `/home/ubuntu/studio/aries-harness-skills` (keep in sync with origin).
- Store/API: UTC ISO with ``Z``. Display (web/ops): OS/browser timezone via ``src/time.ts`` ``formatDateTime`` / ``formatTime``.
- Harness scripts/templates: `.aries_harness/scripts/` + `.aries_harness/templates/` (not project-root `scripts/`/`templates/`).
- Invoke: `bash .aries_harness/scripts/aries-harness.sh <cmd> --project-root .`
- Aries Harness is the **forced default** process for this project (not optional preference).

## Promotion rule

- if a lesson is durable, move it into MEMORY, docs/insights, AGENTS, or a reusable harness asset
- do not let retrospective output become the only place where important operating knowledge lives
