---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:15:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:15:00+00:00"
content_fingerprint: "sha256:1180124c3c9eb6d80e3772ff33c9806e6d4f10b080fff65ab78703c6e4e846c2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-009 — Knowledge service API & data contracts

## Service

`aulos-knowledge` default `:5095`

## Entities (minimum)

- `source_authorities` — id, name, tier, connector, base_urls, license_class, rate_limit_qps, enabled,
  **plus registry fields:** verification_status (`candidate|review|verified|rejected|suspended`),
  verified_by, verified_at, tos_notes, attribution_template, allowed_path_prefixes,
  connector_semver, origin_class (`encyclopedia|identity_seed|media|editorial`), registry_revision
- `fetch_jobs` — id, source_id, status, params_json, error, started_at, finished_at
- `fetch_artifacts` — id, job_id, source_id, content_hash, content_type, storage_path, source_url, fetched_at
- `composers` / `works` / `recordings` — professional entities + external ids + optional `aulos_work_id`
- `composer_life_events` — REQ-010 dated life timeline (event_type, dates, place, significance, provenance)
- `works` tree fields: `parent_work_id`, `work_kind`, `year_start`, `year_end`
- `composers` dossier fields: `era`, `summary_en`, `summary_zh`
- `knowledge_documents` / `knowledge_chunks` — text + embedding + provenance FKs + status (published|quarantine)

## Authority registry (REQ-008)

- Normative list: `data/registry/sources.yaml` (REG-SRC-001). Boot sync upserts metadata; does not clobber human `verification_status` / `enabled` unless entry sets `force: true`.
- **Job gate:** enqueue only if `enabled && verification_status == verified && connector registered`.
- **Fetch gate:** HTTP URLs must match source `base_urls` (and optional path prefixes); respect `rate_limit_qps`.
- **Publish gate:** default document status `quarantine`; auto-`published` only when tier=S, verified, and origin_class in {identity_seed, encyclopedia} per `publish_policy`.

## APIs

### Public / internal read

- `GET /health`
- `POST /v1/kb/retrieve` body: `{query, work_id?, composer_id?, k?}` → hits + optional dossier snippets
- `GET /v1/kb/stats`
- `GET /v1/kb/benchmark/dashboard` — aggregated performance report (trend, insights, executive summary)

### Benchmark (KB-BENCH-001)

Normative suite: `data/benchmark/suite.yaml` (retrieve cases with work_id bleed guards).

Dimensions (0–100, weighted overall):

| Dimension | Weight | Signal |
| --- | ---: | --- |
| corpus | 20% | publish ratio, works with published docs |
| registry | 15% | verified + crawl-ready sources |
| provenance | 15% | published docs with source+artifact+job+extractor |
| retrieval | 40% | suite pass rate (required cases) |
| pipeline | 10% | recent job success rate |

- `POST /v1/admin/benchmark/run` → **202** `{id, status: queued}` when async; **200** full report when `sync_jobs` (dev/tests). Query `async=true` forces queue.
- `GET /v1/admin/benchmark/runs?limit=`
- `GET /v1/admin/benchmark/runs/{id}` — poll until `succeeded` | `failed`

Benchmark run state machine: `queued` → `running` → `succeeded` | `failed` (durable `benchmark_runs` row).

Ops unified queue: `POST /v1/ops/knowledge/benchmark/run` → `knowledge.benchmark` task (SPEC-018).

### Diagnosis & improve (KB-DIAG-001 / KB-IMPROVE-001)

- Auto-diagnose after each succeeded benchmark run.
- `GET /v1/admin/benchmark/runs/{id}/diagnosis` — structured findings + actions
- `POST /v1/admin/improvements/execute-safe?diagnosis_id=` — L1 auto crawl (authority sources)
- `POST /v1/admin/improve/cycle` — diagnose → safe actions → re-benchmark
- `POST /v1/ops/knowledge/improve/cycle` → `knowledge.improve` task
- L3 `engineering_task` actions surface coding-layer RAG/retrieve upgrades for harness TASK_STACK.

### Admin

- `GET|POST /v1/admin/sources`
- `PATCH /v1/admin/sources/{id}`
- `POST /v1/admin/sources/{id}/verify` — body optional `{ by }` → verification_status=verified
- `POST /v1/admin/sources/{id}/reject` — → rejected; enabled=false
- `POST /v1/admin/sources/{id}/suspend` — → suspended; enabled=false
- `POST /v1/admin/sources/explore` — REQ-009 depth+breadth graph discovery (`composer_id`, `wikidata_qid`, `enqueue_crawl`)
- `GET /v1/admin/sources/explore/seeds` — A–Z composer catalog + famous/featured + portraits (META-001 §3.4)
- `POST /v1/admin/sources/explore/prepare-seeds` — enqueue Wikidata/Wikipedia for curated famous roster
- `GET /v1/admin/sources/explore/runs` — recent discovery runs
- `GET /v1/admin/sources/explore/runs/{id}` — graph + ranked candidates
- `POST /v1/admin/sources/explore/runs/{id}/register-candidates` — upsert `candidate` sources
- `POST /v1/admin/sources/explore/runs/{id}/enqueue-crawl` — authority bundle crawl for seed
- `GET /v1/admin/media/{id}/content` — portrait bytes for Explore avatars
- `GET|POST /v1/admin/jobs` — crawl enqueue; **202** + `async:true` when queue mode
  (`SYNC_JOBS=false` or `?async=true`); poll `GET .../jobs/{id}` for `queued→running→succeeded|failed`
- `GET /v1/admin/jobs/{id}`
- `GET /v1/admin/documents?status=`
- `POST /v1/admin/documents/{id}/quarantine`
- `GET /v1/admin/artifacts/{id}`
- `GET /v1/admin/provenance/{document_id}` — includes `chunks[]` summaries
- `GET /v1/admin/chunks/{chunk_id}/provenance` — chunk → document → source + artifact + job
- `GET /v1/admin/documents/{id}` — includes `chunks[]`
- `GET /v1/admin/composers/{id}/dossier` — REQ-010 timeline + works_tree + portrait
- `POST /v1/admin/composers/{id}/build-dossier` — enqueue Wikidata `mode=composer_dossier` (**202** async)
- `GET /v1/kb/composers/{id}/dossier` — read dossier (same token gate as admin for S1)

## Acceptance

- Unregistered source cannot enqueue a job (400).
- Unverified or suspended source cannot enqueue a job (400).
- Fetch outside base_urls raises / fails the job.
- Published document provenance endpoint returns source + artifact + job.
- Chunk provenance endpoint returns chunk text + parent document + source + artifact + job.
- Wikipedia / IMSLP / RISM connectors registered; ingest defaults to quarantine (tier A / media).
- Retrieve with `work_id=bach.cello-suites…` does not return Goldberg-only docs when filters applied.
- Retrieve only returns `status=published` documents.
- Benchmark run persists score + markdown report; retrieval dimension fails when cello/Goldberg bleed detected.
- Composer dossier build yields birth/death events and works tree for Bach seed (mocked in pytest).
