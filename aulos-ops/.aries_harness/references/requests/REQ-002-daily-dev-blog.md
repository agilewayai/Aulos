---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-26T16:20:00Z"
effective_status: "active"
effective_since: "2026-07-26T16:20:00Z"
content_fingerprint: "sha256:a0895af0865bea6e4b6afdb1cb47673d2d4dc6cf61ad4b23143164e07cc6c48d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Request Brief

## Document Control

- Request ID: REQ-002
- Artifact type: request
- Objective mode: functional_capability
- Title: Daily product development blog in Ops
- Status: active
- Owner: ubuntu
- Review date: 2026-07-26
- Child refs: SPEC-002, STORY-PACK-002, ARCH-001

## Belongs Here

- Request source: operator ask for a blog-style daily summary of git + harness work
- Problem statement: raw git history and harness daily files are engineer-facing; operators need a plain-language product narrative
- Why now: fleet already journals and refreshes history; product storytelling is missing in Ops
- Intended outcome: one monorepo blog post per UTC day, readable as product features / user stories / architecture stories
- Scope boundary: Ops UI + API generate/list/read; evidence from whole `aulos` monorepo
- Constraints: use Ops-configured LLM; fake provider must still produce a readable draft offline; Simplified Chinese
- Non-goals: public community blog distill; per-subproject tabs; cron auto-publish; replacing harness `history/daily`

## Delivery Links

- Spec package: SPEC-002
- Story-slice pack: STORY-PACK-002
- Architecture design pack: ARCH-001 (seam patch)
