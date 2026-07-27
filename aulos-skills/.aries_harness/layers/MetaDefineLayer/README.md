---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "layer-manifest"
harness_layer: "MetaDefineLayer"
layer_manifest_for: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:05Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:05Z"
content_fingerprint: "sha256:8fc288864f2b9c81a237b9e5dfd4db44b4981cf92df28b17e18fa050f0f0c54e"
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

## Meta principles

- `references/META-001-meta-principles.md` — fleet纲领: root-cause thinking, asset sync, engineering craft

## Rules

- keep durable requirements, design, policy, and gate definitions here
- do not treat transient run output as MetaDefine truth
- when run evidence changes a stable rule, promote the conclusion here after review
