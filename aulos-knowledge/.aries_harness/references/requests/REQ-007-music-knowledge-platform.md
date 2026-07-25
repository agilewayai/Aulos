---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:15:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:15:00+00:00"
content_fingerprint: "sha256:a4a869f0f7925e355a44814c8874d2f08bbb7db2abc3eb27b9ea3c6b67300072"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-007 — Professional Music Knowledge Platform

## Why now

Listening guides need deep, trustworthy knowledge of works, composers, history, and
discography. Today’s SQLite RAG cache shares the user/business database and cannot
scale, cannot audit provenance, and cannot run crawlers safely.

## Outcome

- Dedicated **aulos-knowledge** plane: Postgres (+ pgvector), crawl workers, artifact store.
- **Registered authority sources** (Wikidata, MusicBrainz, Catalog, …) with license + rate limits.
- Every published chunk is **observable and auditable** (source → artifact → job → review).
- OPS **Knowledge** tab for source registry, jobs, provenance, retrieve lab.
- Business DB (`aulos.db` users/guides/ops settings) stays **physically separate**.

## Non-goals (this request)

- Mirroring commercial streaming catalogs wholesale.
- Unlicensed full-site HTML scraping of Discogs/paywalled reviews.
- Replacing Work Identity Catalog (SPEC-008) — identity stays in skills catalog.

## Links

- ARCH-005, ADR-005, ADR-006, SPEC-009, SPEC-010, DOM-003
