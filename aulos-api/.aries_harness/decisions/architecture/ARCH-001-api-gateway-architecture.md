---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:e17bd1a1d33948b1dc8c319c4bc97501c04121d804fa3fdeeda40cdbf9c83457"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Design Pack

## Document Control

- Architecture ID: ARCH-001
- Title: aulos-api FastAPI gateway architecture
- Status: active
- Owner: ubuntu
- Related request: REQ-001
- Related spec: SPEC-001
- Child refs: ADR-001, STORY-001
- Last reviewed: 2026-07-25

## Design Drivers

- Primary business outcome: governed `aulos-api` (API gateway) for the Aulos initiative
- Quality attributes: modularity, offline testability, clear sibling contracts
- Constraints: Sprint-0 skeleton; aries-harness recovery surface

## Current And Target Shape

- Target shape: `clients → FastAPI routes → AgentProxy → aulos-agent / aulos-mcp (optional)`

## Package layout

```text
aulos-api/
├── .aries_harness/
├── src/aulos_api/{app,cli,config,routes,services}
├── tests/
├── scripts/aries-harness/
└── pyproject.toml
```

## Integration boundaries

- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent
- Prefer HTTP through `aulos-api` for GUI traffic; MCP for host/tool integrations

## Open decisions

- Auth model deferred
- Production deploy deferred
