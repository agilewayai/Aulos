---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "history-timeline"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:07:42Z"
generated_at: "2026-07-27T10:25:13+00:00"
effective_status: "generated"
effective_since: "2026-07-27T10:25:13+00:00"
content_fingerprint: "sha256:e0e49e8576c1087a622b6908ece915ae2b5710ef125aa479b7d0fd34cad9fd41"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-07-27T10:25:13+00:00`

## Journal milestones

### 2026-07-26T19:12:00Z

- Atelier: countable chain progress (N/M) + stage list; SSE reconnect; Retry chain for failed/interrupted jobs (pairs with API SPEC-013 delta).
- Verify: `npm run build`.

### 2026-07-26T19:15:00Z

- SPEC-007: move Guide | Atelier | Library tabs from mobile bottom bar to sticky top (under topbar) for easier reach.
- Verify: `npm run build`.

### 2026-07-26T18:55:00Z

- SPEC-008: before asset auto-reload, capture UI scene (tab, draft, guide id, library filters, scroll); restore once after reload with notice.
- Same pattern on aulos-ops (tab + user filters + scroll). Passwords never persisted.
- Verify: `node --experimental-strip-types src/sessionScene.selftest.ts`; `npm run build` web+ops.

### 2026-07-26T18:45:00Z

- Asset update: poll `/version.json`; on mismatch show “New version found — refreshing…” then auto `location.reload` (~2.2s). No manual Reload click.
- Same behavior in aulos-ops. Dismiss/session skip removed.
- Verify: `npm run build` (web + ops).

### 2026-07-26T18:40:00Z

- SPEC-007: single-pane studio — Guide | Atelier | Library as full-area tabs at all breakpoints (ui-ux-pro-max: progressive disclosure, one job per view).
- Compose dock collapses after compose/open; expandable “New guide”. Desktop no longer three-column squeeze.
- Verify: `npm run build` green.

### 2026-07-26T18:15:00Z

- SPEC-006: compose/recompose via durable jobs + event watch; resume in-progress on studio load.
- Library: search, All/Favorites/Published/In progress filters, tag filter, favorite/star, tags editor, delete, failed retry.
- Verify: `npm run build` green.

### 2026-07-26T17:55:00Z

- SPEC-005 closeout: product portal polish via ui-ux-pro-max (editorial listening studio — Fraunces/Syne/Manrope, teal + paper/stage).
- Auth split gate; sticky topbar; compose dock; Guide/Atelier/Library mobile tabs with fixed bottom nav + safe-area; More menu with outside/Escape dismiss; toast auto-dismiss.
- Compose/recompose auto-switches to Atelier then Guide when ready. Reset password minLength aligned to 10.
- Verify: `npm run build` green.

### 2026-07-26T17:45:00Z

- Recovered the complete `src/App.tsx` portal surface after a bad checkout: authentication and password recovery, streamed compose/recompose, guide publishing, library, Discogs picker, and chain-trace diagnostics.
- Restored SPEC-005 responsive studio structure: compose dock, Guide/Atelier/Library tabs, guide overflow actions, toasts, accessible password fields, and skip navigation.
- Verify: `npx tsc -b --pretty false` passed.

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
