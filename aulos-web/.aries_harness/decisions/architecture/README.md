---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "pipeline-architecture-readme"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:42Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:42Z"
content_fingerprint: "sha256:9528e4ba2cdd158a07543d8682f1f64492bf3d3928b16e3f8dfe8d717e78a4a2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# System Design

Use this directory for architecture design packs, system-design notes, interface boundaries, and implementation-facing design deltas.

## Recommended naming

- `ARCH-*`
- `system-design-*`
- `architecture-*`

## Each artifact should make clear

- design intent
- main components or seams
- tradeoffs
- linked risks and verification anchors

## Layer rule

- this directory belongs to `MetaDefineLayer`
- keep runtime execution output and debugging transcripts out of architecture packs
