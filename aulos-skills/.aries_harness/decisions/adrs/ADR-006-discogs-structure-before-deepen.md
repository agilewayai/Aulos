---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T22:10:00Z"
effective_status: "active"
effective_since: "2026-08-01T22:10:00Z"
content_fingerprint: "sha256:163a4c656ed362a675600c0d75e0ba436b21d83d63dd69831b48d84619d12992"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-006 — Discogs structure before deepen

## Status

Accepted (2026-08-01)

## Context

SPEC-033 stopped collapsing multi-catalog titles into one track, but the listening
pipeline could still deepen via a generic family pack with empty deepdives. The
operator covenant: for multi-work Discogs pressings, **fully fetch → structure →
then layer deepen**.

## Decision

1. Introduce a first-class `ReleaseStructure` artifact (SPEC-034) built from the
   full Discogs payload **before** corpus/synthesize thicken.
2. Promote the order as META-001 §4.1 (fleet covenant).
3. Emit structure from analyze + diary snapshot; subsequent slices hard-gate
   Agent deepen on `structure_ready` and expand per `expansion_plan`.

## Consequences

- Multi-work guides gain an explicit program map even when Catalog `work_id` is null.
- Family scaffolds may not short-circuit program recognition.
- Slightly more intake CPU; no extra Discogs API calls beyond the existing full fetch.

## Alternatives rejected

- Per-release craft YAML for famous discs (violates unknown-case / data-over-heuristics).
- Hoping IntentLock `multi_work` alone forces thick prose (it does not fill chambers).
