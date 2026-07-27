---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-26T16:20:00Z"
effective_status: "active"
effective_since: "2026-07-26T16:20:00Z"
content_fingerprint: "sha256:e011b9aa62f299034044f197a12acb5108a181fade805f1ee220da11eb60eb5d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Spec Package

## Document Control

- Spec ID: SPEC-002
- Title: Daily product development blog (Ops)
- Status: active
- Related request: REQ-002
- Child refs: STORY-PACK-002, ARCH-001
- Upstream API: aulos-api `/v1/ops/dev-blog*`

## Behaviors

1. Ops shows a **Dev Blog** tab for superadmin operators.
2. Operator can list cached posts (newest first) and open one by **post id**.
3. Operator can **generate on demand** for any evidence UTC day — creates a **new** post each time (zero or many per day allowed).
4. **Regenerate selected** rewrites the current post in place (`force` + `post_id`).
5. List supports filters: exact `day`, `day_from`/`day_to` range, keyword `q` (title + body).
6. Generated body follows **SPEC-017** internal writing contract (factual dev trace; three section headings):
   - `## 今天产品多了什么`
   - `## 谁因此更好用了`
   - `## 系统怎么搭起来的`
7. Voice: engineer-to-colleague summary; no hype, emotion, or external marketing tone.
8. Evidence comes from monorepo git commits that day plus harness JOURNAL / history daily / changed REQ|SPEC|STORY paths.
9. When Ops LLM is `fake` or not live-ready, generate still succeeds with a deterministic factual draft and `provider=fake`.
10. Timestamps on the wire are UTC (`Z`); UI displays via `src/time.ts` OS/browser local time.

## Acceptance heuristics

- `GET /v1/ops/dev-blog` and `GET /v1/ops/dev-blog/{day}` work authenticated
- `POST /v1/ops/dev-blog/{day}/generate` returns body with the three headings
- Offline pytest covers evidence collect + fake generate + list/get/force
- Ops `npm run build` succeeds with Dev Blog tab wired

## Non-goals

- Public community blog posts
- Per-project blog columns
- Scheduled cron generation
- Editing posts in the UI (regenerate only)
