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
content_fingerprint: "sha256:f0af833313e67510037ee58f5da3bfb0c3f13ec0c205e1b8133ea78632baf826"
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
- Intended outcome: on-demand **internal dev-trace** posts from monorepo evidence (see SPEC-017); not public marketing
- Scope boundary: Ops UI + API generate/list/read; evidence from whole `aulos` monorepo
- Constraints: use Ops-configured LLM; fake provider must still produce a readable draft offline; Simplified Chinese; **factual voice per SPEC-017**
- Non-goals: public community blog distill; per-subproject tabs; cron auto-publish; replacing harness `history/daily`

## Delivery Links

- Spec package: SPEC-002
- Story-slice pack: STORY-PACK-002
- Architecture design pack: ARCH-001 (seam patch)
