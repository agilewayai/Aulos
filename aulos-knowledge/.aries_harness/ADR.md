---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "adr"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:20:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:20:00+00:00"
content_fingerprint: "sha256:aa8c77450eec4ebd38a9ba19dde0441e5f75fa3403dc373379ec0dc38bee3995"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Decisions

## Decision index

- ADR-005 — Dedicated Postgres knowledge DB
- ADR-006 — Allowlisted sources + mandatory artifact provenance

## Current decision

- Knowledge plane is physically separate from business SQLite; OPS audits via proxy.
