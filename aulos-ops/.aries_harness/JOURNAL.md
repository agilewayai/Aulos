---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "journal"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:06Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:06Z"
content_fingerprint: "sha256:77e1a15360404f241fb1ce1a0fd1e2233413c9ea6f60bca086944d87efd5701c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

## 2026-08-01T21:00:00Z

- **SPEC-031:** Guide quality — Promote to production after staging; copy states
  system pipeline, not case patch.

## 2026-08-01T20:40:00Z

- **SPEC-030:** Guide quality panel shows promote candidate + Stage craft (staging
  only); scorecard table adds Asset / Promote columns.

## 2026-08-01T17:35:00Z

- **Ambient fallback UI:** LLM/Listening settings radio for official Embed vs server
  stream extract (`listening.ambient_fallback_mode`); API helpers in `api.ts`.


## 2026-08-01T17:05:00Z

- **REQ-010 Δ Composer dossier UI:** works panel tabs 题材 / 时间线 / 树; shows year, catalog,
  genre badges + soft-cap hint. Types: `works_by_year` / `works_by_genre`.

## 2026-08-01T18:55:00Z

- SPEC-019: Ops tab **Guide quality** (`GuideQualityPanel`) — multi-guide rollup table + node dim expand via trace.

## 2026-08-01T18:40:00Z

- SPEC-018: LLM settings tab hosts `listening.review_llm` Intent Critic switch (saved with LLM form).

## 2026-08-01T06:35:00Z

- **Knowledge console ship closeout:** Explore / Benchmark / Diagnose-improve / Performance report /
  Composer dossier modules + Ops dashboard shell/sidebar layout; Honeycomb before git push.

## 2026-07-27T16:55:00Z

- Knowledge **Composer dossier** module: picker + 构建履历与作品 + timeline/works tree (REQ-010).

## 2026-07-26T16:45:00Z

- UX: `PasswordField` Show/Hide on login password + all API key / token fields

## 2026-07-26T16:30:00Z

- SPEC-002 / STORY-PACK-002: Ops **Dev Blog** tab — list/read/generate monorepo daily product blog
- Evidence from git + harness; LLM via Ops providers (fake offline draft); three Chinese sections
- Verify: `aulos-api` `pytest tests/test_dev_blog.py` 5 passed; `npm run build` green

## 2026-07-25T17:34:00Z

- SPEC-010: OPS Knowledge audit UI opened — Browse/proofread, Sources, Jobs & crawl, Retrieve lab
- Knowledge APIs: document detail+body, publish restore, composers list, document filters
- systemd `aulos-knowledge.service` on PG; API `AULOS_KNOWLEDGE_BASE_URL`; ops rebuilt to :5092 / aulos-ops.purezen.ai

## 2026-07-25T17:22:35Z

- STORY-PACK-007 S4: Knowledge tab plane up/down badge + empty-state when plane unreachable

## 2026-07-25T17:00:00Z

- Added ``src/time.ts``; users/deliveries/health refresh use OS-local timestamps

## 2026-07-25T11:20:06Z

- initialized `.aries_harness/`
- wrote `ARIES_HARNESS_FINGERPRINT.json`
- no execution history recorded yet
