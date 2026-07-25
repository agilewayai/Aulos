---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:20c6f62302d6317a92748c5996c7fe85b353731bbd828985261788a39fb57608"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-001 — FastAPI as the gateway runtime

## Status

- accepted

## Context

- Need a Sprint-0 runtime for `aulos-api` that is easy to verify offline and extend later.

## Decision

- Use FastAPI + uvicorn with a pluggable AgentProxy defaulting to fake mode for offline verify.

## Consequences

- Positive: fast local iteration; clear seam to siblings
- Negative: will need auth/observability hardening before production
