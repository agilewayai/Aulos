---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "journal"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:43Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:43Z"
content_fingerprint: "sha256:a66ebaa468bde16b97fbebd2963814cf3b855e11591d23b45fa280dd6991144f"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

## 2026-07-26T16:50:00Z

- SPEC-002: `POST /v1/auth/forgot-password` + `POST /v1/auth/reset-password`; Mailgun `reset_password` mail
- Anti-enumeration; one-time `EmailToken` purpose=`reset_password`
- Verify: `pytest tests/test_auth.py` 7 passed

## 2026-07-26T16:30:00Z

- SPEC-009: `/v1/ops/dev-blog` list/get/generate; `dev_blog_posts` table; `services/dev_blog.py`
- Collect UTC-day git + harness excerpts; Ops LLM or fake template with product narrative headings
- Verify: `pytest tests/test_dev_blog.py` 5 passed offline

## 2026-07-25T19:50:00Z

- REVIEW-008 smoke `423-287-1`: was truncating to release 423; now catno search → Mozart/Horowitz
- Fixes: parse catno, Discogs search, exclude composer from performers, workish titles
- Verify: `test_discogs.py` 6 passed; live `resolve_discogs_message("/discogs #423-287-1")` SMOKE_OK

## 2026-07-25T19:40:00Z

- Root cause of “no Discogs token UI”: local-only; live OPS/API not redeployed
- Deployed host: OPS nav **Discogs** tab + `/v1/ops/discogs` (401 without auth = route live)

## 2026-07-25T19:35:00Z

- OPS GUI: dedicated **Integrations** tab for Discogs token (status + enable + save/clear); Overview link

## 2026-07-25T19:30:00Z

- OPS office: `/v1/ops/discogs` + LLM tab form to store Discogs personal user token (overrides env)

## 2026-07-25T19:20:00Z

- Renamed slash command `/discog` → `/discogs` (parser only accepts `/discogs`)

## 2026-07-25T19:15:00Z

- STORY-PACK-008 `/discogs`: REQ/SPEC/STORY/CKPT authored; id = Discogs **release** (master fallback)
- Implemented `services/discogs.py` + `parse_discogs_command`; wired `_run_chain_core` seed vinyl/interpretations
- Studio hint for `/discogs #release-id`; tests: `test_discogs.py` 4 passed; listening-guide regression green

## 2026-07-25T18:25:45Z

- Web research loop: thin RAG → Wikipedia/DDG (+ optional Brave) → LLM verify → KB upsert (user + global)
- Ops `/v1/ops/web-research` + LLM tab controls; query variants for opus-specific titles
- Verified: `tests/test_web_research.py` 5 passed; live Dvořák Dumky `rag_mode=no_match+web-research`, persisted docs 12/13, next search 6 hits

## 2026-07-25T17:22:35Z

- STORY-PACK-007 S2: `_rag_context` resolves Catalog work_id for knowledge-plane retrieve
- Client-side drop of mismatched `aulos_work_id` hits; `tests/test_knowledge_plane_rag.py` green

## 2026-07-26T01:15:00Z

- RAG aligned to Work Identity Catalog (REQ-006): seed identity cards; weak tokens from policy
- works_compatible respects work_id; identity_only cards never replace full dossiers

## 2026-07-26T00:55:00Z

- RAG identity gate: `bwv`/form words are weak tokens; soft-filter requires distinctive overlap
- Retrieve must not attach Goldberg `kb_dossier` to Bach cello suites / 大提琴无伴奏组曲
- SPEC-006 identity hard-gate + regression tests

## 2026-07-25T17:15:00Z

- Listening gateway delegates to AgentProxy.run_listening (no local iter_listening_chain)

## 2026-07-25T17:00:00Z

- Added ``aulos_api.timefmt.to_utc_iso``; listening/ops/mailgun wire UTC ``Z``; tests/test_timefmt.py

## 2026-07-25T14:53:12Z

- Research KB + vector RAG: knowledge_documents/chunks, embeddings ops settings, lexical fallback, corpus seed
- Recompose/update-publish APIs; by-share ownership; studio + /g owner toolbar
- SPEC-006; listening tests for KB search + recompose slug stability


## 2026-07-25T11:52:22Z

- STORY-002..005 auth MVP: users/roles, register/verify/login, Mailgun config (fakeable), superadmin ops gate
- SQLite + JWT + bcrypt; bootstrap superadmin via env
- aulos-web register/login/verify UI; aulos-ops superadmin + Mailgun settings
- pytest auth suite green; public smoke on aulos.purezen.ai / aulos-ops.purezen.ai


## 2026-07-25T11:07:43Z

- initialized `.aries_harness/`
- wrote `ARIES_HARNESS_FINGERPRINT.json`
- no execution history recorded yet

## 2026-07-25T12:21:57Z

- Added ops-managed LLM providers (DeepSeek + Grok) with GET/PUT/test; chat uses live provider when ready.
- Verified: pytest 20 passed; ops UI LLM tab deployed.

## 2026-07-25T12:55:17Z

- Shipped listening-guide MVP (REQ-003/SPEC-003): width+depth research workflow, HTML guide, observable steps, web studio UI.
- Verified: pytest 22 passed; Goldberg smoke guide created; aulos-web redeployed.

## 2026-07-25T13:23:08Z

- Longrun 1–4 done: SkillRuntime drives listening guides; skill_versions persisted; MCP skills.list/run; ops Skills tab; web shows skill ids.
- Verified: skills 5 / api 22 pytest; live Goldberg probe score=10; guide steps cite aulos-listening-*.

## 2026-07-25T13:34:45Z

- Closed residual 1–4: ops Disable now skips skill steps at runtime; SSE `/v1/listening-guides/stream`; web live chain; serve.py streams event-stream.
- Verified: skills 7 / api 24 pytest; SSE smoke on :5090 and proxy :5091.
