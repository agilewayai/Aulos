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
generated_at: "2026-08-01T20:59:19+00:00"
effective_status: "generated"
effective_since: "2026-08-01T20:59:19+00:00"
content_fingerprint: "sha256:8aec61eddbbe8eb03e2b88e61b48e6c2ed1582ef2cc22bbadc1b01e0d99b4fe6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-08-01T20:59:19+00:00`

## Journal milestones

### 2026-08-01T16:20:00Z

- Dual-draft UI: score + hard-flaw delta; repair_log on v2; scorecard chip 硬伤 N.
- Verify: npm run build.

### 2026-08-01T16:00:00Z

- Review panel: expert perspective header; 硬伤修复指令 / 硬伤发现 (drop Sources list).
- Verify: npm run build.

### 2026-08-01T15:55:00Z

- **Travel / immersive guide reading:** GuideReader with in-app fullscreen overlay
- Verify: npm run build green.

### 2026-08-01T15:30:00Z

- **Atelier trail progress UX:** show 完成 / 跳过 / 共 breakdown; localize step status labels;
- Verify: atelierTrailUtils.test.ts ok; npm run build green.

### 2026-08-01T11:34:00Z

- REQ-011 / SPEC-021Δ: 聆乐导赏工坊审阅区 — 审阅意见 textarea；按状态显示通过发布 /
- Verify: `npm run build` green (upstream `test_diary_guides.py` 3 passed).

### 2026-08-01T19:05:00Z

- Diary guide review now uses the same Studio iframe path (`prepareGuideHtml` + `GUIDE_IFRAME_SANDBOX` + `.guide-frame`) instead of `dangerouslySetInnerHTML` into `.diary-guide-html` (which restyled Salon Codex HTML).
- Verify: `npm run build`.

### 2026-08-01T18:55:00Z

- SPEC-019: `ProcessScorecardCard` on Studio Atelier + diary 导赏工坊 when `process_scorecard` present.

### 2026-08-01T18:40:00Z

- SPEC-018: `AtelierTrail` surfaces failed `listening.review` milestones as「本意偏离已拦截」.

## Recent git commits

- `1d325d5` 2026-08-01 Ship knowledge discovery, dossier, and benchmark console; refresh fleet honeycomb.
- `491b042` 2026-07-27 Ship authority source registry, OPS knowledge console, and refresh fleet honeycomb.
- `5633e94` 2026-07-27 Ship Ops task queue, dev blog v2, and refresh fleet honeycomb.
- `c3009d2` 2026-07-27 Harden platform security, ship fleet DevOps control, and refresh harness honeycomb.
- `0c8a847` 2026-07-27 Ship Ops daily Dev Blog and web forgot-password reset.
- `6ab1ea3` 2026-07-26 Ship /discogs release and catalog-number listening guides with OPS token UI.
- `53e7437` 2026-07-26 Ship identity catalog, Hans/Hant locales, web research, and knowledge plane.
- `555cf53` 2026-07-26 Ship listening product, mandatory harness, facility layout, and UTC/local time.
- `93c0f6e` 2026-07-25 Add aulos-skills, aulos-ops, host deploy, and fleet operating defaults.
- `7632d9b` 2026-07-25 Add aulos-web, aulos-api, and aulos-mcp sub-projects under aries-harness.
- `0d5cb01` 2026-07-25 Initial commit: Aulos hackathon workspace with LangChain agent runtime.

## Working tree snapshot

- `M` `aulos-agent/.aries_harness/INDEX.md`
- `M` `aulos-agent/.aries_harness/history/DAILY_SUMMARY_INDEX.md`
- `M` `aulos-agent/.aries_harness/history/DOC_TRACE.md`
- `M` `aulos-agent/.aries_harness/history/README.md`
- `M` `aulos-agent/.aries_harness/history/RETROSPECTIVE.md`
- `M` `aulos-agent/.aries_harness/history/ROADMAP.md`
- `M` `aulos-agent/.aries_harness/history/STATUS.md`
- `M` `aulos-agent/.aries_harness/history/TIMELINE.md`
- `M` `aulos-agent/.aries_harness/history/daily/2026-07-25.md`
- `M` `aulos-agent/.aries_harness/history/daily/2026-07-26.md`
- `M` `aulos-agent/.aries_harness/history/daily/2026-07-27.md`
- `M` `aulos-agent/.aries_harness/history/daily/2026-08-01.md`
