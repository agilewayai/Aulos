---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "harness-index"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness well-organized"
initialized_at: "2026-07-25T17:25:00+00:00"
last_organized_at: "2026-08-02T07:27:26+00:00"
effective_status: "generated"
effective_since: "2026-08-02T07:27:26+00:00"
content_fingerprint: "sha256:0615dce88a3720e880f499da367efd93f01fe862c781a70397c7697be5ce5e6d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Harness Index

Last organized: `2026-08-02T07:27:26+00:00`

Canonical spelling: `/aries-harness well-organized`

Fingerprint marker: `aries-harness` / `aries-harness/bootstrap-doc/v1`

## Layer manifests

- MetaDefineLayer: missing `layers/MetaDefineLayer/README.md`
- RunCookingLayer: missing `layers/RunCookingLayer/README.md`
- SharedSupportSurface: missing `layers/SharedSupportSurface/README.md`

## Layer model

- `MetaDefineLayer` defines stable mission, architecture, gates, risk policy, and planning truth
- `RunCookingLayer` carries the live execution stack, progression state, checkpoints, and delivery evidence
- `SharedSupportSurface` provides shared entry docs, memory, generated history, and archive material

## MetaDefineLayer

### Root docs
- [MISSION.md](MISSION.md)
  north star, boundary, and success test
- [EVAL.md](EVAL.md)
  verification commands and acceptance gate
- [ADR.md](ADR.md)
  high-level architecture decisions

### Managed collections

#### `references/`
- role: meta-definition collections and reference packs
- [REG-001-artifact-register.md](references/REG-001-artifact-register.md)

#### `references/requests/`
- role: upstream request briefs and business intent anchors
- [REQ-007-music-knowledge-platform.md](references/requests/REQ-007-music-knowledge-platform.md)
- [REQ-008-authority-source-registry.md](references/requests/REQ-008-authority-source-registry.md)
- [REQ-009-source-discovery-graph.md](references/requests/REQ-009-source-discovery-graph.md)
- [REQ-010-composer-dossier.md](references/requests/REQ-010-composer-dossier.md)
- [REQ-011-person-entity-cards.md](references/requests/REQ-011-person-entity-cards.md)
- [REQ-012-person-multi-source-bilingual.md](references/requests/REQ-012-person-multi-source-bilingual.md)

#### `references/specs/`
- role: behavior and acceptance contracts derived from requests
- [SPEC-009-knowledge-api-and-data.md](references/specs/SPEC-009-knowledge-api-and-data.md)
- [SPEC-010-ops-knowledge-audit-ui.md](references/specs/SPEC-010-ops-knowledge-audit-ui.md)
- [SPEC-011-person-entity-card.md](references/specs/SPEC-011-person-entity-card.md)
- [SPEC-012-person-multi-source-bilingual.md](references/specs/SPEC-012-person-multi-source-bilingual.md)

#### `references/stories/`
- role: sprintable slices linked to specs and verification
- [STORY-PACK-007-music-knowledge-plane.md](references/stories/STORY-PACK-007-music-knowledge-plane.md)

#### `references/domain/`
- role: domain analysis and modeling artifacts
- [DOM-003-music-knowledge.md](references/domain/DOM-003-music-knowledge.md)

#### `references/iterations/`
- role: iteration and sprint planning artifacts
- none

#### `references/tasks/`
- role: detailed task breakdown and slice maps
- none

#### `references/risks/`
- role: detailed risk registers and mitigation notes
- none

#### `decisions/`
- role: meta decisions and decision packs
- none

#### `decisions/architecture/`
- role: system design and architecture packs
- [ARCH-005-knowledge-plane.md](decisions/architecture/ARCH-005-knowledge-plane.md)

#### `decisions/adrs/`
- role: detailed ADR records linked from the root ADR index
- [ADR-005-dedicated-knowledge-db.md](decisions/adrs/ADR-005-dedicated-knowledge-db.md)
- [ADR-006-allowlisted-sources-provenance.md](decisions/adrs/ADR-006-allowlisted-sources-provenance.md)

## RunCookingLayer

### Root docs
- [TASK_STACK.md](TASK_STACK.md)
  active tasks, milestone, blockers, and next slices
- [STATE.md](STATE.md)
  current run state, workspace, and next action
- [JOURNAL.md](JOURNAL.md)
  milestones, failures, and resume hints

### Managed collections

#### `checkpoints/`
- role: pause, resume, handoff, and checkpoint artifacts
- [CKPT-007-music-knowledge-longrun.md](checkpoints/CKPT-007-music-knowledge-longrun.md)

#### `runs/`
- role: run summaries and execution evidence
- none

#### `runs/tests/`
- role: test execution and fix evidence
- none

#### `runs/reports/`
- role: iteration reports and closeouts
- [SUM-007-music-knowledge-longrun.md](runs/reports/SUM-007-music-knowledge-longrun.md)
- [VR-007-music-knowledge-longrun.md](runs/reports/VR-007-music-knowledge-longrun.md)

#### `runs/github/`
- role: commit, PR, and merge evidence
- none

#### `runs/deployments/`
- role: deployment, smoke, and rollback evidence
- none

## SharedSupportSurface

### Root docs
- [INDEX.md](INDEX.md)
  generated index of root docs and organized collections
- [MEMORY.md](MEMORY.md)
  hot durable memory snapshot and retrieval map

### Managed collections

#### `layers/`
- role: layer manifests and ownership guides
- none

#### `memory/`
- role: cold memory maps and durable cards
- none

#### `history/`
- role: generated history projections
- [DAILY_SUMMARY_INDEX.md](history/DAILY_SUMMARY_INDEX.md)
- [DOC_TRACE.md](history/DOC_TRACE.md)
- [README.md](history/README.md)
- [RETROSPECTIVE.md](history/RETROSPECTIVE.md)
- [ROADMAP.md](history/ROADMAP.md)
- [STATUS.md](history/STATUS.md)
- [TIMELINE.md](history/TIMELINE.md)

#### `archive/`
- role: retained historical artifacts
- none

## Command reminders

- `/aries-harness init` creates the stable skeleton.
- `/aries-harness well-organized` keeps the root high-signal and moves extra Markdown into managed collections.
- `/aries-harness pipeline-inspect` checks the engineering pipeline phase ledger, layer markers, artifact paths, and gate coverage.
- `/aries-harness memory-inspect` checks hot-memory size, cold-memory cards, and stale memory hygiene.
- `/aries-harness history-refresh` regenerates readable status, roadmap, timeline, retrospective, daily-summary, and doc-trace docs under `history/`.
- `/aries-harness history-status` prints the same history model as a quick terminal or JSON snapshot.

## Organization rules

- keep canonical recovery docs in the root
- keep `MetaDefineLayer` and `RunCookingLayer` semantically separated even when root entry docs coexist
- move extra run, checkpoint, and design notes under managed collections
- do not delete Markdown files during organization

## Document governance

- every managed Markdown file should declare `effective_status`, `effective_since`, `content_fingerprint`, and git-backed trace fields when history exists
- canonical docs default to `active`; generated history surfaces default to `generated`; archived material defaults to `archived`
- richer per-doc trace fields are `trace_history_source`, `trace_last_commit_sha`, `trace_last_commit_at`, and `trace_revision_count`
- when a closeout-critical phase artifact becomes `done` or `validated`, record `completed_at`, `timebox_actual`, and a `Closeout timing` section instead of relying on `last_updated_at` alone
- use `history/DOC_TRACE.md` and `history/doc-trace.json` for the readable and machine-readable document trace
