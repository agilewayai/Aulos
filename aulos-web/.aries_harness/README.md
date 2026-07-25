---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "harness-readme"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:42Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:42Z"
content_fingerprint: "sha256:cc714ad48d65d790330071c0c8b9f57c9ce856a926cd51b05812b37d81e5b00d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# aulos-web Harness

This directory is the controlled recovery and execution surface for the project.

## Layer-first reading order

### MetaDefineLayer

1. `layers/MetaDefineLayer/README.md`
2. `MISSION.md`
3. `ADR.md`
4. `RUNBOOK.md`
5. `EVAL.md`
6. `RISKS.md`

### RunCookingLayer

1. `layers/RunCookingLayer/README.md`
2. `TASK_STACK.md`
3. `PIPELINE.md`
4. `STATE.md`
5. `JOURNAL.md`

### Shared support surface

1. `layers/SharedSupportSurface/README.md`
2. `MEMORY.md`
3. `INDEX.md`

## Canonical commands

- `/aries-harness init`
- `/aries-harness well-organized`
- `/aries-harness pipeline-inspect`
- `/aries-harness memory-inspect`
- `/aries-harness history-refresh`
- `/aries-harness history-status`

## Recognition fingerprint

- harness-generated Markdown keeps `managed_by: "aries-harness"` in frontmatter
- every managed Markdown file should declare a `harness_layer`
- every managed Markdown file should also declare `effective_status` and `effective_since`
- richer trace-aware docs should also carry `content_fingerprint`, `trace_history_source`, `trace_last_commit_sha`, `trace_last_commit_at`, and `trace_revision_count`
- the root marker file is `ARIES_HARNESS_FINGERPRINT.json`

## Layer model

- `MetaDefineLayer` holds stable harness operating definitions, planning truth, design intent, gates, and approval boundaries
- `RunCookingLayer` holds the live execution stack, phase progression, state updates, and produced evidence
- `SharedSupportSurface` holds shared entry docs, memory, generated history, and archive material

## Root rule

Keep the root high-signal and clearly labeled.

- canonical recovery docs stay in the root for compatibility and fast resume
- `PIPELINE.md` is the RunCookingLayer phase ledger from requirements through deployment
- extra Markdown moves into managed subdirectories when organization is needed

## Managed directories

- `layers/`
- `history/`
- `memory/`
- `checkpoints/`
- `decisions/`
- `runs/`
- `references/`
- `archive/`

## Engineering pipeline collections

- `references/requests/`
- `references/specs/`
- `references/stories/`
- `references/domain/`
- `references/iterations/`
- `references/tasks/`
- `references/risks/`
- `decisions/architecture/`
- `decisions/adrs/`
- `runs/tests/`
- `runs/reports/`
- `runs/github/`
- `runs/deployments/`

## Document trace

- use `/aries-harness history-refresh` to generate `history/DOC_TRACE.md` and `history/doc-trace.json`
- the same refresh also regenerates `history/DAILY_SUMMARY_INDEX.md` and `history/daily/*.md` for per-day development memo and feature evolution
- treat those outputs as trace surfaces, not as replacements for the underlying source docs

## Facility assets

Harness tooling stays inside this directory (not at the project root):

- `scripts/` — `aries-harness.sh`, `ah.sh`, init / organize / history helpers
- `templates/` — init skeletons (`*.tmpl`) used by `init`

Canonical invoke:

```bash
bash .aries_harness/scripts/aries-harness.sh history-status --project-root .
```

