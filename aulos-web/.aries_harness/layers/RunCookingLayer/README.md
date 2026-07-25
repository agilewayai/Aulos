---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "layer-manifest"
harness_layer: "RunCookingLayer"
layer_manifest_for: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:42Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:42Z"
content_fingerprint: "sha256:6f23418946f3c18931eea71d6ad940e25fab3f5a86f30f23bd4a5ffcf97f7571"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# RunCookingLayer

This layer holds the live execution queue, phase progression, state transitions, checkpoints, and delivery evidence.

## Owns root docs

- `TASK_STACK.md`
- `PIPELINE.md`
- `STATE.md`
- `JOURNAL.md`

## Owns managed collections

- `checkpoints/`
- `runs/`
- `runs/tests/`
- `runs/reports/`
- `runs/github/`
- `runs/deployments/`

## Rules

- keep current execution state and evidence here
- do not redefine stable architecture, approval policy, or mission boundaries here
- summarize what happened and promote stable conclusions back into `MetaDefineLayer` when they harden
