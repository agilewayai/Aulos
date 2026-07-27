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
generated_at: "2026-07-27T09:46:13+00:00"
effective_status: "generated"
effective_since: "2026-07-27T09:46:13+00:00"
content_fingerprint: "sha256:4f13d85884d57c6fde1cd2a6f9ce5afc8af408209834a070bbfc8bdd81d90d74"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-07-27T09:46:13+00:00`

## Recent changes

- Fleet DevOps control plane:
- `deploy/aulos-ctl.sh` — unified commands: `deploy`, `build`, `restart`, `status`, `smoke`, `logs`, `doctor`, `secrets {init|check}`, `units install`, `ingress apply`, `test`.
- Shared libs under `deploy/lib/`; `start-host.sh` → thin `aulos-ctl deploy` wrapper.
- AUDIT-009 continuation — F2 / F10 / F11 (F1 deferred per operator):
- F11: `ADR-008-plaintext-systemsetting-secrets-sprint1.md` accepts Sprint-1 plaintext secrets with compensating controls.
- F2: `SPEC-015` guide HTML security; `guide_html_security.sanitize_guide_html` + public CSP tests; web `guideHtml.ts` sandbox selftest (no `allow-same-origin`).

## What is working

- Fleet DevOps control plane:
- `deploy/aulos-ctl.sh` — unified commands: `deploy`, `build`, `restart`, `status`, `smoke`, `logs`, `doctor`, `secrets {init|check}`, `units install`, `ingress apply`, `test`.
- Shared libs under `deploy/lib/`; `start-host.sh` → thin `aulos-ctl deploy` wrapper.
- AUDIT-009 continuation — F2 / F10 / F11 (F1 deferred per operator):

## What needs attention

- working tree is dirty with 238 tracked or untracked change(s)
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
