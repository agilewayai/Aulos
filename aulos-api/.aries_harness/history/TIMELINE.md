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
generated_at: "2026-07-25T19:31:05+00:00"
effective_status: "generated"
effective_since: "2026-07-25T19:31:05+00:00"
content_fingerprint: "sha256:8d7fb89be47e04764142799a55cdd6f0f9af88bd20b4c53a015ffce2a027e167"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-25T19:31:05+00:00`

## Journal milestones

### 2026-07-25T19:50:00Z

- REVIEW-008 smoke `423-287-1`: was truncating to release 423; now catno search → Mozart/Horowitz
- Fixes: parse catno, Discogs search, exclude composer from performers, workish titles
- Verify: `test_discogs.py` 6 passed; live `resolve_discogs_message("/discogs #423-287-1")` SMOKE_OK

### 2026-07-25T19:40:00Z

- Root cause of “no Discogs token UI”: local-only; live OPS/API not redeployed
- Deployed host: OPS nav **Discogs** tab + `/v1/ops/discogs` (401 without auth = route live)

### 2026-07-25T19:35:00Z

- OPS GUI: dedicated **Integrations** tab for Discogs token (status + enable + save/clear); Overview link

### 2026-07-25T19:30:00Z

- OPS office: `/v1/ops/discogs` + LLM tab form to store Discogs personal user token (overrides env)

### 2026-07-25T19:20:00Z

- Renamed slash command `/discog` → `/discogs` (parser only accepts `/discogs`)

### 2026-07-25T19:15:00Z

- STORY-PACK-008 `/discogs`: REQ/SPEC/STORY/CKPT authored; id = Discogs **release** (master fallback)
- Implemented `services/discogs.py` + `parse_discogs_command`; wired `_run_chain_core` seed vinyl/interpretations
- Studio hint for `/discogs #release-id`; tests: `test_discogs.py` 4 passed; listening-guide regression green

### 2026-07-25T18:25:45Z

- Web research loop: thin RAG → Wikipedia/DDG (+ optional Brave) → LLM verify → KB upsert (user + global)
- Ops `/v1/ops/web-research` + LLM tab controls; query variants for opus-specific titles
- Verified: `tests/test_web_research.py` 5 passed; live Dvořák Dumky `rag_mode=no_match+web-research`, persisted docs 12/13, next search 6 hits

### 2026-07-25T17:22:35Z

- STORY-PACK-007 S2: `_rag_context` resolves Catalog work_id for knowledge-plane retrieve
- Client-side drop of mismatched `aulos_work_id` hits; `tests/test_knowledge_plane_rag.py` green

## Recent git commits

- `53e7437` 2026-07-26 Ship identity catalog, Hans/Hant locales, web research, and knowledge plane.
- `555cf53` 2026-07-26 Ship listening product, mandatory harness, facility layout, and UTC/local time.
- `93c0f6e` 2026-07-25 Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- `7632d9b` 2026-07-25 Add aulos-web, aulos-api, and aulos-mcp sub-projects under aries-harness.
- `0d5cb01` 2026-07-25 Initial commit: Aulos hackathon workspace with LangChain agent runtime.

## Working tree snapshot

- `M` `aulos-api/.aries_harness/ARIES_HARNESS_FINGERPRINT.json`
- `M` `aulos-api/.aries_harness/INDEX.md`
- `M` `aulos-api/.aries_harness/JOURNAL.md`
- `M` `aulos-api/.aries_harness/STATE.md`
- `M` `aulos-api/.aries_harness/TASK_STACK.md`
- `M` `aulos-api/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
- `M` `aulos-api/.aries_harness/history/DOC_TRACE.md`
- `M` `aulos-api/.aries_harness/history/README.md`
- `M` `aulos-api/.aries_harness/history/RETROSPECTIVE.md`
- `M` `aulos-api/.aries_harness/history/ROADMAP.md`
- `M` `aulos-api/.aries_harness/history/STATUS.md`
- `M` `aulos-api/.aries_harness/history/TIMELINE.md`
