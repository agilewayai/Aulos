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
generated_at: "2026-07-27T10:25:06+00:00"
effective_status: "generated"
effective_since: "2026-07-27T10:25:06+00:00"
content_fingerprint: "sha256:1f59bfc56433867ee61161c4f3afe041ec9be12fc214efb3eb48e454d1dc2940"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-07-27T10:25:06+00:00`

## Recent changes

- SPEC-018: Ops background task queue — `ops_tasks` table, Redis `aulos:ops:tasks:queue`, worker in lifespan.
- Dev blog generate/regenerate → **202** enqueue `dev_blog.generate`; sync mode for tests (`AULOS_TASK_QUEUE_SYNC`).
- API: `GET /v1/ops/tasks/dashboard`, `/tasks`, `/tasks/{id}`; dashboard aggregates mail + listening + ops.
- SPEC-017: Dev Blog **internal writing contract** — evidence-only, factual dev trace; no hype/emotion/external marketing.
- `dev_blog_contract.py`: SYSTEM_PROMPT rewrite + `validate_dev_blog_body()` soft lint; fake draft aligned.
- Promoted into SPEC-009, ops SPEC-002, REQ-002, `aulos-operating-defaults`, Ops UI lead copy.

## What is working

- SPEC-018: Ops background task queue — `ops_tasks` table, Redis `aulos:ops:tasks:queue`, worker in lifespan.
- Dev blog generate/regenerate → **202** enqueue `dev_blog.generate`; sync mode for tests (`AULOS_TASK_QUEUE_SYNC`).
- API: `GET /v1/ops/tasks/dashboard`, `/tasks`, `/tasks/{id}`; dashboard aggregates mail + listening + ops.
- SPEC-017: Dev Blog **internal writing contract** — evidence-only, factual dev trace; no hype/emotion/external marketing.

## What needs attention

- working tree is dirty with 51 tracked or untracked change(s)
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
