---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "mission"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:76845dc9f8e3e7fd2a15c1d77974a9272bccfc4d441b1a9be03783d6ac7527c9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Mission

## Outcome

- Deliver an MCP server (`aulos-mcp`) so hosts and agents can integrate with Aulos through Model Context Protocol tools.

## Scope boundary

- In scope: FastMCP stdio server, built-in tools, offline unit tests, harness artifact ladder
- Out of scope: OAuth MCP hosts, remote SSE productization, irreversible external tools without approval

## Success test

- pytest green; FastMCP server builds with echo/now/status tools; ARCH/SPEC/STORY linked

## Approval boundaries

- Live external side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
