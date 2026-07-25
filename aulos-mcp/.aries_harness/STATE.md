---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:9ed705b843cc7602c0e0b0efc5886d8a4c015b8383f9f9cb4222dc0ef54bcb65"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- Bootstrap STORY-001 in progress / ready for verify

## Active run

- RUN-BOOTSTRAP-001

## Hot facts

- Project root: `aulos-mcp/`
- Role: MCP agents integration
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent

## Open risks

- Cross-service contract drift between web, api, mcp, and agent
- Live upstream backends unverified in Sprint-0
