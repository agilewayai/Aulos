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
generated_at: "2026-08-02T07:27:11+00:00"
effective_status: "generated"
effective_since: "2026-08-02T07:27:11+00:00"
content_fingerprint: "sha256:da85668871d586ff6962949b8ca41f41626ecbc401743a852895191acfa04748"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-02T07:27:11+00:00`

## Recent changes

- **Production deploy sync:** root `bash deploy/aulos-ctl.sh deploy` published
- Verify: root `doctor` passed; deploy test suite -> 5 passed; root `status`
- Central deploy evidence:
- 我的聆乐日记: drop 78rem/44rem/72ch shell squeeze; browse feed full-width album
- Verify: `npm run build`.
- Plaza feed: drop featured hero lead (first card no longer full-bleed / oversized);

## What is working

- **Production deploy sync:** root `bash deploy/aulos-ctl.sh deploy` published
- Verify: root `doctor` passed; deploy test suite -> 5 passed; root `status`
- Central deploy evidence:
- 我的聆乐日记: drop 78rem/44rem/72ch shell squeeze; browse feed full-width album

## What needs attention

- working tree is dirty with 196 tracked or untracked change(s)
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
