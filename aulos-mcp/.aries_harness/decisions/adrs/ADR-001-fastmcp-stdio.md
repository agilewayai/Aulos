---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:593805973f41e05de2eadaf528785482e8c6839f1bbfcc43c0a93bda8bfafe66"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-001 — FastMCP stdio as the MCP transport

## Status

- accepted

## Context

- Need a Sprint-0 runtime for `aulos-mcp` that is easy to verify offline and extend later.

## Decision

- Use the official MCP Python FastMCP helper with stdio transport and pure offline-safe tools first.

## Consequences

- Positive: fast local iteration; clear seam to siblings
- Negative: will need auth/observability hardening before production
