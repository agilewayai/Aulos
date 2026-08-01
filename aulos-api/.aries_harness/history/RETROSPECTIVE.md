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
generated_at: "2026-08-01T06:31:23+00:00"
effective_status: "generated"
effective_since: "2026-08-01T06:31:23+00:00"
content_fingerprint: "sha256:0f54b23f1cf62ceac72f9418e0bbda818da2aa033a34aae6786f9a34a7329e79"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-01T06:31:23+00:00`

## Recent changes

- **SPEC-018 delta:** ops task type `knowledge.benchmark` (+ improve path) via knowledge plane proxy;
- Honeycomb closeout with knowledge/ops knowledge-console ship.
- Cross-ref **AUDIT-009** remediation (primary journal: `aulos-skills/.aries_harness/JOURNAL.md`, review `runs/reviews/AUDIT-009-…`):
- F3 SPEC-014 HttpOnly session cookie; F2 SPEC-015 guide HTML security + sanitizer; F10 SPEC-016 module splits; F11 ADR-008 plaintext secrets accepted for Sprint-1.
- Fleet DevOps: `deploy/aulos-ctl.sh`, `deploy/OPS.md`, `deploy/honeycomb.sh` (commit `c3009d2`).
- SPEC-018: Ops background task queue — `ops_tasks` table, Redis `aulos:ops:tasks:queue`, worker in lifespan.

## What is working

- **SPEC-018 delta:** ops task type `knowledge.benchmark` (+ improve path) via knowledge plane proxy;
- Honeycomb closeout with knowledge/ops knowledge-console ship.
- Cross-ref **AUDIT-009** remediation (primary journal: `aulos-skills/.aries_harness/JOURNAL.md`, review `runs/reviews/AUDIT-009-…`):
- F3 SPEC-014 HttpOnly session cookie; F2 SPEC-015 guide HTML security + sanitizer; F10 SPEC-016 module splits; F11 ADR-008 plaintext secrets accepted for Sprint-1.

## What needs attention

- working tree is dirty with 110 tracked or untracked change(s)
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
