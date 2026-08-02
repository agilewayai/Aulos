---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "request"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T21:45:00Z"
effective_status: "active"
effective_since: "2026-08-01T21:45:00Z"
content_fingerprint: "sha256:6782ec8a8152e315cb2b341e13799734304cb2a1a52d41b49665fe0ea72264a9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-006 — Desktop browse workspace density

## Intent

On a computer-sized viewport, browsing Studio / Diary / Plaza / guide review should use the full screen as a working surface. The current centered narrow column wastes space and makes interaction feel cramped.

## Outcome

Desktop (≥1100px) layouts fill the viewport: tall guide frames, sticky list/rails, multi-column feeds. Continuous prose stays ~72ch for readability; chrome and shelves expand to the edges.

## Non-goals

- Redesigning published guide HTML
- Changing mobile (<1100px) interaction patterns
- New product surfaces

## Acceptance

- Desktop studio guide pane fills remaining viewport height
- Diary list + detail and guide-review reader + rail use split workspace
- Plaza / blog feeds use multi-column grids on wide screens
- `npm run build` green; mobile breakpoints unchanged
