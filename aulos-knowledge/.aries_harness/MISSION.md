---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "mission"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T08:45:00Z"
effective_status: "active"
effective_since: "2026-07-27T08:45:00Z"
content_fingerprint: "sha256:fcc075153d2982e4d51c24ae29cd6149c827b0257aa880cb359077c6b454cf7d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Mission

Operate the Aulos professional music knowledge plane: durable sources, fetch jobs, artifacts, published documents, and retrieve APIs scoped by Catalog `work_id`.

## Non-goals

- End-user portal UX (owned by `aulos-web` / `aulos-ops`)
- Business auth and operator RBAC (owned by `aulos-api`; plane uses service token for admin)

## Success signals

- Retrieve honors `work_id` filters and provenance is inspectable
- Admin mutation routes require service bearer token
- Offline pytest green for API, jobs, and audit flows
