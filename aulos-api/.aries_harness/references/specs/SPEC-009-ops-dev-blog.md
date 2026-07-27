---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-26T16:20:00Z"
effective_status: "active"
effective_since: "2026-07-26T16:20:00Z"
content_fingerprint: "sha256:5274f650b805dd4585e93e5c3c823624960bc1f07646e27a18e04c35be044ba9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Spec Package

## Document Control

- Spec ID: SPEC-009
- Title: Ops daily product development blog API
- Status: active
- Related request: aulos-ops REQ-002
- Downstream UI: aulos-ops SPEC-002

## Behaviors

1. Persist posts in `dev_blog_posts` (`day` = evidence UTC `YYYY-MM-DD`; **multiple posts per day allowed**).
2. Endpoints (superadmin):
   - `GET /v1/ops/dev-blog` — list summaries; query `day`, `day_from`, `day_to`, `q`, `limit`
   - `GET /v1/ops/dev-blog/posts/{id}` — full post + evidence
   - `GET /v1/ops/dev-blog/{day}` — latest post for evidence day (compat)
   - `POST /v1/ops/dev-blog/{day}/generate` — `{ "force", "post_id" }`; default **always creates new**; `force`+`post_id` rewrites that row
   - `POST /v1/ops/dev-blog/generate` — body `{ "day", "force", "post_id" }`
3. Repo root via `AULOS_REPO_ROOT` or auto-detect monorepo parent of `aulos-api`.
4. Evidence: git log for that UTC day + harness JOURNAL / history daily / changed REQ|SPEC|STORY paths under `aulos-*`.
5. Writing contract **SPEC-017** (`dev_blog_contract.py`): internal dev trace; evidence-only; no hype; system prompt + soft lint.
6. Fake / non-live LLM path returns deterministic factual draft containing the three headings.
7. `generated_at` serialized with `to_utc_iso`.

## Acceptance

- `pytest tests/test_dev_blog.py` offline green
- Generate without live keys succeeds (`provider=fake`)
