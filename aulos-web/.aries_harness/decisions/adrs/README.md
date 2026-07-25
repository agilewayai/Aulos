---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "pipeline-adrs-readme"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:42Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:42Z"
content_fingerprint: "sha256:167e915331187d369b53e649130c1b2c0dd537d1779ac60b892a4c167dc6d843"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR Records

Use this directory for detailed architecture decision records that are linked from the root `ADR.md` index.

## Recommended naming

- `ADR-*`
- `decision-*`

## Each artifact should make clear

- decision statement
- context and tradeoffs
- consequences and affected artifacts
- owner and status

## Layer rule

- this directory belongs to `MetaDefineLayer`
- keep `ADR.md` as the short decision index and avoid duplicating transient execution logs here
