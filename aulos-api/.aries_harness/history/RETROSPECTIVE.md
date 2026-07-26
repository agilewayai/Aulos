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
generated_at: "2026-07-26T16:28:21+00:00"
effective_status: "generated"
effective_since: "2026-07-26T16:28:21+00:00"
content_fingerprint: "sha256:356d71dc1702a3de34b5b90a733ee111ae5a3ddd7ce06dc95e771a71701b83a1"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-07-26T16:28:21+00:00`

## Recent changes

- SPEC-002: `POST /v1/auth/forgot-password` + `POST /v1/auth/reset-password`; Mailgun `reset_password` mail
- Anti-enumeration; one-time `EmailToken` purpose=`reset_password`
- Verify: `pytest tests/test_auth.py` 7 passed
- SPEC-009: `/v1/ops/dev-blog` list/get/generate; `dev_blog_posts` table; `services/dev_blog.py`
- Collect UTC-day git + harness excerpts; Ops LLM or fake template with product narrative headings
- Verify: `pytest tests/test_dev_blog.py` 5 passed offline

## What is working

- SPEC-002: `POST /v1/auth/forgot-password` + `POST /v1/auth/reset-password`; Mailgun `reset_password` mail
- Anti-enumeration; one-time `EmailToken` purpose=`reset_password`
- Verify: `pytest tests/test_auth.py` 7 passed
- SPEC-009: `/v1/ops/dev-blog` list/get/generate; `dev_blog_posts` table; `services/dev_blog.py`

## What needs attention

- working tree is dirty with 78 tracked or untracked change(s)
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
