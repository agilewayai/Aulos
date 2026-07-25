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
content_fingerprint: "sha256:1bee9cdd18c127bc5c13b5f095117807072d36b4bbac363ce71244e7e01a7620"
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

## Identity gate (hard)

Identity confirmation is owned by the **Work Identity Catalog** (aulos-skills SPEC-008).
API RAG must not alone decide which work a query is about.

`works_compatible(query, doc_…)` / retrieve:

- Prefer explicit `work_id` / `corpus_key` match against resolved identity when provided.
- Composer-only overlap is never enough.
- Catalog prefixes and generic form words are **weak** (shared policy with skills catalog).
- Soft-filter: require ≥1 non-weak distinctive token; composer-only queries must not open
  the whole composer shelf.
- Seed indexes Catalog identity cards (short chunks) alongside full Salon dossiers so the
  correct attractors exist in the vector/lexical space.
- `kb_dossier` attaches only when the best doc passes the identity gate at the score floor.

## Verification

- Compose indexes chunks; search returns Goldberg hits without embed key (lexical).
- Recompose reindexes same work_key.
- Retrieve for Bach cello suites / 大提琴无伴奏组曲 must **not** attach Goldberg `kb_dossier`.
- Retrieve for Mozart must not attach Goldberg hits.
- Chopin / Mahler catalog slots must not collapse onto Goldberg without Resolver code changes.
