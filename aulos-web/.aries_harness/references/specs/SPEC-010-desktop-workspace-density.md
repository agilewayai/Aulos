---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T21:45:00Z"
effective_status: "active"
effective_since: "2026-08-01T21:45:00Z"
content_fingerprint: "sha256:b1e19261bde9110a8113c24f3e802b5681b72aadb647f103f943be3d2c77196f"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-010 — Desktop workspace density

Upstream: REQ-006, SPEC-005, ui-ux-pro-max (dense journal / reading shelf).

## Outcome

At `min-width: 1100px`, aulos-web browse surfaces behave like a full-bleed studio shelf: shell height locks to the viewport, stages scroll inside, and list/reader/rail columns share the width. Prose measure stays readable (~72ch) only for focused article reading.

## Behaviors

1. **Shell** — `.shell-studio` uses `100dvh` with overflow hidden; `.stage` scrolls; gutters via `--workspace-gutter`.
2. **Studio** — `.studio` / `.studio-stage` / `.guide-reader` fill remaining height; guide iframe stretches; compose dock stays compact when collapsed.
3. **Diary** — shell and layout drop `1120px` cap; sticky list pane + fluid detail; guide review = reader main + sticky notes/actions rail.
4. **Plaza / blog** — shells full width (no 44rem / 78rem squeeze). Plaza feed 3/4 cols; 我的聆乐 browse feed album tiles 2→3→4 cols. Diary detail / atelier / guide review stay full-bleed workspace; only continuous note prose uses ~72ch.
5. **Guide chrome** — desktop shows a short bar hint; immersive fullscreen remains available.
6. **Motion** — honor `prefers-reduced-motion` for atmosphere.

## Non-goals

- Dark mode; native apps; rewriting guide HTML typography inside iframes.
- Changing <1100px mobile/tablet stacks.

## Acceptance

- `npm run build` green.
- ≥1100px: no large empty side gutters on studio/diary/plaza chrome; guide frames use viewport height.
- <1100px: prior responsive rules still apply.
