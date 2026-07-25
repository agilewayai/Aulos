---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "adr"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:05Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:05Z"
content_fingerprint: "sha256:e4b9471857700b0895d56f007b2ef7f8ce3a36474220d18acf4e78bef0db4ca5"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Decisions

## Decision index

- ADR-004 — Catalog over procedural identity heuristics (`decisions/adrs/ADR-004-catalog-over-heuristics.md`)

## Current decision

- Work Catalog + IdentityResolver own listening identity; RAG does not alone confirm work.

## Detailed architecture artifacts

- store architecture design packs under `decisions/architecture/`
- store detailed ADR records under `decisions/adrs/`
