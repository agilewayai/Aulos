---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "history-retrospective"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:05Z"
generated_at: "2026-08-02T07:26:47+00:00"
effective_status: "generated"
effective_since: "2026-08-02T07:26:47+00:00"
content_fingerprint: "sha256:039255257baece086662c9a8a3d8cc6c6b9fc8d0d94048b585694f57ff8f7414"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-02T07:26:47+00:00`

## Recent changes

- **Production deploy — SPEC-034 Slice G:** operator requested production deploy,
- Evidence memo:
- Verify: `bash deploy/aulos-ctl.sh doctor` passed; `bash
- **SPEC-034 Slice G / multi-work sheet mode:** Root cause was plural program data
- Compose/render upgrade: `render_bilingual_guide_html` now renders sheet tabs
- Skill bumps: `aulos-listening-synthesize` 0.2.1 and

## What is working

- **Production deploy — SPEC-034 Slice G:** operator requested production deploy,
- Evidence memo:
- Verify: `bash deploy/aulos-ctl.sh doctor` passed; `bash
- **SPEC-034 Slice G / multi-work sheet mode:** Root cause was plural program data

## What needs attention

- working tree is dirty with 196 tracked or untracked change(s)
- no explicit next-up slice is recorded

## Durable reminders

- Listening guides are Salon Codex products: chambers + bilingual panes + playable ambient (SPEC-005/006).
- Cold-path synthesize: family structural lists win; scrub foreign flagship chambers; KB needs positive title match.
- Media contract: `/v1/media/audio` cache→proxy→origin with `Content-Disposition: inline`.
- Eval hard-fails missing ambient player.
- **Identity:** Catalog YAML + `IdentityResolver` only — no composer/work `elif` in runtime (SPEC-008 / ADR-004).
- **Chinese locales:** `zh-Hans` (简体) + `zh-Hant` (繁体) only. Never regional codes (`*TW*`, `*CN*` region tags) in OSS source or UI.

## Promotion rule

- if a lesson is durable, move it into MEMORY, docs/insights, AGENTS, or a reusable harness asset
- do not let retrospective output become the only place where important operating knowledge lives
