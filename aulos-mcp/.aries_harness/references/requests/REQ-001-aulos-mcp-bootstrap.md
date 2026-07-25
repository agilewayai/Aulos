---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:d0a173e866973affa70b09bd76327112f8686e7e38df3e13414a3b2306e91a3c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Request Brief

## Semantic Role

- This artifact owns why the work matters, for whom it matters, and the boundary around the ask.

## Document Control

- Request ID: REQ-001
- Artifact type: request
- Objective mode: functional_capability
- Title: Bootstrap aulos-mcp as the Aulos MCP integration surface
- Status: active
- Owner: ubuntu
- Review date: 2026-07-25
- Parent refs: n/a
- Child refs: SPEC-001, STORY-001, ARCH-001
- Source of truth: `.aries_harness/references/requests/REQ-001-aulos-mcp-bootstrap.md`

## Belongs Here

- Request source: operator ask to apply aries-harness and init `aulos-mcp`
- Problem statement: agents and MCP hosts need a governed tool surface to integrate with Aulos
- Why now: hackathon multi-service bootstrap; harness and seams must exist before feature work
- Intended user or operator outcome: a runnable, testable `aulos-mcp` skeleton that another operator can extend
- Business value: clearer separation of GUI / gateway / MCP / agent concerns
- Success signals: `.aries_harness/` initialized; starter app present; offline verify path; linked mission/architecture/stories
- Scope boundary: `aulos-mcp/` only for this request; contracts with siblings are documented but not fully productized
- Constraints: aries-harness governed artifacts; keep Sprint-0 offline-verifiable
- Non-goals: OAuth MCP hosts, remote SSE productization, irreversible external tools without approval

## Delivery Links

- Spec package: SPEC-001
- Story-slice pack: STORY-PACK-001
- Architecture design pack: ARCH-001
- Value traceability matrix: TRACE-001

## Refresh Triggers

- What should force this brief to be reviewed: change of product role for `aulos-mcp` or merge into another service
