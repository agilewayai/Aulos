---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "history-readme"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T10:55:22Z"
generated_at: "2026-08-01T06:31:48+00:00"
effective_status: "generated"
effective_since: "2026-08-01T06:31:48+00:00"
content_fingerprint: "sha256:5970e0d6c60469937492069fcedbaeb91b2d45ef17d525bfe16f1620f407f850"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Harness History Surface

Last refreshed: `2026-08-01T06:31:48+00:00`

This directory holds generated development-history views derived from harness facts and repo evidence.

## Commands

- `/aries-harness history-refresh` regenerates this history surface.
- `/aries-harness history-status` prints a concise snapshot without rewriting files.
- `/ah history-refresh` and `/ah history-status` are the short aliases.

## Generated files

- `STATUS.md` for current phase, milestone, verification, and next action.
- `ROADMAP.md` for outcome, current milestone, now/next/later slices, and guardrails.
- `TIMELINE.md` for journal milestones plus recent git commits.
- `RETROSPECTIVE.md` for recent wins, attention areas, and durable reminders.
- `DAILY_SUMMARY_INDEX.md` plus `daily/*.md` for per-day development memo and feature-evolution summaries.
- `DOC_TRACE.md` for document governance, effective status, and recent revision trace.
- `doc-trace.json` for machine-readable document trace details.
- `summary.json` for machine-readable automation and inspection.

## Evidence model

- `.aries_harness/MISSION.md`
- `.aries_harness/TASK_STACK.md`
- `.aries_harness/STATE.md`
- `.aries_harness/JOURNAL.md`
- `.aries_harness/EVAL.md`
- `.aries_harness/MEMORY.md`
- `git status --porcelain=v1`
- `git log`
- `.aries_harness/**/*.md frontmatter + git file history`

## Design rules

- derive history from actual project evidence, not chat-only narrative
- keep status, roadmap, timeline, and retrospective as separate views
- promote durable lessons into `MEMORY.md`, `docs/insights.md`, or `AGENTS.md` instead of hiding them only in history output
