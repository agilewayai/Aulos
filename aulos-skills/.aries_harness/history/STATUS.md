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
generated_at: "2026-07-27T11:49:07+00:00"
effective_status: "generated"
effective_since: "2026-07-27T11:49:07+00:00"
content_fingerprint: "sha256:f889455ff6ef292dd806f276bbe92bea9a463ede798b8392bc817b9c12302991"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Current Status

Generated at: `2026-07-27T11:49:07+00:00`

## Current phase

- AUDIT-009 F2/F10/F11 closed: guide HTML security contract + sanitizer, module splits, plaintext-secrets ADR.

## Branch and workspace

- no branch or workspace details recorded
- git branch: main
- HEAD: `5633e94` Ship Ops task queue, dev blog v2, and refresh fleet honeycomb.
- working tree: dirty
- change: `M` `AGENTS.md`
- change: `M` `CLAUDE.md`
- change: `M` `aulos-api/.aries_harness/JOURNAL.md`
- change: `M` `aulos-api/.aries_harness/references/REG-001-artifact-register.md`
- change: `M` `aulos-api/src/aulos_api/services/dev_blog.py`
- change: `M` `aulos-api/tests/test_dev_blog.py`
- change: `M` `aulos-knowledge/.aries_harness/EVAL.md`
- change: `M` `aulos-knowledge/.aries_harness/JOURNAL.md`

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
