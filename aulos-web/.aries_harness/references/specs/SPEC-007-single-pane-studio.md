---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T18:35:00Z"
effective_status: "active"
effective_since: "2026-07-26T18:35:00Z"
content_fingerprint: "sha256:a0f6936df8ffe5ade9fbb8d733c83a3eb2b3ba132e1a39e166a2035481a7ac4a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-007 — Single-pane studio workspace

Upstream: SPEC-005 + ui-ux-pro-max (navigation / progressive disclosure).

## Outcome

Studio is one product surface: Guide | Atelier | Library switch as full-area panes.
No three-column squeeze on desktop.

## Behaviors

1. Segment control sticky under the topbar at **all** breakpoints (≥44px targets, `role=tablist`) — top placement for reachability while scrolling content.
2. Only the active pane is shown; it fills remaining viewport height (`flex: 1`).
3. Compose is a **compact dock** below the tabs; does not compete with the guide for vertical space.
4. Pane change uses 150–250ms fade; honor `prefers-reduced-motion`.
5. Opening a library item switches to Guide; compose/recompose switches to Atelier then Guide.

## Acceptance

- Desktop and mobile: never show ≥2 workspace panes at once.
- Guide iframe / Atelier trail / Library list each use nearly full remaining height.
- `npm run build` green.
