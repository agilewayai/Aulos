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
content_fingerprint: "sha256:c8a02810cf90732181679a5f34b1abab596056b3f187f95f09b8d5cecc112a1c"
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

### Admin

- `GET|POST /v1/admin/sources`
- `PATCH /v1/admin/sources/{id}`
- `POST /v1/admin/sources/{id}/verify` — body optional `{ by }` → verification_status=verified
- `POST /v1/admin/sources/{id}/reject` — → rejected; enabled=false
- `POST /v1/admin/sources/{id}/suspend` — → suspended; enabled=false
- `GET|POST /v1/admin/jobs`
- `GET /v1/admin/jobs/{id}`
- `GET /v1/admin/documents?status=`
- `POST /v1/admin/documents/{id}/quarantine`
- `GET /v1/admin/artifacts/{id}`
- `GET /v1/admin/provenance/{document_id}` — includes `chunks[]` summaries
- `GET /v1/admin/chunks/{chunk_id}/provenance` — chunk → document → source + artifact + job
- `GET /v1/admin/documents/{id}` — includes `chunks[]`

## Acceptance

- Unregistered source cannot enqueue a job (400).
- Unverified or suspended source cannot enqueue a job (400).
- Fetch outside base_urls raises / fails the job.
- Published document provenance endpoint returns source + artifact + job.
- Chunk provenance endpoint returns chunk text + parent document + source + artifact + job.
- Wikipedia / IMSLP / RISM connectors registered; ingest defaults to quarantine (tier A / media).
- Retrieve with `work_id=bach.cello-suites…` does not return Goldberg-only docs when filters applied.
- Retrieve only returns `status=published` documents.
