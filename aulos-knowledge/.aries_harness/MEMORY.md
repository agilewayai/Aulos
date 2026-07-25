---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "memory"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:25:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:25:00+00:00"
content_fingerprint: "sha256:7aebec7c88f73a036865beb09feb580e825636f70b289ae11b6917ffefacf472"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# MEMORY — aulos-knowledge (hot)

## Hard constraints

- Business SQLite (`aulos.db`) must never store encyclopedic music KB tables.
- Only allowlisted SourceAuthority rows may crawl/import (ADR-006).
- Published docs require provenance (source + artifact + job).
- Catalog/Resolver owns `work_id` identity; KB owns content richness.

## Active longrun

- CKPT-007 / STORY-PACK-007 — **complete** (see VR-007). Residual: PG smoke on docker host.
