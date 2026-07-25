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
content_fingerprint: "sha256:e73a4c8611b620089e9b884b3a65e1a46e8a30849008f7bc20b2e14be40a181e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-009 — Knowledge service API & data contracts

## Service

`aulos-knowledge` default `:5095`

## Entities (minimum)

- `source_authorities` — id, name, tier, connector, base_urls, license_class, rate_limit_qps, enabled
- `fetch_jobs` — id, source_id, status, params_json, error, started_at, finished_at
- `fetch_artifacts` — id, job_id, source_id, content_hash, content_type, storage_path, source_url, fetched_at
- `composers` / `works` / `recordings` — professional entities + external ids + optional `aulos_work_id`
- `knowledge_documents` / `knowledge_chunks` — text + embedding + provenance FKs + status (published|quarantine)

## APIs

### Public / internal read

- `GET /health`
- `POST /v1/kb/retrieve` body: `{query, work_id?, composer_id?, k?}` → hits + optional dossier snippets
- `GET /v1/kb/stats`

### Admin

- `GET|POST /v1/admin/sources`
- `PATCH /v1/admin/sources/{id}`
- `GET|POST /v1/admin/jobs`
- `GET /v1/admin/jobs/{id}`
- `GET /v1/admin/documents?status=`
- `POST /v1/admin/documents/{id}/quarantine`
- `GET /v1/admin/artifacts/{id}`
- `GET /v1/admin/provenance/{document_id}`

## Acceptance

- Unregistered source cannot enqueue a job (400).
- Published document provenance endpoint returns source + artifact + job.
- Retrieve with `work_id=bach.cello-suites…` does not return Goldberg-only docs when filters applied.
