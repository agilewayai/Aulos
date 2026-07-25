---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "history-timeline"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:05Z"
generated_at: "2026-07-25T19:31:11+00:00"
effective_status: "generated"
effective_since: "2026-07-25T19:31:11+00:00"
content_fingerprint: "sha256:f89aa4acad610a1493d6b63c548cb5ce5d395e5ecbe4bd4b8072127ece813b7d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-25T19:31:11+00:00`

## Journal milestones

### 2026-07-25T18:50:00Z

- Fixed Unknown composer: Chinese 《》 title parse + catalog soft aliases (CJK len≥2); added Dvořák Dumky catalog shelf
- Chinese locales: **简体 (zh-Hans)** + **繁体 (zh-Hant)** — script tags only
- Guide switcher: 简体 | 繁体 | English

### 2026-07-25T18:35:00Z

- External skill intake: **Agent Reach** (`Panniantong/Agent-Reach` @ `b4d52c46…`)
- Security audit → conditional allow as **search enabler only**
- Installed `skills/enabler-agent-reach/` (policy fence; social/cookie/CLI-install denied)
- Wired Jina deepen into `aulos-api` web_search / web-research + OPS toggle
- Verified: registry discovers enabler; web_research tests pass

### 2026-07-26T01:15:00Z

- Work Identity Catalog productized (REQ-006 / SPEC-008 / DOM-002 / ADR-004)
- Catalog schema + 5 works (Bach Goldberg/Cello, Beethoven duo, Chopin/Mahler slots)
- IdentityResolver wired into intake/scrub/ambient; RAG seeds catalog cards
- Removed work-name elif trees; identity authority is catalog YAML

### 2026-07-26T00:55:00Z

- Deep identity audit + fix: Bach cello suites pollution (Goldberg / Beethoven duo)
- Added `solo-cello-suites` family; hardened intake, scrub, ambient conflict gates
- SPEC-006 identity rules updated; hard-fail tests for cello suites + ambient

### 2026-07-25T17:15:00Z

- operating-defaults 0.4.0: product capabilities via Agent + Skill Harness; ADR-002 consequences updated

### 2026-07-25T17:00:00Z

- Timezone constraint promoted: store UTC / display OS local (operating-defaults 0.3.3)

### 2026-07-25T16:50:00Z

- Self-evolution closeout: process + facility + canonical source
- Memo: `docs/evolution-cycle-2026-07-25-harness-process-facility.md`
- Insights promoted; STATE/TASK_STACK updated for day organize + history-refresh
- Canonical library confirmed: `agilewayai/aries-harness-skills` (not studio)

### 2026-07-25T16:40:00Z

- Relocated harness **facility** assets into `.aries_harness/` across the fleet
- Was: project-root `scripts/aries-harness/` + `templates/aries_harness/`
- Now: `.aries_harness/scripts/` + `.aries_harness/templates/`
- Updated init/router usage strings, READMEs, operating-defaults 0.3.1, service-bootstrap
- Smoke: history-status / memory-inspect / well-organized OK from new paths

## Recent git commits

- `53e7437` 2026-07-26 Ship identity catalog, Hans/Hant locales, web research, and knowledge plane.
- `555cf53` 2026-07-26 Ship listening product, mandatory harness, facility layout, and UTC/local time.
- `93c0f6e` 2026-07-25 Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- `7632d9b` 2026-07-25 Add aulos-web, aulos-api, and aulos-mcp sub-projects under aries-harness.
- `0d5cb01` 2026-07-25 Initial commit: Aulos hackathon workspace with LangChain agent runtime.

## Working tree snapshot

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
- `M` `aulos-api/.aries_harness/history/daily/2026-07-25.md`
