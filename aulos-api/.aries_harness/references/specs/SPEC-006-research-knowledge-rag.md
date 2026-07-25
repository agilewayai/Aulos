---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:23:49+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:23:49+00:00"
content_fingerprint: "sha256:6d67e66cba44aa961e4a8e2b4da5919ece5afc143eb05fa2bbd5e5f99e6c0e59"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-006 — Research knowledge base & vector RAG

## Behavior

After each listening-guide compose/recompose:

1. Persist full Salon Codex dossier into `ListeningGuide.research_json` (`corpus_dossier` + eval meta).
2. Upsert `knowledge_documents` / `knowledge_chunks` for `work_key` + `user_id` (global seeds use `user_id=NULL`).
3. Embeddings via **local FastEmbed** (default, `provider=local`) or ops-configured OpenAI-compatible `/embeddings`.
   If neither works → lexical hash vectors (`rag_mode=lexical`).
   Default local model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (EN+ZH).

Before the skill chain:

1. `retrieve(query, work_hint, composer, user_id)` → top-k chunks + best-matching `kb_dossier`.
2. Pass `kb_dossier` / `rag_hits` / `rag_mode` into SkillRuntime synthesize (merge layer `kb-rag`).

## APIs

- `GET /v1/knowledge/search?q=&work_hint=` (auth)
- `GET /v1/knowledge/stats` (auth)
- `GET|PUT /v1/ops/embeddings` (superadmin)
- `GET /v1/ops/knowledge/stats` (superadmin)

## Seed

Curated corpus YAML (`bwv-988`, …) indexed once as global documents on first retrieve/stats.

## Verification

- Compose indexes chunks; search returns Goldberg hits without embed key (lexical).
- Recompose reindexes same work_key.
