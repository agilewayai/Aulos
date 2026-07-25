---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:012f69e9893750894fd9332e428f58cf7ca1d80894cc20ebdf19a00640f5cb0e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-001 — Vite + React as the web GUI runtime

## Status

- accepted

## Context

- Need a Sprint-0 runtime for `aulos-web` that is easy to verify offline and extend later.

## Decision

- Use Vite + React + TypeScript with a thin fetch client to aulos-api (dev proxy in vite.config).

## Consequences

- Positive: fast local iteration; clear seam to siblings
- Negative: will need auth/observability hardening before production
