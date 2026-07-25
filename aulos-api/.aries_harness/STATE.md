---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:958bf67dd82818b94db915da602cbfc079962a81d85ee391e7718e957c8ac683"
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

- Project root: `aulos-api/`
- Role: API gateway
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent

## Open risks

- Cross-service contract drift between web, api, mcp, and agent
- Live upstream backends unverified in Sprint-0
