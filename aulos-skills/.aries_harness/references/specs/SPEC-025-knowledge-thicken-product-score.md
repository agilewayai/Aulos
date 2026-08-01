---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T19:20:00Z"
effective_status: "active"
effective_since: "2026-08-01T19:20:00Z"
content_fingerprint: "sha256:7b0e32be2bed0139a47bf958e526386842b4958970337f7959879e2139e8a5c6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-025 — Knowledge thicken + ProductScorecard

Upstream: REQ-015. Complements SPEC-024, SPEC-019, SPEC-008.

## Knowledge thicken (`knowledge_thicken.py`)

Input: knowledge-plane composer dossier JSON.

Output chamber patch:

| Source | Salon chamber |
| --- | --- |
| `portrait.source_url` / media | `composer_portrait` |
| `composer.summary_*` / lifespan / era | `composer_profile` |
| major timeline events | `genesis` (year/place/background) |
| `composer.name_zh` / `summary_zh` | `zh.composer_profile` |

Merge rule: fill empty / below-floor only; never clobber richer KB/LLM/craft-pack.

API (`knowledge_proxy.fetch_composer_dossier_sync`) + listening_guide after identity lock
injects `kb_dossier["_knowledge_composer"]` and chamber patch under `_knowledge_thicken`.

## Work craft packs

Path: `aulos-listening-corpus/assets/craft/{work_id}.yaml`  
Loaded in synthesize when `work_id` set; merged after family, before ensure_chamber_floor.

## ProductScorecard (`product_scorecard.py`)

Schema `aulos.product_scorecard/v1`. Dimensions (0–3 each):

- identity_clarity
- craft_richness
- bilingual_parity
- prose_hygiene
- atelier_coverage

`rollup.pct` / `band` ∈ {weak, fair, solid, strong}.  
`eval_pass` ⇔ product band ∈ {solid, strong} and no high product hard findings.  
Process scorecard unchanged (pipeline diagnostic).

## Acceptance gates

- `tests/test_knowledge_product_score.py` (thicken + craft + product score)
- `tests/test_marker_boundaries.py` (digit alien bounds)
- EVAL.md commands updated
- Guide #50: product scorecard persisted; craft + knowledge-plane in synthesize_source
