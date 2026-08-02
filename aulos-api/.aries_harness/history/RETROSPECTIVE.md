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
generated_at: "2026-08-02T10:06:49+00:00"
effective_status: "generated"
effective_since: "2026-08-02T10:06:49+00:00"
content_fingerprint: "sha256:52f41b29d75707d864eb0dd0796461d6418bea4b32b39a348d3dd5b8d3922610"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-02T10:06:49+00:00`

## Recent changes

- Deployed gateway Slice H production code with `bash deploy/aulos-ctl.sh
- Post-deploy `smoke` and `status` stayed green: `aulos-api`, `aulos-web`,
- Production PostgreSQL guide #60 trace confirms gateway `g.program` budget work
- **Review Critics → AI Code Mirror (Codex):** agent `_ops_llm_complete(role=review)`
- **LLM provider: AI Code Mirror (Codex Responses relay):** Ops slot

## What is working

- Deployed gateway Slice H production code with `bash deploy/aulos-ctl.sh
- Post-deploy `smoke` and `status` stayed green: `aulos-api`, `aulos-web`,
- Production PostgreSQL guide #60 trace confirms gateway `g.program` budget work
- **Review Critics → AI Code Mirror (Codex):** agent `_ops_llm_complete(role=review)`

## What needs attention

- working tree is dirty with 144 tracked or untracked change(s)
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
