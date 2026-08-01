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
content_fingerprint: "sha256:cebd10c063e6eb0e7b7b86a660c25ae38c5472d27dd40e03526b9602bf26d8e0"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

## 2026-08-01T17:15:00Z

- **REQ-010 soft-cap → 2048:** `WORKS_CAP` raised from 400 to 2048.
- **Plaza “lost diaries” root cause:** API `db_ha` stuck on **SQLite failover**
  (`auto_failback=false`) while Postgres primary still held the published Horowitz/Mozart
  diary. Failover mirror had a different draft → plaza feed empty. Restored `active_role=primary`
  (API restart); healed guide #47 ghost `running` → `completed`. Diary guide links #47/#48
  derive `ready_for_review` (not deleted).

## 2026-08-01T17:05:00Z

- **REQ-010 Δ Composer dossier works + identity:** Famous QID lock (Mozart no longer Franz
  Xaver); SPARQL works soft-cap 400 with year/catalog order + film/junk filters; dossier payload
  adds `works_by_year` / `works_by_genre`; merge upsert avoids global `works` PK clashes.
  Live rebuild: Mozart 424 / Beethoven ~310 / Bach 397. Tests: `test_composer_dossier` + famous
  persist lock green.

## 2026-08-01T08:10:00Z

- **REQ-012 Multi-source person aggregate + bilingual:** field-merge Discogs + Wikidata +
  Wikipedia EN/ZH (ADR-007); API fan-in + OPS LLM translate for missing locale; 聆乐 card
  中文/EN toggle. Tests: merge precedence + aggregate endpoint + API orchestration green.

## 2026-08-01T07:45:00Z

- **REQ-011 match fix:** strict person identity (no CJK soft match; orphan RAG cannot invent
  cards). Discogs artist profile is now first enrich authority (API → ingest), then Wikidata/
  Wikipedia. Tests: unrelated 朱莉亚尼/Giuliani ≠ Bach; Discogs-before-wikidata API path.

## 2026-08-01T07:30:00Z

- **REQ-011 Person entity cards:** `person_entity.resolve_person_card` — local composer+RAG first,
  then Wikidata search + Wikipedia summary enrich; persist composer + searchable chunk (prefer
  wikidata tier-S publish). Route `POST /v1/kb/entities/person/resolve`. Tests: `test_person_entity.py`
  3 passed. API proxy `/v1/entities/person`; 聆乐 names clickable → side panel.

## 2026-08-01T06:35:00Z

- **Ship closeout / Honeycomb:** REQ-009 source discovery + REQ-010 composer dossier + benchmark /
  diagnose-improve + async job queues aligned in INDEX/REG-001; fleet Honeycomb before git push.
- Gates: knowledge pytest suite (benchmark / dossier / discovery / job_queue / diagnosis) + API
  `test_knowledge_benchmark_task`.

## 2026-07-27T16:55:00Z

- **REQ-010 Composer life dossier + works tree:** `composer_life_events` + works parent/kind/years +
  composers era/summary; Wikidata `mode=composer_dossier` (claims → timeline, SPARQL P86 → works tree);
  `GET/POST .../composers/{id}/dossier|build-dossier` (202 async); OPS **Composer dossier** module;
  pytest mocks green; live Bach smoke: birth/death + 80 works, job succeeded.

## 2026-07-27T16:50:00Z

- **Crawl async queue (META-001 §3.3):** `job_queue.py` background dispatch + drain loop;
  `POST /jobs` → **202** when async; production `SYNC_JOBS=false`; OPS polls until terminal.
  Sync remains pytest escape hatch only.

## 2026-07-27T16:45:00Z

- **Fix Explore seeds 404:** redeployed `aulos-knowledge` / ops so `/explore/seeds` + `prepare-seeds` live;
  prepare now respects `sync_jobs` (was stuck queued); featured-first portrait seed; client fallback catalog.

## 2026-07-27T16:40:00Z

- **Explore product UX (META-001 §3.4 Meta Play Simple):** A–Z composer picker + Famous/Featured strip;
  `GET .../explore/seeds`, `POST .../prepare-seeds`, media content proxy for portraits; QID hidden under Advanced.
- Expanded `FAMOUS_COMPOSERS` seed network; OPS Explore module redesigned as human-first entry.

## 2026-07-27T16:20:00Z

- **REQ-009 follow-on:** explore → auto-enqueue authority crawl (Wikidata/Wikipedia/MusicBrainz/IMSLP);
  `POST .../enqueue-crawl`; diagnosis proposes `explore_sources` L1 for corpus/registry/retrieval gaps;
  OPS interactive SVG discovery graph + crawl job panel.

## 2026-07-27T13:10:00Z

- **REQ-009 Source discovery:** `source_discovery.py` depth+breadth graph search from registry seeds +
  Wikidata authority links + composer/work entities; `source_discovery_runs` table; admin explore APIs;
  OPS **Explore sources** module; pytest `test_source_discovery.py`.

## 2026-07-27T12:50:00Z

- **KB-DIAG-001 / KB-IMPROVE-001:** diagnosis engine (`diagnosis.py`), improvement executor
  (`improvement.py`), auto-diagnose after benchmark; L1 auto crawl (Wikipedia/Wikidata/catalog);
  L3 engineering tasks for RAG/code; OPS **Diagnose & improve** module; `knowledge.improve` ops task.

## 2026-07-27T12:35:00Z

- **Benchmark async queue:** `benchmark_runs` state machine (queued→running→succeeded|failed);
  `POST /v1/admin/benchmark/run?async=true` returns 202; background thread dispatch.
- Ops task `knowledge.benchmark` via `POST /v1/ops/knowledge/benchmark/run`.
- META-001 §3.3 long-running work & task queues.

## 2026-07-27T12:25:00Z

- **Performance dashboard report:** `GET /v1/kb/benchmark/dashboard` aggregates trend, insights,
  executive summary; OPS **Performance report** module + Overview compact summary card.

## 2026-07-27T12:10:00Z

- **KB-BENCH-001:** benchmark suite (`data/benchmark/suite.yaml`), scoring engine (`benchmark.py`),
  `benchmark_runs` table, admin APIs; OPS Knowledge **Benchmark** module (run, history, report).
- SPEC-009/010 updated; `tests/test_benchmark.py`.

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
