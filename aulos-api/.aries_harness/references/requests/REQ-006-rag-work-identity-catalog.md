---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:01:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:01:00+00:00"
content_fingerprint: "sha256:93a495d165c3226279984c0813bbc59415d0ef241298f801cf18634bbd3f21e5"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-006 — RAG respects Work Identity Catalog

## Problem

API RAG attached flagship dossiers (Goldberg) to unrelated Bach queries via weak token
overlap and sparse corpus attraction.

## Outcome

- Seed indexes Catalog identity cards alongside full dossiers.
- `works_compatible` / retrieve gates use catalog `work_id`, aliases, catalog numbers,
  distinctive tokens — not composer-only or catalog-prefix-only matches.
- API never invents work identity; Agent/Skills Resolver owns confirmation.

## Links

- aulos-skills SPEC-008 / ADR-004
- SPEC-006 research knowledge RAG (updated)
