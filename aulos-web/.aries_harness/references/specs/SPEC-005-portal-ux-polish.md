---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T17:40:00Z"
effective_status: "active"
effective_since: "2026-07-26T17:40:00Z"
content_fingerprint: "sha256:3b3e0477e79e50ba51f7876438a4dd5ee52d7d7f957913fb2c724ed15c6ead52"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-005 — User portal product UX polish

Upstream: SPEC-001 + ui-ux-pro-max (editorial listening studio).

## Outcome

aulos-web feels like a real listening product portal (not a prototype dashboard):
clear hierarchy, elegant motion, accessible forms, responsive mobile workspace.

## Behaviors

1. **Auth gate** — desktop split brand panel + form; mobile stacked; visible labels; toast feedback.
2. **Studio shell** — compact topbar (brand + user chip + sign out); compose dock as primary CTA surface.
3. **Workspace** — desktop: Guide dominant + Atelier rail; mobile: tab switcher Guide | Atelier | Library (≥44px targets).
4. **Guide toolbar** — primary actions visible; secondary under “More” on narrow viewports.
5. **Motion** — 150–300ms purposeful transitions; honor `prefers-reduced-motion`.
6. **Safe areas** — padding respects `env(safe-area-inset-*)`.

## Non-goals

- Dark-mode theme toggle; native apps; redesign of published guide HTML itself.

## Acceptance

- `npm run build` green.
- 375 / 768 / 1024 layouts usable without horizontal scroll.
- Auth + studio keyboard focus rings visible.
