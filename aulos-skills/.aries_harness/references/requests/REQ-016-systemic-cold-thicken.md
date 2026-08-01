---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T19:40:00Z"
effective_status: "active"
effective_since: "2026-08-01T19:40:00Z"
content_fingerprint: "sha256:522b25d175ba000cce9db0d04b9fbc3e0f3b1d12094364e02e69e75b0685e3bb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-016 — Systemic cold-path thicken (any Catalog work)

## Problem

SPEC-025 raised craft for works that already have a hand-written craft YAML and a
built knowledge dossier. Most Discogs / cold paths still sit on a thin family floor
+ LLM — the **pipeline** is general, but **thickness** is not. Operators feel the
system is still gauze-thin on arbitrary cases.

## Outcomes

1. **Catalog craft floor** — any Catalog-resolved `work_id` gets a work-bound craft
   layer derived from Catalog work + composer card + matched family (no per-work
   prose YAML required). Explicit `assets/craft/{work_id}.yaml` still wins.
2. **Auto dossier build** — when composer identity is locked and the knowledge-plane
   dossier is thin, enqueue `build-dossier` (async) so the *next* compose thickens.
3. **Product asset provenance** — ProductScorecard scores whether thickness came from
   craft pack / knowledge / catalog floor / family-only; identity-resolved shelves
   cannot claim `strong` on family-or-scaffold alone.

## Non-goals

- Hand-authoring every work craft YAML in this slice.
- Blocking the current compose on dossier crawl completion.
- Replacing curated corpus / LLM enrichment.

## Acceptance

- Unit: catalog floor binds Chopin nocturne (or any catalog work) without craft YAML.
- Unit: thin dossier detection + enqueue helper (mocked HTTP).
- Unit: product `asset_depth` dims; family-only cannot be strong when identity-resolved.
- EVAL.md updated.
