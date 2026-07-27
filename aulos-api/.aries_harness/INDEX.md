---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "harness-index"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness well-organized"
initialized_at: "2026-07-25T11:07:43Z"
last_organized_at: "2026-07-27T10:25:06+00:00"
effective_status: "generated"
effective_since: "2026-07-27T10:25:06+00:00"
content_fingerprint: "sha256:331ad2b4b105b55afba86584968d3b8c894423098ade44afc3a1998a5fcc52d9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Harness Index

Last organized: `2026-07-27T10:25:06+00:00`

Canonical spelling: `/aries-harness well-organized`

Fingerprint marker: `aries-harness` / `aries-harness/bootstrap-doc/v1`

## Layer manifests

- [MetaDefineLayer](layers/MetaDefineLayer/README.md)
- [RunCookingLayer](layers/RunCookingLayer/README.md)
- [SharedSupportSurface](layers/SharedSupportSurface/README.md)

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
- [RISKS.md](RISKS.md)
  risk and approval boundaries
- [ADR.md](ADR.md)
  high-level architecture decisions
- [RUNBOOK.md](RUNBOOK.md)
  start, resume, takeover, and rollback notes

### Managed collections

#### `references/`
- role: meta-definition collections and reference packs
- [HDM-001-harness-design-memo.md](references/HDM-001-harness-design-memo.md)
- [REG-001-artifact-register.md](references/REG-001-artifact-register.md)
- [TRACE-001-value-traceability.md](references/TRACE-001-value-traceability.md)

#### `references/requests/`
- role: upstream request briefs and business intent anchors
- [README.md](references/requests/README.md)
- [REQ-001-aulos-api-bootstrap.md](references/requests/REQ-001-aulos-api-bootstrap.md)
- [REQ-002-users-roles-auth-mvp.md](references/requests/REQ-002-users-roles-auth-mvp.md)
- [REQ-003-classical-listening-guide-mvp.md](references/requests/REQ-003-classical-listening-guide-mvp.md)
- [REQ-006-rag-work-identity-catalog.md](references/requests/REQ-006-rag-work-identity-catalog.md)
- [REQ-008-discog-release-guide.md](references/requests/REQ-008-discog-release-guide.md)
- [REQ-009-durable-guide-jobs-library.md](references/requests/REQ-009-durable-guide-jobs-library.md)

#### `references/specs/`
- role: behavior and acceptance contracts derived from requests
- [README.md](references/specs/README.md)
- [SPEC-001-api-gateway.md](references/specs/SPEC-001-api-gateway.md)
- [SPEC-002-users-roles-auth.md](references/specs/SPEC-002-users-roles-auth.md)
- [SPEC-003-listening-guide-workflow.md](references/specs/SPEC-003-listening-guide-workflow.md)
- [SPEC-006-research-knowledge-rag.md](references/specs/SPEC-006-research-knowledge-rag.md)
- [SPEC-007-timezone-utc-store-local-display.md](references/specs/SPEC-007-timezone-utc-store-local-display.md)
- [SPEC-008-discog-release-guide.md](references/specs/SPEC-008-discog-release-guide.md)
- [SPEC-009-ops-dev-blog.md](references/specs/SPEC-009-ops-dev-blog.md)
- [SPEC-010-salon-email-craft.md](references/specs/SPEC-010-salon-email-craft.md)
- [SPEC-011-mail-queue.md](references/specs/SPEC-011-mail-queue.md)
- [SPEC-012-chain-trace.md](references/specs/SPEC-012-chain-trace.md)
- [SPEC-013-listening-guide-jobs-library.md](references/specs/SPEC-013-listening-guide-jobs-library.md)
- [SPEC-014-session-cookie-auth.md](references/specs/SPEC-014-session-cookie-auth.md)
- [SPEC-015-guide-html-security.md](references/specs/SPEC-015-guide-html-security.md)
- [SPEC-017-dev-blog-writing-contract.md](references/specs/SPEC-017-dev-blog-writing-contract.md)
- [SPEC-018-ops-task-queue.md](references/specs/SPEC-018-ops-task-queue.md)

