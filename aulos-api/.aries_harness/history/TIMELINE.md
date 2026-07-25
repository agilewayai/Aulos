---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "history-timeline"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:07:43Z"
generated_at: "2026-07-25T18:52:15+00:00"
effective_status: "generated"
effective_since: "2026-07-25T18:52:15+00:00"
content_fingerprint: "sha256:60db80b993ce2e1158e1f3e7f56922de56ba77bcf33e4514c9ba3dda7d35034b"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-25T18:52:15+00:00`

## Journal milestones

### 2026-07-25T18:25:45Z

- Web research loop: thin RAG → Wikipedia/DDG (+ optional Brave) → LLM verify → KB upsert (user + global)
- Ops `/v1/ops/web-research` + LLM tab controls; query variants for opus-specific titles
- Verified: `tests/test_web_research.py` 5 passed; live Dvořák Dumky `rag_mode=no_match+web-research`, persisted docs 12/13, next search 6 hits

### 2026-07-25T17:22:35Z

- STORY-PACK-007 S2: `_rag_context` resolves Catalog work_id for knowledge-plane retrieve
- Client-side drop of mismatched `aulos_work_id` hits; `tests/test_knowledge_plane_rag.py` green

### 2026-07-26T01:15:00Z

- RAG aligned to Work Identity Catalog (REQ-006): seed identity cards; weak tokens from policy
- works_compatible respects work_id; identity_only cards never replace full dossiers

### 2026-07-26T00:55:00Z

- RAG identity gate: `bwv`/form words are weak tokens; soft-filter requires distinctive overlap
- Retrieve must not attach Goldberg `kb_dossier` to Bach cello suites / 大提琴无伴奏组曲
- SPEC-006 identity hard-gate + regression tests

### 2026-07-25T17:15:00Z

- Listening gateway delegates to AgentProxy.run_listening (no local iter_listening_chain)

### 2026-07-25T17:00:00Z

- Added ``aulos_api.timefmt.to_utc_iso``; listening/ops/mailgun wire UTC ``Z``; tests/test_timefmt.py

### 2026-07-25T14:53:12Z

- Research KB + vector RAG: knowledge_documents/chunks, embeddings ops settings, lexical fallback, corpus seed
- Recompose/update-publish APIs; by-share ownership; studio + /g owner toolbar
- SPEC-006; listening tests for KB search + recompose slug stability

### 2026-07-25T11:52:22Z

- STORY-002..005 auth MVP: users/roles, register/verify/login, Mailgun config (fakeable), superadmin ops gate
- SQLite + JWT + bcrypt; bootstrap superadmin via env
- aulos-web register/login/verify UI; aulos-ops superadmin + Mailgun settings
- pytest auth suite green; public smoke on aulos.purezen.ai / aulos-ops.purezen.ai

## Recent git commits

- `555cf53` 2026-07-26 Ship listening product, mandatory harness, facility layout, and UTC/local time.
- `93c0f6e` 2026-07-25 Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- `7632d9b` 2026-07-25 Add aulos-web, aulos-api, and aulos-mcp sub-projects under aries-harness.
- `0d5cb01` 2026-07-25 Initial commit: Aulos hackathon workspace with LangChain agent runtime.

## Working tree snapshot

- `M` `aulos-agent/.aries_harness/INDEX.md`
- `M` `aulos-agent/.aries_harness/JOURNAL.md`
- `M` `aulos-agent/.aries_harness/MEMORY.md`
- `M` `aulos-agent/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
- `M` `aulos-agent/.aries_harness/history/DOC_TRACE.md`
- `M` `aulos-agent/.aries_harness/history/README.md`
- `M` `aulos-agent/.aries_harness/history/RETROSPECTIVE.md`
- `M` `aulos-agent/.aries_harness/history/ROADMAP.md`
- `M` `aulos-agent/.aries_harness/history/STATUS.md`
- `M` `aulos-agent/.aries_harness/history/TIMELINE.md`
- `M` `aulos-agent/.aries_harness/history/daily/2026-07-25.md`
- `M` `aulos-agent/.aries_harness/history/doc-trace.json`
