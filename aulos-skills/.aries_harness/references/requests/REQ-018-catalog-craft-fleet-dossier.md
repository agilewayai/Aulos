---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:00:00Z"
content_fingerprint: "sha256:fa801cb7b6696f1ef5722d11e3fcf9aba2fa757faa4871a45c52d89306edbccd"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-018 — Catalog craft coverage + fleet dossier ensure

## Problem

SPEC-027 gave every Catalog work a genre family. Thickness above family still depends
on hand craft YAML (only Mendelssohn had one) and on whether a composer dossier was
already crawled. Cold Catalog paths cannot all reach ProductScorecard `asset_depth=3`.

## Outcomes

1. **Craft pack for every Catalog work** under `assets/craft/{work_id}.yaml`
   (work-bound thesis / map / ZH / caveats above family floor).
2. **Fleet dossier ensure** — ops/API can enqueue `build-dossier` for every Catalog
   `composer_id` whose knowledge dossier is thin (batch, non-blocking).

## Non-goals

- Waiting for dossier crawls inside a single compose.
- Replacing curated corpus HTML for flagships that already ship rich corpus.

## Acceptance

- `list_craft_pack_ids()` covers every Catalog `work_id`.
- Unit: synthesize source for K.488 / Requiem includes `craft:`.
- Unit/API: `ensure_catalog_composer_dossiers` reports thin→enqueued vs rich→skip.
- EVAL.md updated.