#### `references/stories/`
- role: sprintable slices linked to specs and verification
- [README.md](references/stories/README.md)
- [STORY-PACK-001-bootstrap.md](references/stories/STORY-PACK-001-bootstrap.md)
- [STORY-PACK-002-auth-mvp.md](references/stories/STORY-PACK-002-auth-mvp.md)
- [STORY-PACK-008-discog-release-guide.md](references/stories/STORY-PACK-008-discog-release-guide.md)

#### `references/domain/`
- role: domain analysis and modeling artifacts
- [README.md](references/domain/README.md)

#### `references/iterations/`
- role: iteration and sprint planning artifacts
- [README.md](references/iterations/README.md)

#### `references/tasks/`
- role: detailed task breakdown and slice maps
- [EC-001-bootstrap-execution-card.md](references/tasks/EC-001-bootstrap-execution-card.md)
- [README.md](references/tasks/README.md)

#### `references/risks/`
- role: detailed risk registers and mitigation notes
- [README.md](references/risks/README.md)

#### `decisions/`
- role: meta decisions and decision packs
- none

#### `decisions/architecture/`
- role: system design and architecture packs
- [ARCH-001-api-gateway-architecture.md](decisions/architecture/ARCH-001-api-gateway-architecture.md)
- [ARCH-002-users-roles-auth.md](decisions/architecture/ARCH-002-users-roles-auth.md)
- [README.md](decisions/architecture/README.md)

#### `decisions/adrs/`
- role: detailed ADR records linked from the root ADR index
- [ADR-001-fastapi-gateway.md](decisions/adrs/ADR-001-fastapi-gateway.md)
- [ADR-002-sqlite-jwt-mailgun.md](decisions/adrs/ADR-002-sqlite-jwt-mailgun.md)
- [ADR-007-business-pg-sqlite-failover.md](decisions/adrs/ADR-007-business-pg-sqlite-failover.md)
- [ADR-008-plaintext-systemsetting-secrets-sprint1.md](decisions/adrs/ADR-008-plaintext-systemsetting-secrets-sprint1.md)
- [README.md](decisions/adrs/README.md)

## RunCookingLayer

### Root docs
- [TASK_STACK.md](TASK_STACK.md)
  active tasks, milestone, blockers, and next slices
- [PIPELINE.md](PIPELINE.md)
  engineering phase ledger from requirements to deployment
- [STATE.md](STATE.md)
  current run state, workspace, and next action
- [JOURNAL.md](JOURNAL.md)
  milestones, failures, and resume hints

### Managed collections

#### `checkpoints/`
- role: pause, resume, handoff, and checkpoint artifacts
- [CKPT-008-discog-release-guide.md](checkpoints/CKPT-008-discog-release-guide.md)

#### `runs/`
- role: run summaries and execution evidence
- none

#### `runs/tests/`
- role: test execution and fix evidence
- [README.md](runs/tests/README.md)
- [VR-001-story-001-bootstrap.md](runs/tests/VR-001-story-001-bootstrap.md)
- [VR-002-auth-mvp.md](runs/tests/VR-002-auth-mvp.md)
- [VR-013-listening-guide-jobs-library.md](runs/tests/VR-013-listening-guide-jobs-library.md)

#### `runs/reports/`
- role: iteration reports and closeouts
- [README.md](runs/reports/README.md)

#### `runs/github/`
- role: commit, PR, and merge evidence
- [README.md](runs/github/README.md)

#### `runs/deployments/`
- role: deployment, smoke, and rollback evidence
- [README.md](runs/deployments/README.md)

## SharedSupportSurface

### Root docs
- [README.md](README.md)
  entry point and command hints
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
- [INDEX.md](memory/INDEX.md)

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
