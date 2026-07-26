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
generated_at: "2026-07-26T16:28:21+00:00"
effective_status: "generated"
effective_since: "2026-07-26T16:28:21+00:00"
content_fingerprint: "sha256:61b68841bea311ad3bad68c206edb1c9809a0cf9518a1a64b3ee82769acd5240"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-07-26T16:28:21+00:00`

## Recent changes

- SPEC-002 / STORY-PACK-002: Ops **Dev Blog** tab — list/read/generate monorepo daily product blog
- Evidence from git + harness; LLM via Ops providers (fake offline draft); three Chinese sections
- Verify: `aulos-api` `pytest tests/test_dev_blog.py` 5 passed; `npm run build` green
- SPEC-010: OPS Knowledge audit UI opened — Browse/proofread, Sources, Jobs & crawl, Retrieve lab
- Knowledge APIs: document detail+body, publish restore, composers list, document filters
- systemd `aulos-knowledge.service` on PG; API `AULOS_KNOWLEDGE_BASE_URL`; ops rebuilt to :5092 / aulos-ops.purezen.ai

## What is working

- SPEC-002 / STORY-PACK-002: Ops **Dev Blog** tab — list/read/generate monorepo daily product blog
- Evidence from git + harness; LLM via Ops providers (fake offline draft); three Chinese sections
- Verify: `aulos-api` `pytest tests/test_dev_blog.py` 5 passed; `npm run build` green
- SPEC-010: OPS Knowledge audit UI opened — Browse/proofread, Sources, Jobs & crawl, Retrieve lab

## What needs attention

- working tree is dirty with 78 tracked or untracked change(s)
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
