---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:9231f8c95104da78b96408517d61f393d2611c06684680f9bd5ac42c6462ec62"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Design Pack

## Document Control

- Architecture ID: ARCH-001
- Title: aulos-ops portal architecture
- Status: active
- Related request: REQ-001
- Related spec: SPEC-001
- Child refs: ADR-001, STORY-001

## Design Drivers

- Primary business outcome: governed `aulos-ops` (admin and ops portal)
- Quality attributes: modularity, offline testability, clear sibling contracts

## Target shape

- `browser → App.tsx ops dashboard → api.ts → aulos-api /health + static fleet catalog`

## Package layout

```text
aulos-ops/
├── .aries_harness/
├── src/App.tsx, api.ts, styles
├── public/
├── .aries_harness/scripts/
└── package.json
```

## Open decisions

- Auth model deferred
- Production deploy deferred
