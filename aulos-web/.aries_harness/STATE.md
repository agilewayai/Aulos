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
content_fingerprint: "sha256:d43f94ccb325978c54d11bc0117c67e3c021d2c0b1bd4f7318f77e41c14e8595"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- SPEC-002 forgot/reset password shipped

## Active run

- RUN-PASSWORD-RESET-001

## Hot facts

- Project root: `aulos-web/`
- Role: web GUI
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent
- Auth: register / verify / login + forgot / reset (SPEC-002)

## Open risks

- Live Mailgun required for real reset emails (fake mode offline-ok)
- Host redeploy needed for live web/api
