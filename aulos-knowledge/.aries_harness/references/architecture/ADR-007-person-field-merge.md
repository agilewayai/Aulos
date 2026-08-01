---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T08:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T08:00:00Z"
content_fingerprint: "sha256:a83b808b5d085fc7227959f784d7ba8dfdeabbf6a70f186d8b1dbbd2e606afb5"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-007 — Field-level merge for person entity cards

## Context

Winner-take-all (Discogs *or* Wikidata) discards complementary authority facts and
blocks bilingual presentation.

## Decision

Use **field-level merge** across registry-verified fragments:

1. Collect fragments (local row, Discogs, Wikidata, Wikipedia EN/ZH).
2. Merge by SPEC-012 precedence tables.
3. Persist one ComposerEntity + per-source knowledge docs.
4. Fill missing locale via API LLM translation, never invent identity.

Discogs credentials and LLM stay in **aulos-api**; knowledge owns merge + store.
API posts Discogs as an optional `fragments[]` into `/aggregate`.

## Consequences

- Cards carry `sources[]` provenance for UI attribution.
- Slightly higher latency on first enrich (parallel fetches).
- Translation quality depends on OPS LLM readiness; native encyclopedia preferred.
