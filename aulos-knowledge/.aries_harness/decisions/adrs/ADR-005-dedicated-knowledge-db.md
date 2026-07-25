---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "adr"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:15:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:15:00+00:00"
content_fingerprint: "sha256:114d9422ce29c4101d3edc6a10b3a9c7d7858086a7922c2a6741d59794b44620"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-005 — Dedicated Postgres knowledge DB (not business SQLite)

## Status

Accepted

## Decision

Music encyclopedic data lives in **aulos-knowledge** with its own database
(production: **PostgreSQL + pgvector**). It must not share tables with users,
listening guides, or OPS system settings in `aulos.db`.

## Consequences

- New deployables: knowledge API, worker, Postgres, Redis.
- aulos-api becomes a client/proxy for retrieve and ops audit.
- Local SQLite KnowledgeDocument tables are deprecated for encyclopedia use.
