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
generated_at: "2026-07-25T19:31:11+00:00"
effective_status: "generated"
effective_since: "2026-07-25T19:31:11+00:00"
content_fingerprint: "sha256:1e43b9047a4b1ab0abb5dee8c670fecb78ddb7b662a882e7cf38bd3161d13e5d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-07-25T19:31:11+00:00`

## Recent changes

- Fixed Unknown composer: Chinese 《》 title parse + catalog soft aliases (CJK len≥2); added Dvořák Dumky catalog shelf
- Chinese locales: **简体 (zh-Hans)** + **繁体 (zh-Hant)** — script tags only
- Guide switcher: 简体 | 繁体 | English
- External skill intake: **Agent Reach** (`Panniantong/Agent-Reach` @ `b4d52c46…`)
- Security audit → conditional allow as **search enabler only**
- Installed `skills/enabler-agent-reach/` (policy fence; social/cookie/CLI-install denied)

## What is working

- Fixed Unknown composer: Chinese 《》 title parse + catalog soft aliases (CJK len≥2); added Dvořák Dumky catalog shelf
- Chinese locales: **简体 (zh-Hans)** + **繁体 (zh-Hant)** — script tags only
- Guide switcher: 简体 | 繁体 | English
- External skill intake: **Agent Reach** (`Panniantong/Agent-Reach` @ `b4d52c46…`)

## What needs attention

- working tree is dirty with 57 tracked or untracked change(s)
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
