---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T19:55:00Z"
effective_status: "active"
effective_since: "2026-08-01T19:55:00Z"
content_fingerprint: "sha256:e28e9e0350cf78ed901816eda76ec004aab3527ad384bfa309e96520d6df3dc4"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-027 — Genre family coverage + Catalog family lock

Upstream: REQ-017. Extends SPEC-026.

## Family packs

Paths under `aulos-listening-synthesize/assets/families/`:

| family_id | Covers |
| --- | --- |
| `piano-concerto` | Solo piano + orchestra concertos |
| `sacred-requiem` | Requiem / sacred mass with choir+orchestra |
| `symphony-orchestra` | Multi-movement orchestra symphonies |
| `piano-trio` | Violin+cello+piano trios (incl. dumky / character sets) |

Each pack ships EN+ZH: thesis, map (≥3), width/depth (≥3), genesis, sound_world,
practice, myths. Registered in `assets/index.yaml`.

## Catalog lock

Every `catalog/works/*.yaml` sets `family_id` to a registered pack.

`_run_synthesize`: if `work_id` resolves and Catalog has `family_id`, prepend to
`family_hints` before `_match_family`.

`build_catalog_craft_floor`: when `family` arg empty and work has `family_id`,
`load_family_pack(family_id)` and bind.

## Acceptance

- `tests/test_family_coverage.py`
- EVAL.md SPEC-027 line
