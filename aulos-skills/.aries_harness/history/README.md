---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "history-readme"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:05Z"
generated_at: "2026-07-27T10:24:56+00:00"
effective_status: "generated"
effective_since: "2026-07-27T10:24:56+00:00"
content_fingerprint: "sha256:678dd87be43d5e28231c6088b524deb115560fd20a6d2079237c6fc73584c084"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Harness History Surface

Last refreshed: `2026-07-27T10:24:56+00:00`

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
