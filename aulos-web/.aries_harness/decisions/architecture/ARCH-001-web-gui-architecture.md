---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:a3774faaab72f9e03916a61c6828ccd15b5036e2751b572f1642e0c58592b97d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Design Pack

## Document Control

- Architecture ID: ARCH-001
- Title: aulos-web Vite/React GUI architecture
- Status: active
- Owner: ubuntu
- Related request: REQ-001
- Related spec: SPEC-001
- Child refs: ADR-001, STORY-001
- Last reviewed: 2026-07-25

## Design Drivers

- Primary business outcome: governed `aulos-web` (web GUI) for the Aulos initiative
- Quality attributes: modularity, offline testability, clear sibling contracts
- Constraints: Sprint-0 skeleton; aries-harness recovery surface

## Current And Target Shape

- Target shape: `browser → App.tsx chat console → api.ts → aulos-api `/v1/chat``

## Package layout

```text
aulos-web/
├── .aries_harness/
├── src/App.tsx, api.ts, styles
├── public/
├── scripts/aries-harness/
└── package.json
```

## Integration boundaries

- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent
- Prefer HTTP through `aulos-api` for GUI traffic; MCP for host/tool integrations

## Open decisions

- Auth model deferred
- Production deploy deferred
