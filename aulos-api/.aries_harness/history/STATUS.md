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
generated_at: "2026-08-02T10:06:49+00:00"
effective_status: "generated"
effective_since: "2026-08-02T10:06:49+00:00"
content_fingerprint: "sha256:4108478629d5ca240b9521483d5da5d490621042c16097efd31194eb8969527f"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Current Status

Generated at: `2026-08-02T10:06:49+00:00`

## Current phase

- SPEC-034 Slice H deployed in gateway: multi-work `g.program` now defaults

## Branch and workspace

- no branch or workspace details recorded
- git branch: main
- HEAD: `9606691` Ship Discogs structure-first guide sheets
- working tree: dirty
- change: `M` `aulos-agent/.aries_harness/INDEX.md`
- change: `M` `aulos-agent/.aries_harness/JOURNAL.md`
- change: `M` `aulos-agent/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
- change: `M` `aulos-agent/.aries_harness/history/DOC_TRACE.md`
- change: `M` `aulos-agent/.aries_harness/history/README.md`
- change: `M` `aulos-agent/.aries_harness/history/RETROSPECTIVE.md`
- change: `M` `aulos-agent/.aries_harness/history/ROADMAP.md`
- change: `M` `aulos-agent/.aries_harness/history/STATUS.md`

## Current milestone

- no current milestone recorded

## Active tasks


## Blockers

- none recorded

## Last verification

- verification command: lint:
- verification command: typecheck:
- verification command: test: `pytest tests/test_dev_blog.py` (SPEC-009); `pytest tests/test_auth.py` (SPEC-002 incl. forgot/reset); `pytest tests/test_email_templates.py tests/test_mailgun.py` (SPEC-010); `pytest tests/test_mail_queue.py` (SPEC-011); `pytest tests/test_discogs.py` (SPEC-008 + search autocomplete + SPEC-034 structure); `pytest tests/test_chain_trace.py` (SPEC-012); `pytest tests/test_diary_guides.py` (SPEC-021 / REQ-011 lifecycle); `PYTHONPATH=. .venv/bin/pytest -q tests/test_listening_jobs.py tests/test_diary_guides.py` (failed eval/publish gate); `.venv/bin/pytest -q tests/test_web_research_partial.py` (SPEC-034 Slice H program deepen budget / fast raw-web path)

## Next action

- no next action recorded
