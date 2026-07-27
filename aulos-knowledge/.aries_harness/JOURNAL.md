---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "journal"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:20:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:20:00+00:00"
content_fingerprint: "sha256:05f08a8f4189def6c10c23022442c04415d93f1a2fdf03c06efab42a023f2ade"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

## 2026-07-27T11:55:00Z

- **OPS Knowledge console:** modular UI (overview / source registry / documents / jobs / RAG simulate / media);
  REQ-008 registry as first-class module with crawl-gate visualization; structured provenance cards.
- SPEC-010 rewritten; stats API adds `chunks` + `sources_verified`.

## 2026-07-27T11:40:09Z

- **REQ-008 S2/S3:** Wikipedia + IMSLP + RISM connectors registered; registry revision
  `2026-07-27.2` verifies/enables them (Grove remains candidate, no connector).
- Chunk provenance: `GET /v1/admin/chunks/{id}/provenance` + chunks on document detail/provenance;
  Ops Knowledge audit lists chunks and opens chunk provenance.
- Gates: `tests/test_s2_s3_connectors.py` + registry assertions (23 pytest passed).

## 2026-07-27T11:20:00Z

- **REQ-008 Authority Source Registry (S1):** versioned `data/registry/sources.yaml` (REG-SRC-001);
  SourceAuthority verification lifecycle; job/fetch/publish gates; Ops Sources register/verify/reject/suspend.
- ADR-006 revised; SPEC-009/010 deltas; gates `tests/test_source_registry.py` (pytest green).

## 2026-07-25T17:42:00Z

- Media durability: artifacts root → `data/persist/artifacts` (json + media/image|audio|meta)
- Wikidata P18 portraits + Commons PD audio; MusicBrainz recording/release meta + Cover Art images
- media_assets table + OPS media list; backup packs media blobs; Bach sample: 3 images + 2 meta on disk

## 2026-07-25T17:38:00Z

- Docker durability: switched PG/Redis from named volumes → host bind mounts under `data/persist/`
- Redis AOF+RDB dual persistence; postgres `stop_grace_period=60s`; backup + persist_smoke scripts
- Verified: force-recreate and `compose down`/`up` keep composers=10 docs=55

## 2026-07-25T17:30:00Z

- Installed Docker Engine from Docker Inc. official apt (not snap)
- Hardened compose: digest-pinned pgvector/pgvector + redis, localhost bind, cap_drop
- PG up healthy; crawl bootstrap: 10 composers, 55 published docs, 31/31 jobs succeeded
- Entry points: Bach/Mozart/Beethoven/Chopin/Schubert/Brahms/Tchaikovsky/Mahler/Debussy/Stravinsky
- QIDs verified via enwiki sitelinks (Chopin Q1268, Debussy Q4700, Brahms Q7294, Mahler Q7304)

## 2026-07-25T17:22:35Z

- STORY-PACK-007 longrun closeout (S0–S5): CKPT-007 complete, VR-007 + SUM-007
- S1: Postgres path docs + `deploy/pg_smoke.sh` (SKIP no docker); SQLite tests green
- S2: Catalog `work_id` passed into knowledge retrieve from `_rag_context`; bleed tests hard-fail
- S3: `docs/worker.md`; disabled enqueue 400; failed job status+error tests
- S4: OPS Knowledge plane badge + empty-state when unreachable
- Verify: aulos-knowledge pytest 8 passed; API knowledge_plane_rag 1 passed

## 2026-07-26T01:20:00Z

- Scaffolded aulos-knowledge professional plane (REQ-007 / ARCH-005 / ADR-005/006)
- Sources allowlist + catalog/wikidata/musicbrainz connectors + artifact provenance
- OPS Knowledge tab + aulos-api `/v1/ops/knowledge/plane/*` proxy
- RAG cutover behind `AULOS_KNOWLEDGE_PLANE_ENABLED` (default off)
