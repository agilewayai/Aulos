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
content_fingerprint: "sha256:9f3a861e47b6bb7c8bd1a4a358bcdddae410468d45f12cc4ab4b305615d6c504"
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
2. Operator can list cached posts by UTC calendar day and open one post.
3. Operator can generate (or force-regenerate) a post for a chosen day.
4. Generated body is Simplified Chinese markdown with exactly these section headings:
   - `## 今天产品多了什么`
   - `## 谁因此更好用了`
   - `## 系统怎么搭起来的`
5. Voice is product-facing plain language; no unexplained internal jargon or file-path walls.
6. Evidence comes from monorepo git commits that day plus harness JOURNAL / history daily / changed REQ|SPEC|STORY paths.
7. Posts persist via API; reopening a day does not re-call LLM unless `force=true`.
8. When Ops LLM is `fake` or not live-ready, generate still succeeds with a deterministic template draft and `provider=fake`.
9. Timestamps on the wire are UTC (`Z`); UI displays via `src/time.ts` OS/browser local time.

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
