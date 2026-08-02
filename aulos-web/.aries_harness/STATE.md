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
content_fingerprint: "sha256:6c55852c0b6f48454144a28f47ffebdd6cc5dd9ff5ea1bd074bdb7ff5d3854cc"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- REQ-006 / SPEC-010 desktop workspace density deployed to production
  (`20260802071831-5476efb`); browser visual smoke not run
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
- Desktop ≥1100px: full-bleed shell, tall guide frames, sticky diary/review rails, multi-column feeds (SPEC-010)
- Product surfaces: plaza (magazine feed) / diary (blog + calendar + tag cloud) / studio
- Listening diary list API returns snapshot for client tag aggregation

## Open risks

- Live Mailgun required for real reset emails (fake mode offline-ok)
- Discogs rate limits without OPS token
- Desktop density CSS deployed; browser-level responsive visual smoke remains
  pending
