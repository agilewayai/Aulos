---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "layer-manifest"
harness_layer: "SharedSupportSurface"
layer_manifest_for: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:42Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:42Z"
content_fingerprint: "sha256:5261e7a9bd7d31d6cdb819fcf1b2f4eff72ba30ad2a555ed6db66190832932a2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SharedSupportSurface

This surface supports both primary layers with entry docs, memory, generated projections, and retained history.

## Owns root docs

- `README.md`
- `INDEX.md`
- `MEMORY.md`

## Owns managed collections

- `layers/`
- `memory/`
- `memory/cards/`
- `history/`
- `archive/`

## Rules

- keep support material concise and clearly secondary to the primary layer truths
- generated projections such as `history/` do not replace either primary layer
- `MEMORY.md` may retain durable lessons from both layers, but it should not become a hidden process log
