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
content_fingerprint: "sha256:de88bb9190a6bf5e1208534b11ffe8bd67164b5880ce4f645800a344e9e9fbd3"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- REQ-011 / SPEC-021Δ diary guide review lifecycle UI shipped locally
- SPEC-009 我的聆乐博客式改版（日历 + Tag 云）已部署 production
- Plaza editorial feed + diary/plaza responsive UX 已上线

## Active run

- idle


## Hot facts

- Project root: `aulos-web/`
- Role: web GUI
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent
- Auth: register / verify / login + forgot / reset (SPEC-002)
- Studio: **+** → Discogs search → compose via `/discogs #id`
- UX: auth gate + studio tabs + compose dock (SPEC-005)
- Product surfaces: plaza (magazine feed) / diary (blog + calendar + tag cloud) / studio
- Listening diary list API returns snapshot for client tag aggregation

## Open risks

- Live Mailgun required for real reset emails (fake mode offline-ok)
- Discogs rate limits without OPS token
