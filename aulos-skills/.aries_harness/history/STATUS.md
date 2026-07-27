---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "history-status"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:05Z"
generated_at: "2026-07-27T09:46:13+00:00"
effective_status: "generated"
effective_since: "2026-07-27T09:46:13+00:00"
content_fingerprint: "sha256:14dd78126d8c6a5bd66799a3ab9d17ea800a6a7d5af19adf99a5ee6f2d90e5cc"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Current Status

Generated at: `2026-07-27T09:46:13+00:00`

## Current phase

- AUDIT-009 F2/F10/F11 closed: guide HTML security contract + sanitizer, module splits, plaintext-secrets ADR.

## Branch and workspace

- no branch or workspace details recorded
- git branch: main
- HEAD: `0c8a847` Ship Ops daily Dev Blog and web forgot-password reset.
- working tree: dirty
- change: `M` `AGENTS.md`
- change: `M` `CLAUDE.md`
- change: `M` `README.md`
- change: `M` `aulos-agent/.aries_harness/INDEX.md`
- change: `M` `aulos-agent/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
- change: `M` `aulos-agent/.aries_harness/history/DOC_TRACE.md`
- change: `M` `aulos-agent/.aries_harness/history/README.md`
- change: `M` `aulos-agent/.aries_harness/history/RETROSPECTIVE.md`

## Current milestone

- no current milestone recorded

## Active tasks


## Blockers

- none recorded

## Last verification

- verification command: unit (skills): `cd aulos-api && .venv/bin/python -m pytest ../aulos-skills/tests/test_runtime.py ../aulos-skills/tests/test_ambient_agent.py ../aulos-skills/tests/test_ambient_playlist.py -q`
- verification command: unit (media API): `cd aulos-api && .venv/bin/python -m pytest tests/test_media.py -q`
- verification command: media smoke: `curl -sI 'http://127.0.0.1:5090/v1/media/audio?src=<urlencoded-commons-url>&mode=cache' | grep -i content-disposition` → must contain `inline`
- verification command: live parity: recompose Goldberg + one cold-path Chinese work; assert bilingual + ambient in `guide_html`

## Next action

- Optional operator: rotate live secrets in `.run/host.env` when ready to redeploy (F1 deferred).
- Later: deeper F10 splits (`listening_guide.py` / `runtime.py`) when product work touches those files.
