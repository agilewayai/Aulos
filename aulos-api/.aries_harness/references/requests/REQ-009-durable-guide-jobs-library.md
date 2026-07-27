---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "request"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T18:00:00Z"
effective_status: "active"
effective_since: "2026-07-26T18:00:00Z"
content_fingerprint: "sha256:cb0ab75cd83f179b4ee573b76de3c19cecf1be7234a8c035172a95f914bf1d46"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-009 — Durable listening-guide jobs + library management

## Outcome

Guide composition survives leaving the browser: jobs enter a queue, a worker advances the workflow, and clients reconnect to progress. Owners can delete, search/filter, favorite, and tag finished (and in-flight) guides.

## Acceptance

- Enqueue returns immediately with `queued` guide row; worker reaches `completed` or `failed` without an open SSE client.
- List supports `q`, status/published/favorited/tag filters.
- Owner DELETE removes the row.
- Favorite + freeform tags round-trip on the wire.

## Non-goals

Celery/ARQ fleet; soft-delete; collaborative drafts.
