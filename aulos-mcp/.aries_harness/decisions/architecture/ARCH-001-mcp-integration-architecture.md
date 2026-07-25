---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:7ad2e929afbf441c212d64a7b88f8c63959b1fc99b6eb697f6873ebc65f06273"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Design Pack

## Document Control

- Architecture ID: ARCH-001
- Title: aulos-mcp FastMCP integration architecture
- Status: active
- Owner: ubuntu
- Related request: REQ-001
- Related spec: SPEC-001
- Child refs: ADR-001, STORY-001
- Last reviewed: 2026-07-25

## Design Drivers

- Primary business outcome: governed `aulos-mcp` (MCP agents integration) for the Aulos initiative
- Quality attributes: modularity, offline testability, clear sibling contracts
- Constraints: Sprint-0 skeleton; aries-harness recovery surface

## Current And Target Shape

- Target shape: `MCP host → stdio → FastMCP tools (echo, now_utc, status) → optional aulos-api bridge later`

## Package layout

```text
aulos-mcp/
├── .aries_harness/
├── src/aulos_mcp/{cli,config,server,tools}
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
