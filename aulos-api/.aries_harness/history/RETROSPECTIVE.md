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
generated_at: "2026-08-02T07:27:02+00:00"
effective_status: "generated"
effective_since: "2026-08-02T07:27:02+00:00"
content_fingerprint: "sha256:5dfbff4957de4aabb850fab37323f3c6f3631273822d1e7e2a74fe4d66f7493f"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-02T07:27:02+00:00`

## Recent changes

- **Production deploy sync:** root `bash deploy/aulos-ctl.sh deploy` published
- Verify: root `doctor` passed; deploy test suite -> 5 passed; root `status`
- Central deploy evidence:
- **SPEC-034 Slice F consumer / guide #59:** hot Postgres latest guide remained
- Fix: Discogs core parsing now prefers explicit performer-role names over
- Verify: `PYTHONPATH=. .venv/bin/pytest -q tests/test_discogs.py` -> 12 passed;

## What is working

- **Production deploy sync:** root `bash deploy/aulos-ctl.sh deploy` published
- Verify: root `doctor` passed; deploy test suite -> 5 passed; root `status`
- Central deploy evidence:
- **SPEC-034 Slice F consumer / guide #59:** hot Postgres latest guide remained

## What needs attention

- working tree is dirty with 196 tracked or untracked change(s)
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
