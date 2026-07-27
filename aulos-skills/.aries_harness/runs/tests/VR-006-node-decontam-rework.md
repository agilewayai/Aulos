---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "verification-report"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T19:25:00Z"
effective_status: "active"
effective_since: "2026-07-26T19:25:00Z"
content_fingerprint: "sha256:9d4ab5eec042e86b2afca20689d5308bc088da668c3476dd87e00366fb83d6a6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# VR-006 — Node decontam + family evidence (SPEC-009)

## Scope

Guide #44 Brahms Violin Concerto Op.77 pollution; per-node decontam rework.

## Checks

| Check | Result |
| --- | --- |
| `pytest tests/test_runtime.py tests/test_ambient_agent.py tests/test_identity.py` | 29 passed |
| Family composer alone does not unlock `duo-cello-piano` | covered by Brahms regression |
| Per-node decontam gate present on synthesize→compose | `runtime._decontam_gate` |
| Ambient foreign-composer form unlock blocked | `ambient_agent._score_related` |

## Residual risk

Cold Discogs works without Catalog `work_id` still depend on catalog-derived alien markers;
adding frequent works (e.g. Brahms Op.77) to Catalog remains follow-up.
