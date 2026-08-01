---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:50:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:50:00Z"
content_fingerprint: "sha256:322eee76ee29cf62bac760befd28e0bb96b18d46c605060e34ac86bc4e61675e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-031 — Dimensional templates + promote-to-production

Upstream: REQ-021. Extends SPEC-029/030. **Anti-case:** no per-work branches.

## Dimension templates (`dimension_templates.py`)

Input: FacetClassifier output + title/composer.

Build family-shaped dict by composing:

- `INSTRUMENT_VOICES[primary_instrument]` (fallback `ensemble`)
- `FORM_VOICES[primary_form]` (fallback `generic-form`)
- optional `ERA_VOICES[era]`

Bind `{short}`, `{composer}`, `{form_label}`, `{instrument_label}` into EN/ZH
thesis / map / width / depth. Mark
`_provenance.dimension_template=true` and `dossier_id=dimension:{inst}+{form}`.

`build_archetype_floor`: prefer registered family pack; else dimension template;
never require a Catalog `work_id`.

## Promote-to-production (`promote_production.py`)

`promote_staged_to_production(*, candidate, staging_pack, composer, work_title,
catalog_root, craft_root, overwrite=False) -> report`

Steps (generic for any candidate):

1. Validate `suggested_work_id` + chamber floors on staging pack.
2. Upsert composer YAML stub (`composer_id` slug from name; aliases from tokens).
3. Upsert work YAML stub: facets from candidate; `family_id` from candidate;
   distinctive_tokens derived from title+facet tokens (algorithmic).
4. Register ids in `index.yaml` if missing.
5. Copy/write production craft from staging pack; strip staging-only caveats;
   set `_provenance.promote_production=true`.
6. Clear `load_catalog` / `load_craft_pack` caches.

Refuse path traversal. Default `overwrite=False`.

## API / Ops

- `POST /v1/ops/listening-guides/{id}/promote-production`
- Guide must have `promote_candidate.status=staged` (or staging file present).
- Mark candidate `status=production` + paths in research_json.
- Ops: “Promote to production” when staged.

## Acceptance

- `tests/test_dimensional_promote.py` — two unrelated titles, same code path.
- `aulos-api/tests/test_promote_production_api.py`
