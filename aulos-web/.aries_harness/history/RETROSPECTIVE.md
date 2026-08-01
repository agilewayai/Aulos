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
generated_at: "2026-08-01T06:31:30+00:00"
effective_status: "generated"
effective_since: "2026-08-01T06:31:30+00:00"
content_fingerprint: "sha256:75945b1f86007a8d85adac75a986b3d3fb4e6c1aa477f13456f41d2186901c54"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-01T06:31:30+00:00`

## Recent changes

- Atelier: countable chain progress (N/M) + stage list; SSE reconnect; Retry chain for failed/interrupted jobs (pairs with API SPEC-013 delta).
- Verify: `npm run build`.
- SPEC-007: move Guide | Atelier | Library tabs from mobile bottom bar to sticky top (under topbar) for easier reach.
- Verify: `npm run build`.
- SPEC-008: before asset auto-reload, capture UI scene (tab, draft, guide id, library filters, scroll); restore once after reload with notice.
- Same pattern on aulos-ops (tab + user filters + scroll). Passwords never persisted.

## What is working

- Atelier: countable chain progress (N/M) + stage list; SSE reconnect; Retry chain for failed/interrupted jobs (pairs with API SPEC-013 delta).
- Verify: `npm run build`.
- SPEC-007: move Guide | Atelier | Library tabs from mobile bottom bar to sticky top (under topbar) for easier reach.
- Verify: `npm run build`.

## What needs attention

- working tree is dirty with 124 tracked or untracked change(s)
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
