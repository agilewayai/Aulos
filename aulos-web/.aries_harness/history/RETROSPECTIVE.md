---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "history-retrospective"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:07:42Z"
generated_at: "2026-07-26T16:28:38+00:00"
effective_status: "generated"
effective_since: "2026-07-26T16:28:38+00:00"
content_fingerprint: "sha256:2b83858956609e8080da5c0c499891dd52250f01f0267bcf1f6cba486ca94e44"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-07-26T16:28:38+00:00`

## Recent changes

- SPEC-002: Forgot password + reset UI (`forgot` / `reset` modes, `/?reset_token=`)
- API clients: `forgotPassword` / `resetPassword`
- Verify: `npm run build` green; upstream `pytest tests/test_auth.py` 7 passed
- Added ``src/time.ts``; guide history/meta show OS-local timestamps
- initialized `.aries_harness/`
- wrote `ARIES_HARNESS_FINGERPRINT.json`

## What is working

- SPEC-002: Forgot password + reset UI (`forgot` / `reset` modes, `/?reset_token=`)
- API clients: `forgotPassword` / `resetPassword`
- Verify: `npm run build` green; upstream `pytest tests/test_auth.py` 7 passed
- Added ``src/time.ts``; guide history/meta show OS-local timestamps

## What needs attention

- working tree is dirty with 77 tracked or untracked change(s)
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
