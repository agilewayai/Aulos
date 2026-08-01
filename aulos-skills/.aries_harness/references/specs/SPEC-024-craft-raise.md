---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T18:50:00Z"
effective_status: "active"
effective_since: "2026-08-01T18:50:00Z"
content_fingerprint: "sha256:f282f148e97134265e9d509d00e4f97086e765ee3f330179297747e62754836e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-024 — Work Resolver + chamber contracts + cold thicken

Upstream: REQ-014. Complements SPEC-008, SPEC-023, SPEC-022.

## Work Resolver (`work_resolver.py`)

Input: `raw_message`, `work_hint`, optional `kb_dossier` (Discogs seed).

Steps:

1. Prefer Discogs `work_title` / `composer` when provenance is discogs.
2. `clean_packaging_work_title` on candidate title.
3. `resolve_identity(cleaned_title + composer, work_hint=cleaned)`.
4. If status=`work`, lock Catalog `work_id`, `family_id`, canonical titles.
5. Discogs path **must not** clear a successful Catalog lock.

## Chamber contracts (`chamber_contracts.py`)

Required when `work_id` or `family_hints` or rich family floor present:

| Chamber | EN floor | ZH parity |
| --- | --- | --- |
| listening_thesis | ≥ 40 chars, not mostly CJK | thesis present if EN craft |
| listening_map | ≥ 3 cues | ≥ 2 if EN map ≥ 3 |
| width_points | ≥ 3 | ≥ 2 if EN ≥ 3 |
| depth_points | ≥ 3 | optional soft |
| genesis | non-empty dict | soft |
| sound_world | non-empty dict | soft |
| myths_and_caveats | ≥ 1 | soft |

`ensure_chamber_floor(dossier, family)` fills empties from family; `mirror_zh_parity`
copies EN craft into ZH when ZH thin (then operator/LLM may rewrite).

## Eval gate

`_run_eval`: if identity-resolved and `audit_chamber_contracts` has high gaps →
`pass=False`, score ≤ 7, notes list gaps.

## Assets

- Register `lyric-piano-miniatures` in synthesize `index.yaml`.
- Add Mendelssohn composer synthesize card.
- Family YAML gains `zh` craft layer + sample interpretations.
