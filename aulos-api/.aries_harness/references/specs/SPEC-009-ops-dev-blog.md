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
content_fingerprint: "sha256:408b3bdcd4401517fd28138421e727dbbcf660644f5e3138c941d15892187125"
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

1. Persist posts in `dev_blog_posts` (`day` unique UTC `YYYY-MM-DD`).
2. Endpoints (superadmin):
   - `GET /v1/ops/dev-blog` — list summaries
   - `GET /v1/ops/dev-blog/{day}` — full post + evidence
   - `POST /v1/ops/dev-blog/{day}/generate` — body `{ "force": bool }`; collect evidence, LLM or fake template, upsert
3. Repo root via `AULOS_REPO_ROOT` or auto-detect monorepo parent of `aulos-api`.
4. Evidence: git log for that UTC day + harness JOURNAL / history daily / changed REQ|SPEC|STORY paths under `aulos-*`.
5. System prompt requires Simplified Chinese and the three product section headings.
6. Fake / non-live LLM path returns deterministic draft containing the three headings.
7. `generated_at` serialized with `to_utc_iso`.

## Acceptance

- `pytest tests/test_dev_blog.py` offline green
- Generate without live keys succeeds (`provider=fake`)
