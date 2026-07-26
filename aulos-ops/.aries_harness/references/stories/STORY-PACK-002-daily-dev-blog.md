---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "story-pack"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-26T16:20:00Z"
effective_status: "active"
effective_since: "2026-07-26T16:20:00Z"
content_fingerprint: "sha256:8c36c8363f10f0b9b09613db1ae5f1d664a2ded38efdc60277aed2be035b47bd"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Story Pack

## Document Control

- Story Pack ID: STORY-PACK-002
- Title: Daily product development blog
- Status: active
- Related spec: SPEC-002

## Stories

### STORY-002a — List and read

- Goal: operator opens Dev Blog, sees days with posts, reads one article
- Acceptance: list + detail API wired; markdown sections visible; local timestamps

### STORY-002b — Generate

- Goal: operator generates today’s (or a chosen day’s) product blog from git + harness evidence
- Acceptance: generate button works; fake LLM yields draft; force regenerates; evidence summary visible

### STORY-002c — Evidence trail

- Goal: operator can see which commits and harness files grounded the post
- Acceptance: detail payload includes evidence summary (commits + source paths)
