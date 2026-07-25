---
schema_version: "0.1"
project_id: "aulos-api"
owner: "arthur"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:47:11Z"
effective_status: "active"
effective_since: "2026-07-25T11:47:11Z"
content_fingerprint: "sha256:d195eee0aafb3672d74435a437c5fc12606f9af51245fe61d87e40f9ae175902"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-002 — SQLite + JWT + Mailgun (fakeable)

## Status
accepted

## Decision
- Persist users/roles/settings in SQLite for Sprint-1 MVP
- Issue JWT bearer tokens after verified login
- Use Mailgun HTTP API with a fake in-memory provider for offline tests; configure credentials via ops (superadmin)

## Consequences
- Simple local deploy; migrate to Postgres later if needed
- Ops becomes source of truth for mail provider config once bootstrapped
