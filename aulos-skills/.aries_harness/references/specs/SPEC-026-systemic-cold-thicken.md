---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T19:40:00Z"
effective_status: "active"
effective_since: "2026-08-01T19:40:00Z"
content_fingerprint: "sha256:ae6ff6dcdf82777c6aa19e848cf4b25f0a10f36568b597e1aaf237fef6768102"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-026 — Systemic cold-path thicken

Upstream: REQ-016. Extends SPEC-025 / SPEC-024.

## Catalog craft floor (`catalog_craft_floor.py`)

Input: `work_id`, optional matched family dict, optional composer card.

Behavior:

1. Load Catalog work + composer.
2. Start from `family_to_dossier` when family present; else empty Salon scaffold
   with form inferred from facets.
3. Bind work-specific identity into scalars:
   - `work_title` ← canonical_title
   - `composer` ← composer name_en
   - `catalog` ← catalog_numbers joined
   - `era` / `form` ← facets when empty
   - thesis / introduction mention canonical short title (not packaging dump)
4. Composer profile from Catalog lifespan/era when empty.
5. ZH: bind `canonical_title_zh` / `name_zh` into zh scalars when family zh exists;
   else seed minimal zh thesis from title_zh.
6. Mark `dossier_id=catalog-floor:{work_id}`,
   `_provenance.catalog_craft_floor=true`.

Merge order in synthesize (later wins):

`family → catalog-floor → craft YAML → … → knowledge thicken → chamber floor`

## Auto dossier enqueue (API)

`knowledge_proxy.dossier_is_thin(payload)` — true when missing usable portrait URL
and timeline/events empty.

After identity lock + fetch: if thin and `composer_id` known, POST
`/v1/admin/composers/{id}/build-dossier` fire-and-forget (log only; never block
compose). Set `rag["knowledge_dossier_enqueued"]=true`.

## ProductScorecard `asset_depth` (0–3)

| Score | Provenance |
| --- | --- |
| 3 | Explicit craft pack (`craft:` / `dossier_id` craft:) **or** (knowledge thicken with portrait **and** catalog floor / craft) |
| 2 | Catalog craft floor **or** knowledge thicken with profile/portrait |
| 1 | Family pack only |
| 0 | Generic scaffold / empty |

Rules when `identity_resolved`:

- `asset_depth == 0` → high `product_asset_empty` (fail)
- `asset_depth == 1` → medium `product_asset_family_only`; band capped to ≤ solid
  (cannot be `strong`)

## Acceptance gates

- `tests/test_systemic_cold_thicken.py`
- EVAL.md SPEC-026 line
