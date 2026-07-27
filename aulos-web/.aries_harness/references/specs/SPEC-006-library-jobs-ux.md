---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T18:00:00Z"
effective_status: "active"
effective_since: "2026-07-26T18:00:00Z"
content_fingerprint: "sha256:9d62b2ece9da889b163ce285def557c936ffc08f688e3f2b0d49b0e6567189e0"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-006 — Library + durable job UX

Upstream: API SPEC-013.

## Behaviors

1. Compose / recompose via `POST …/jobs` then `GET …/events` (leaving the page does not cancel).
2. On studio load, refresh library; auto-attach to newest `queued`/`running` job.
3. Library: search (`q`), filters All / Favorites / Published / In progress, tag filter.
4. Row: open, favorite star, tags edit, delete confirm; status badge; failed shows error + retry.

## Acceptance

- `npm run build` green; touch targets ≥44px on library actions.
