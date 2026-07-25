---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "adr"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:45:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:45:00+00:00"
content_fingerprint: "sha256:afcce064bedf404876b7e442ea4104df7ca8af8bfe047c8214f37e51ff637944"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-007 — Business Postgres primary + SQLite failover mirror

## Context

Knowledge plane already runs on durable Postgres. Business traffic (`users`, guides,
settings, local RAG cache) still lived on a single SQLite file — a single point of
failure for availability.

## Decision

1. **Primary**: Postgres database `aulos` on the same hardened Docker Postgres host
   as knowledge (`aulos_knowledge` remains a separate DB — no table mixing).
2. **Failover**: local SQLite file (`AULOS_DB_FAILOVER_URL`) kept as a full-table
   mirror for break-glass availability.
3. **Sync**: Redis list `aulos:db_sync:queue` for OPS-enqueued clones + scheduled
   full clone (default 300s). Inline clone if Redis unavailable.
4. **Failover**: OPS can switch `AULOS_DB_ACTIVE_ROLE` / runtime role; optional
   auto-failover when primary probe fails (failback default off).

## Consequences

- Operators use OPS **Fleet → Business DB HA** to enqueue sync and switch roles.
- Tests remain SQLite-primary by default; HA tests use dual SQLite files.
- Knowledge plane DB is unchanged and still independent.
