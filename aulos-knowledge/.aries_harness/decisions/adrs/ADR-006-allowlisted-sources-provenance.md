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
effective_since: "2026-07-27T11:20:00Z"
content_fingerprint: "sha256:1b4dfc773c641f75e0fbc2b464324b60c53bda184683926aa26aff52819cf822"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-006 — Allowlisted sources + mandatory artifact provenance

## Status

Accepted (revised 2026-07-27 — Authority Source Registry)

## Decision

1. Only **registered SourceAuthority** rows may be crawled or imported.
2. **Normative registry** lives in Git as `data/registry/sources.yaml` (REG-SRC-001).
   DB is the runtime + verification state. Boot sync upserts metadata without
   silently overriding human verification/enabled unless `force: true`.
3. Crawl requires **`enabled` + `verification_status=verified` + registered connector**.
   Verification and enablement are independent (verified-but-disabled is allowed).
4. Every published KnowledgeDocument requires `source_id` + `artifact_id` +
   `job_id` + `extractor_version` (or explicit identity_seed origin with file hash).
5. Raw fetch bytes/HTML/JSON are stored as **artifacts** for audit replay.
6. HTTP fetches must stay within the source's registered `base_urls` (fetch policy).
7. Failed, ToS-unclear, or non-auto-publish extracts go to **quarantine**, never silent
   publish. Auto-publish only under publish_policy (tier S + verified + allowed origin_class).

## Consequences

- OPS registers and **verifies** Wikidata / MusicBrainz / Catalog (and future authorities)
  before jobs run.
- Connectors declare license_class and rate limits; candidate sources without connectors
  cannot be enabled for crawl.
- Audit UI shows verification badges and can open document **and chunk** provenance.
- Expanding the classical canon = add registry entry → implement connector → verify → crawl
  (not ad-hoc URLs in code). Registered connectors as of S2/S3: catalog_import, wikidata,
  musicbrainz, wikipedia, imslp, rism (Grove remains candidate).
