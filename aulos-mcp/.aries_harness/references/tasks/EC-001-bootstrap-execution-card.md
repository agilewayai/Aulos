---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "task-breakdown"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:e725c3f3cf0c35769ed74ca500026a8e8bb9d613b44d332c650d6e072ae15718"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Aries Harness Execution Card

## Artifact header

- Artifact ID: EC-001
- Artifact type: execution-card
- Status: active
- Owner: ubuntu
- Canonical path: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- Upstream links: STORY-001, ARCH-001
- Verification state: in_progress
- Last reviewed: 2026-07-25

## Runtime links

- Run ID: RUN-BOOTSTRAP-001
- Task ID / Slice ID: STORY-001

## Before Starting

- Target: initialize `aulos-mcp` with aries-harness + starter architecture
- Scope: harness artifacts + starter app + offline verify
- Done condition: verify green; architecture docs linked; harness mission/state updated

## During Execution

- Current phase: Verify / Summarize
- Current risks: cross-service contract drift

## Before Closing

- What changed: harness init; REQ/SPEC/STORY/ARCH/ADR; starter app
- What remains unverified: live multi-service path
