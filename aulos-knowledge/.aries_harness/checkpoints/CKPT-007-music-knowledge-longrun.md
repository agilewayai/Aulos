---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "checkpoint"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:25:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:22:35+00:00"
content_fingerprint: "sha256:7aee84bcda0a18fd28e78df31ddc63b3be95d3fecc5cf212853563d3414e224c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# CKPT-007 — Music knowledge longrun

## Artifact header

- Artifact ID: CKPT-007
- Artifact type: checkpoint
- Status: **complete**
- Owner: ubuntu
- Canonical path: checkpoints/CKPT-007-music-knowledge-longrun.md
- Upstream: REQ-007, SPEC-009, SPEC-010, STORY-PACK-007
- Downstream: VR-007, SUM-007
- Verification state: verified
- Last reviewed: 2026-07-25T17:22:35Z

## Runtime links

- Run ID: RUN-knowledge-longrun-2026-07-26
- Slice ID: S5 closeout
- Checkpoint ID: CKPT-007

## objective

Ship an auditable professional music knowledge plane (SPEC-009/010) physically
separate from business SQLite; enable work_id-filtered RAG consumption.

## completed work

- S0: STORY-PACK-007, CKPT-007, STATE, TASK_STACK, REG, MEMORY
- S1: README Postgres/pgvector path; `deploy/pg_smoke.sh`; `.env.example`; SQLite tests green
- S2: `_rag_context` resolves Catalog `work_id` → plane retrieve; hard-fail bleed tests
- S3: `docs/worker.md`; disabled source → 400; connector failure → status=failed + error
- S4: OPS Knowledge tab plane badge + empty-state when unreachable
- S5: VR-007 + SUM-007 + journal + history-refresh
- P0 scaffold retained (connectors, OPS proxy, feature flag default off)

## in-progress work

- none (longrun package complete)

## next step

1. Optional: run `bash deploy/pg_smoke.sh` where docker is available
2. Later TASK_STACK: ARQ worker; pgvector ANN indexes; Discogs/IMSLP (compliance-gated)

## blockers / risks

- **Residual:** PG smoke SKIP on this host (no docker) — docs + script ready
- Wikidata/MusicBrainz live network flaky — not in default unit path beyond catalog

## verification performed

```bash
cd aulos-knowledge && .venv/bin/python -m pytest tests/ -q
# 8 passed
cd aulos-api && .venv/bin/python -m pytest tests/test_knowledge_plane_rag.py -q
# 1 passed
bash aulos-knowledge/deploy/pg_smoke.sh
# SKIP: docker not available
```

## verification still needed

- Live PG compose smoke on a docker-capable host (recorded residual, not blocking package)

## context state

- op: **continue** (package closed; new work starts a new story/checkpoint)
- carry: CKPT complete, VR-007, residual PG smoke
- noise: low
