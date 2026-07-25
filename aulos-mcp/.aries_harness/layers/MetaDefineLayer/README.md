---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "layer-manifest"
harness_layer: "MetaDefineLayer"
layer_manifest_for: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:44Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:44Z"
content_fingerprint: "sha256:81ef8118e103fa9992dfde3912f50b67d6f7567380517c85d446d8d8336e1ba6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# MetaDefineLayer

This layer holds stable harness operating definitions, planning truth, design intent, gates, and approval boundaries.

## Owns root docs

- `MISSION.md`
- `ADR.md`
- `RUNBOOK.md`
- `EVAL.md`
- `RISKS.md`

## Owns managed collections

- `references/`
- `references/requests/`
- `references/specs/`
- `references/stories/`
- `references/domain/`
- `references/iterations/`
- `references/tasks/`
- `references/risks/`
- `decisions/`
- `decisions/architecture/`
- `decisions/adrs/`

## Rules

- keep durable requirements, design, policy, and gate definitions here
- do not treat transient run output as MetaDefine truth
- when run evidence changes a stable rule, promote the conclusion here after review
