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
content_fingerprint: "sha256:0173798772f05b5364b0cc225d982d7ff4d67385fb337272e97caf43bb1e37fa"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-006 — Allowlisted sources + mandatory artifact provenance

## Status

Accepted

## Decision

1. Only **registered SourceAuthority** rows may be crawled or imported.
2. Every published KnowledgeDocument requires `source_id` + `artifact_id` +
   `job_id` + `extractor_version` (or explicit `origin=catalog_seed` with file hash).
3. Raw fetch bytes/HTML/JSON are stored as **artifacts** for audit replay.
4. Failed or ToS-unclear extracts go to **quarantine**, never silent publish.

## Consequences

- OPS must register Wikidata / MusicBrainz / Catalog before jobs run.
- Connectors declare license_class and rate limits.
- Audit UI can open provenance for any chunk.
