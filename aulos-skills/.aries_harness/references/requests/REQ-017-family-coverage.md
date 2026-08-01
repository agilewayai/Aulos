---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T19:55:00Z"
effective_status: "active"
effective_since: "2026-08-01T19:55:00Z"
content_fingerprint: "sha256:d822c0352f8161c9d05a0e159f4b9fc361256cd37f86766ca1959de6efce885c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-017 — Genre family coverage + Catalog family lock

## Problem

SPEC-026 catalog floors still fall back to generic scaffolds when no family pack
matches. Four Catalog works (piano concerto, requiem, symphony, piano trio) had
`family_id: null` and no genre family — cold paths stay thin on those shapes.

## Outcomes

1. Genre family packs for piano-concerto, sacred-requiem, symphony-orchestra,
   piano-trio (bilingual Salon floors).
2. Catalog `family_id` set on every Catalog work; synthesize prefers Catalog
   `family_id` over fuzzy match alone.
3. Catalog craft floor auto-loads family by `work.family_id` when caller omits family.
4. Composer cards for Mahler + Dvořák in synthesize index.

## Non-goals

- Per-work craft YAML for every flagship in this slice.
- Blocking compose on knowledge dossier completion.

## Acceptance

- Every Catalog work has non-null `family_id` pointing at a registered family.
- Synthesize for Mozart K.488 / Requiem / Mahler 5 / Dumky includes `family:…` +
  `catalog-floor:…`.
- Unit tests in `tests/test_family_coverage.py`.
