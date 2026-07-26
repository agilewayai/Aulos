---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:f1c9013a43ade9b095db27cd993d7a83690c34fb95c84afbe2595a23d19d2479"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Design Pack

## Document Control

- Architecture ID: ARCH-001
- Title: aulos-ops portal architecture
- Status: active
- Related request: REQ-001
- Related spec: SPEC-001
- Child refs: ADR-001, STORY-001

## Design Drivers

- Primary business outcome: governed `aulos-ops` (admin and ops portal)
- Quality attributes: modularity, offline testability, clear sibling contracts

## Target shape

- `browser → App.tsx ops dashboard → api.ts → aulos-api /health + static fleet catalog`
- Dev Blog seam: `DevBlogPanel → /v1/ops/dev-blog* → collect git+harness evidence → Ops LLM (or fake) → dev_blog_posts`

## Package layout

```text
aulos-ops/
├── .aries_harness/
├── src/App.tsx, api.ts, DevBlogPanel.tsx, styles
├── public/
├── .aries_harness/scripts/
└── package.json
```

## Open decisions

- Production deploy deferred
- Cron auto-generate deferred (manual generate in this slice)
