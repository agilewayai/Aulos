---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:97fae81d140a2d949e096560d9fdbcd8b2c8bd31a7ea74e323eab9dabb4ccda5"
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

- Project root: `aulos-web/`
- Role: web GUI
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent

## Open risks

- Cross-service contract drift between web, api, mcp, and agent
- Live upstream backends unverified in Sprint-0
