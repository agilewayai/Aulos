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
generated_at: "2026-08-02T10:06:49+00:00"
effective_status: "generated"
effective_since: "2026-08-02T10:06:49+00:00"
content_fingerprint: "sha256:c4fc271cc28eee78193011ae207bf00e5745b1bce5df21a1f23cde42f0f8e542"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Timeline

Generated at: `2026-08-02T10:06:49+00:00`

## Journal milestones

### 2026-08-02T10:02:45Z

- Deployed gateway Slice H production code with `bash deploy/aulos-ctl.sh
- Post-deploy `smoke` and `status` stayed green: `aulos-api`, `aulos-web`,
- Production PostgreSQL guide #60 trace confirms gateway `g.program` budget work

### 2026-08-02T10:15:00Z

- **Review Critics → AI Code Mirror (Codex):** agent `_ops_llm_complete(role=review)`

### 2026-08-02T09:50:00Z

- **LLM provider: AI Code Mirror (Codex Responses relay):** Ops slot

### 2026-08-02T09:44:23Z

- SPEC-034 Slice H gateway fix implemented from production PostgreSQL guide #60
- API fix: `web.research` program-deepen config now defaults to fast/budgeted
- Ready multi-work fast mode skips album-level `g.llm`; full deepen remains
- Tests: `tests/test_web_research_partial.py` green (4 passed).

### 2026-08-02T07:24:00Z

- **Production deploy sync:** root `bash deploy/aulos-ctl.sh deploy` published
- Verify: root `doctor` passed; deploy test suite -> 5 passed; root `status`
- Central deploy evidence:

### 2026-08-02T06:21:15Z

- **SPEC-034 Slice F consumer / guide #59:** hot Postgres latest guide remained
- Fix: Discogs core parsing now prefers explicit performer-role names over
- Verify: `PYTHONPATH=. .venv/bin/pytest -q tests/test_discogs.py` -> 12 passed;

### 2026-08-01T23:10:00Z

- **META-001 v9 consumer (guide #57):** gateway program loop uses

### 2026-08-01T22:55:00Z

- **SPEC-034Δ program deepen loop (gateway):** after `g.rag`, multi-work
- Verify: `test_web_research_partial` + `test_listening_plan` green.

## Recent git commits

- `9606691` 2026-08-02 Ship Discogs structure-first guide sheets
- `5476efb` 2026-08-02 Ship identity freeze (SPEC-032) and listening hardenings across the fleet; refresh honeycomb.
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

## Working tree snapshot

- `M` `aulos-agent/.aries_harness/INDEX.md`
- `M` `aulos-agent/.aries_harness/JOURNAL.md`
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
