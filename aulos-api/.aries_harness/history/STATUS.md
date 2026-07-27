---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "history-status"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:07:43Z"
generated_at: "2026-07-27T09:44:33+00:00"
effective_status: "generated"
effective_since: "2026-07-27T09:44:33+00:00"
content_fingerprint: "sha256:ab9285f48eb33a3db8596d041f54964f643c2024ccad97a21e0f62f3bc025e3d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Current Status

Generated at: `2026-07-27T09:44:33+00:00`

## Current phase

- SPEC-013 durable jobs + library shipped (pytest green)

## Branch and workspace

- no branch or workspace details recorded
- git branch: main
- HEAD: `0c8a847` Ship Ops daily Dev Blog and web forgot-password reset.
- working tree: dirty
- change: `M` `AGENTS.md`
- change: `M` `CLAUDE.md`
- change: `M` `README.md`
- change: `M` `aulos-api/.aries_harness/ARIES_HARNESS_FINGERPRINT.json`
- change: `M` `aulos-api/.aries_harness/EVAL.md`
- change: `M` `aulos-api/.aries_harness/INDEX.md`
- change: `M` `aulos-api/.aries_harness/JOURNAL.md`
- change: `M` `aulos-api/.aries_harness/STATE.md`

## Current milestone

- no current milestone recorded

## Active tasks


## Blockers

- none recorded

## Last verification

- verification command: lint:
- verification command: typecheck:
- verification command: test: `pytest tests/test_dev_blog.py` (SPEC-009); `pytest tests/test_auth.py` (SPEC-002 incl. forgot/reset); `pytest tests/test_email_templates.py tests/test_mailgun.py` (SPEC-010); `pytest tests/test_mail_queue.py` (SPEC-011); `pytest tests/test_discogs.py` (SPEC-008 + search autocomplete); `pytest tests/test_chain_trace.py` (SPEC-012)

## Next action

- no next action recorded
