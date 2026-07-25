---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "adr"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:01:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:01:00+00:00"
content_fingerprint: "sha256:37edfe19d0e60476b1e2a03c2affd0d5fc7b2573cc0e248762b6cfe7bedc8413"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-004 — Catalog over procedural identity heuristics

## Status

Accepted

## Context

Case patches (Bach cello `elif`, Goldberg scrub tuples, ambient conflict special-cases)
stopped one failure mode but cannot productize Chopin, Mahler, or future shelves.
RAG nearest-neighbor was incorrectly treated as work identity.

## Decision

1. **Work Catalog YAML is the identity authority.**
2. **IdentityResolver** is the only intake identity path — generic scoring, no work-name branches.
3. **RAG must not alone decide work identity**; it may attach dossiers only when catalog
   `work_id` / `corpus_key` matches the resolved identity.
4. Scrub and ambient conflict handling read **catalog-derived** conflict markers and facets.

## Consequences

- Adding a composer/work = authoring catalog records (+ optional dossier/family).
- Runtime identity `elif` trees are debt; remove and forbid regressions.
- Thin catalog slots (Chopin/Mahler) are valid before full Salon dossiers exist.

## Rejected alternatives

- Continue stacking per-work `if` branches in `runtime.py`.
- Rely on LLM free-text to name the work without catalog confirmation.
- Treat embedding similarity as sufficient same-work proof.
