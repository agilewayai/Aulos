---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "history-timeline"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T17:25:00+00:00"
generated_at: "2026-07-27T10:25:25+00:00"
effective_status: "generated"
effective_since: "2026-07-27T10:25:25+00:00"
content_fingerprint: "sha256:0d87f9f969caabff8e7a52f9fba0dee9a219f5928ab904aa3e707dda9f8e3ed8"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-27T10:25:25+00:00`

## Journal milestones

### 2026-07-25T17:42:00Z

- Media durability: artifacts root → `data/persist/artifacts` (json + media/image|audio|meta)
- Wikidata P18 portraits + Commons PD audio; MusicBrainz recording/release meta + Cover Art images
- media_assets table + OPS media list; backup packs media blobs; Bach sample: 3 images + 2 meta on disk

### 2026-07-25T17:38:00Z

- Docker durability: switched PG/Redis from named volumes → host bind mounts under `data/persist/`
- Redis AOF+RDB dual persistence; postgres `stop_grace_period=60s`; backup + persist_smoke scripts
- Verified: force-recreate and `compose down`/`up` keep composers=10 docs=55

### 2026-07-25T17:30:00Z

- Installed Docker Engine from Docker Inc. official apt (not snap)
- Hardened compose: digest-pinned pgvector/pgvector + redis, localhost bind, cap_drop
- PG up healthy; crawl bootstrap: 10 composers, 55 published docs, 31/31 jobs succeeded
- Entry points: Bach/Mozart/Beethoven/Chopin/Schubert/Brahms/Tchaikovsky/Mahler/Debussy/Stravinsky
- QIDs verified via enwiki sitelinks (Chopin Q1268, Debussy Q4700, Brahms Q7294, Mahler Q7304)

### 2026-07-25T17:22:35Z

- STORY-PACK-007 longrun closeout (S0–S5): CKPT-007 complete, VR-007 + SUM-007
- S1: Postgres path docs + `deploy/pg_smoke.sh` (SKIP no docker); SQLite tests green
- S2: Catalog `work_id` passed into knowledge retrieve from `_rag_context`; bleed tests hard-fail
- S3: `docs/worker.md`; disabled enqueue 400; failed job status+error tests
- S4: OPS Knowledge plane badge + empty-state when unreachable
- Verify: aulos-knowledge pytest 8 passed; API knowledge_plane_rag 1 passed

### 2026-07-26T01:20:00Z

- Scaffolded aulos-knowledge professional plane (REQ-007 / ARCH-005 / ADR-005/006)
- Sources allowlist + catalog/wikidata/musicbrainz connectors + artifact provenance
- OPS Knowledge tab + aulos-api `/v1/ops/knowledge/plane/*` proxy
- RAG cutover behind `AULOS_KNOWLEDGE_PLANE_ENABLED` (default off)

## Recent git commits

- `c3009d2` 2026-07-27 Harden platform security, ship fleet DevOps control, and refresh harness honeycomb.
- `0c8a847` 2026-07-27 Ship Ops daily Dev Blog and web forgot-password reset.
- `6ab1ea3` 2026-07-26 Ship /discogs release and catalog-number listening guides with OPS token UI.
- `53e7437` 2026-07-26 Ship identity catalog, Hans/Hant locales, web research, and knowledge plane.
- `555cf53` 2026-07-26 Ship listening product, mandatory harness, facility layout, and UTC/local time.
- `93c0f6e` 2026-07-25 Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- `7632d9b` 2026-07-25 Add aulos-web, aulos-api, and aulos-mcp sub-projects under aries-harness.
- `0d5cb01` 2026-07-25 Initial commit: Aulos hackathon workspace with LangChain agent runtime.

## Working tree snapshot

- `M` `AGENTS.md`
- `M` `CLAUDE.md`
- `M` `aulos-api/.aries_harness/INDEX.md`
- `M` `aulos-api/.aries_harness/JOURNAL.md`
- `M` `aulos-api/.aries_harness/STATE.md`
- `M` `aulos-api/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
- `M` `aulos-api/.aries_harness/history/DOC_TRACE.md`
- `M` `aulos-api/.aries_harness/history/README.md`
- `M` `aulos-api/.aries_harness/history/RETROSPECTIVE.md`
- `M` `aulos-api/.aries_harness/history/ROADMAP.md`
- `M` `aulos-api/.aries_harness/history/STATUS.md`
- `M` `aulos-api/.aries_harness/history/TIMELINE.md`
