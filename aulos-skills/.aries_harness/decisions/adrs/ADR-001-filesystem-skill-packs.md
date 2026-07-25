---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:7eb49f7cdbaba049be7a1253728bb1a5fc3f08c9970d23265b4c3b1b6e94211d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-001 — Filesystem skill packs with YAML manifests

## Status

- accepted

## Context

- Need a Sprint-0 runtime for `aulos-skills` that is easy to verify offline and extend later.

## Decision

- Store skills as directories with skill.yaml + SKILL.md and discover them via a thin Python registry/CLI.

## Consequences

- Positive: fast local iteration; clear seam to siblings
- Negative: will need auth/observability hardening before production
