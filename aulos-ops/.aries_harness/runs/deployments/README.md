---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "pipeline-deployments-readme"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:06Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:06Z"
content_fingerprint: "sha256:2f0758c941705a9fbfedac9e87fa5973221d205827f6e42de981bba0382b8e81"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Production Deployments

Use this directory for deployment logs, smoke-check summaries, rollback notes, and operator signoff evidence.

## Recommended naming

- `DEPLOY-*`
- `rollout-*`
- `production-*`
- `rollback-*`

## Each artifact should make clear

- environment and release target
- smoke or rollback result
- owner and approval state

## Layer rule

- this directory belongs to `RunCookingLayer`
- keep rollout policy or deployment standards in meta rules, not in deploy run evidence
