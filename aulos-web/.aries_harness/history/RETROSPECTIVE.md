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
generated_at: "2026-08-01T20:59:19+00:00"
effective_status: "generated"
effective_since: "2026-08-01T20:59:19+00:00"
content_fingerprint: "sha256:3d5d899ca6dba1fa93f0580f60c536422d3d36ece52119f027cb56d8dfc664e7"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-01T20:59:19+00:00`

## Recent changes

- Dual-draft UI: score + hard-flaw delta; repair_log on v2; scorecard chip 硬伤 N.
- Verify: npm run build.
- Review panel: expert perspective header; 硬伤修复指令 / 硬伤发现 (drop Sources list).
- Verify: npm run build.
- **Travel / immersive guide reading:** GuideReader with in-app fullscreen overlay
- Verify: npm run build green.

## What is working

- Dual-draft UI: score + hard-flaw delta; repair_log on v2; scorecard chip 硬伤 N.
- Verify: npm run build.
- Review panel: expert perspective header; 硬伤修复指令 / 硬伤发现 (drop Sources list).
- Verify: npm run build.

## What needs attention

- working tree is dirty with 330 tracked or untracked change(s)
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
