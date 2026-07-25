---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:00:00Z"
effective_status: "active"
effective_since: "2026-07-25T17:00:00Z"
content_fingerprint: "sha256:16fc8b21c30b9e1cb216a27b39e157b7f5c0d4233140fe2f91b7a4c0c506cfb8"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-007 — Timezone: store UTC, display OS local

## Contract

1. Persistence and API wire timestamps are UTC (ISO-8601 with explicit ``Z``).
2. Product UIs format timestamps in the user OS / browser timezone.
3. Harness-generated Markdown may keep UTC for shared operator docs.

## Implementation anchors

- ``aulos_api.timefmt.to_utc_iso`` / ``to_utc_iso_optional``
- ``aulos-web/src/time.ts``, ``aulos-ops/src/time.ts``

## Acceptance

- Unit tests assert UTC ``Z`` wire form.
- UI helpers use ``toLocaleString(undefined, …)`` without forcing ``timeZone: 'UTC'``.
