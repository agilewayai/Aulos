---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "history-timeline"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:06Z"
generated_at: "2026-07-26T16:28:21+00:00"
effective_status: "generated"
effective_since: "2026-07-26T16:28:21+00:00"
content_fingerprint: "sha256:b20590a6f5fda8fbdac66945da0530452408dd8811b1475d7a9e0676c4c25c79"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-26T16:28:21+00:00`

## Journal milestones

### 2026-07-26T16:30:00Z

- SPEC-002 / STORY-PACK-002: Ops **Dev Blog** tab — list/read/generate monorepo daily product blog
- Evidence from git + harness; LLM via Ops providers (fake offline draft); three Chinese sections
- Verify: `aulos-api` `pytest tests/test_dev_blog.py` 5 passed; `npm run build` green

### 2026-07-25T17:34:00Z

- SPEC-010: OPS Knowledge audit UI opened — Browse/proofread, Sources, Jobs & crawl, Retrieve lab
- Knowledge APIs: document detail+body, publish restore, composers list, document filters
- systemd `aulos-knowledge.service` on PG; API `AULOS_KNOWLEDGE_BASE_URL`; ops rebuilt to :5092 / aulos-ops.purezen.ai

### 2026-07-25T17:22:35Z

- STORY-PACK-007 S4: Knowledge tab plane up/down badge + empty-state when plane unreachable

### 2026-07-25T17:00:00Z

- Added ``src/time.ts``; users/deliveries/health refresh use OS-local timestamps

### 2026-07-25T11:20:06Z

- initialized `.aries_harness/`
- wrote `ARIES_HARNESS_FINGERPRINT.json`
- no execution history recorded yet

## Recent git commits

- `6ab1ea3` 2026-07-26 Ship /discogs release and catalog-number listening guides with OPS token UI.
- `53e7437` 2026-07-26 Ship identity catalog, Hans/Hant locales, web research, and knowledge plane.
- `555cf53` 2026-07-26 Ship listening product, mandatory harness, facility layout, and UTC/local time.
- `93c0f6e` 2026-07-25 Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- `7632d9b` 2026-07-25 Add aulos-web, aulos-api, and aulos-mcp sub-projects under aries-harness.
- `0d5cb01` 2026-07-25 Initial commit: Aulos hackathon workspace with LangChain agent runtime.

## Working tree snapshot

- `M` `aulos-api/.aries_harness/ARIES_HARNESS_FINGERPRINT.json`
- `M` `aulos-api/.aries_harness/EVAL.md`
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
