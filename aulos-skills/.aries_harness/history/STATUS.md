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
generated_at: "2026-07-25T16:29:44+00:00"
effective_status: "generated"
effective_since: "2026-07-25T16:29:44+00:00"
content_fingerprint: "sha256:38eef9e9e5f1646219bc08bedabbc2cac50c4a7cc46abdf5b068fa9dc84fdbb1"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Current Status

Generated at: `2026-07-25T16:29:44+00:00`

## Current phase

- Listening product gates active (CKPT-005 ambient + identity hygiene)

## Branch and workspace

- no branch or workspace details recorded
- git branch: main
- HEAD: `93c0f6e` Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- working tree: dirty
- change: `M` `.gitignore`
- change: `M` `AGENTS.md`
- change: `M` `CLAUDE.md`
- change: `M` `aulos-agent/.aries_harness/INDEX.md`
- change: `M` `aulos-agent/.aries_harness/MEMORY.md`
- change: `M` `aulos-agent/.aries_harness/README.md`
- change: `M` `aulos-agent/.aries_harness/decisions/architecture/ARCH-001-langchain-agent-architecture.md`
- change: `M` `aulos-agent/.aries_harness/history/DAILY_SUMMARY_INDEX.md`

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

- no next action recorded
