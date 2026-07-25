---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "architecture"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:15:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:15:00+00:00"
content_fingerprint: "sha256:3753a40eb9e96edda7f8f7b41b64b32e26d12700a896acc564cfb4ec541b70ab"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ARCH-005 — Music knowledge plane vs business plane

## Planes

| Plane | Service | Store | Owns |
| --- | --- | --- | --- |
| Business | aulos-api, aulos-web, aulos-ops auth | SQLite `aulos.db` | Users, guides, mail, LLM settings |
| Identity | aulos-skills Catalog / Resolver | YAML catalog | `work_id` confirmation |
| Knowledge | **aulos-knowledge** | **Postgres + pgvector** | Entities, sources, crawls, chunks |

## Components

- **FastAPI aulos-knowledge** — admin + retrieve APIs
- **PostgreSQL 16 + pgvector** — entities + vectors (dev may use SQLite JSON embeddings)
- **Redis + ARQ** — crawl/ingest jobs (dev: in-process sync runner)
- **Artifact store** — `data/artifacts/{source_id}/{job_id}/{hash}` raw evidence
- **Connectors** — catalog_import, wikidata, musicbrainz (allowlist only)
- **aulos-api proxy** — `/v1/ops/knowledge/*` + RAG retrieve client
- **aulos-ops Knowledge tab** — audit UI

## Integration

1. Intake resolves `work_id` via Catalog (unchanged).
2. API retrieve calls knowledge service filtered by `work_id` / composer.
3. User guide upserts do **not** become global encyclopedic truth.
