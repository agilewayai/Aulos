---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "history-daily-summary-index"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:05Z"
generated_at: "2026-07-27T09:46:13+00:00"
effective_status: "generated"
effective_since: "2026-07-27T09:46:13+00:00"
content_fingerprint: "sha256:b69741f6ea8623c8b1db21ef804340fcf10db2370ea8f4a29a220042d5c5a60c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Daily Summary Index

Generated at: `2026-07-27T09:46:13+00:00`

This index tracks the generated daily development summaries under `history/daily/`.

## Daily reports

- `2026-07-27` -> `daily/2026-07-27.md`
- `2026-07-26` -> `daily/2026-07-26.md`
- `2026-07-25` -> `daily/2026-07-25.md`

## Design rule

- daily summaries are generated projections of journal and git evidence, not manually maintained source truth
- if the daily memo is weak, improve `JOURNAL.md`, `STATE.md`, `TASK_STACK.md`, or commit hygiene rather than editing generated files by hand
