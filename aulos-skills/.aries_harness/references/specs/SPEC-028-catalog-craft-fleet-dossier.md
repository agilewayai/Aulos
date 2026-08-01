---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:00:00Z"
content_fingerprint: "sha256:7fc871c87dcec71f5a017016c00489cb161303cc6d5f5c4946746f468a146bbc"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-028 — Catalog craft coverage + fleet dossier ensure

Upstream: REQ-018. Extends SPEC-025–027.

## Craft packs

Path: `aulos-listening-corpus/assets/craft/{work_id}.yaml`

Gate: for every Catalog work, a craft file exists with:

- `work_id`, EN `listening_thesis` (≥40), ZH thesis (≥12)
- `listening_map` ≥3, `width_points` ≥3, `depth_points` ≥3
- work-specific myths/caveats (identity conflicts when Catalog declares them)

`craft_packs.list_craft_work_ids()` / `assert_catalog_craft_coverage()` for tests.

Merge order unchanged: family → catalog-floor → **craft** → …

## Fleet dossier ensure (API)

`knowledge_proxy.ensure_catalog_composer_dossiers(*, dry_run=False) -> dict`

1. Load Catalog composer ids.
2. For each: fetch dossier; if `dossier_is_thin`, enqueue build (unless dry_run).
3. Return `{rich: [...], enqueued: [...], failed: [...], dry_run}`.

Ops: `POST /v1/ops/knowledge/composers/ensure-dossiers`  
Body optional `{ "dry_run": true }`. Auth = ops admin (same as other knowledge ops).

## Acceptance

- `tests/test_catalog_craft_coverage.py`
- API test for ensure endpoint (dry_run / mocked enqueue)
- EVAL.md SPEC-028
