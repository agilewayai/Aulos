---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:23:49+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:23:49+00:00"
content_fingerprint: "sha256:dff441d93fd7f05a6f6dd07fe4b653e276378b5aeb8d92c4d82b47196f3fab9c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-003 — Listening Guide Workflow

## Behavior

`POST /v1/listening-guides` (auth required)

Request: `{ "message": str, "work_hint": optional str }`

Response:

```json
{
  "id": 1,
  "work_title": "J.S. Bach — Goldberg Variations, BWV 988",
  "composer": "Johann Sebastian Bach",
  "status": "completed",
  "source": "curated|deepseek|grok|fake",
  "steps": [
    {
      "id": "intake",
      "title": "...",
      "status": "completed|running|failed",
      "thinking": "...",
      "detail": "...",
      "started_at": "...",
      "finished_at": "..."
    }
  ],
  "guide_html": "<!DOCTYPE html>...",
  "summary": "short plain-text summary",
  "created_at": "..."
}
```

## Workflow steps (ordered)

1. `intake` — parse listening intent / normalize work title  
2. `width` — wide research (historical & cultural frame)  
3. `depth` — deep research (musical architecture & listening map)  
4. `compose` — synthesize professional guide narrative  
5. `render` — produce beautiful standalone HTML page  

## Publish / share

- `POST /v1/listening-guides/{id}/publish` — assign stable `share_slug`, set `published_at`
- `POST /v1/listening-guides/{id}/unpublish` — clear `published_at` (keep slug)
- `POST /v1/listening-guides/{id}/recompose/stream` — owner SSE; overwrite HTML/research; keep slug/published
- `POST /v1/listening-guides/{id}/update-publish` — ensure published (same slug)
- `GET /v1/listening-guides/by-share/{slug}` — owner lookup for share-page toolbar
- Public `GET /v1/public/guides/{slug}` — raw guide HTML (no auth); no owner Re-compose/Update/Studio chrome on the public page (manage in studio)

## Offline contract

When ops LLM is not live-ready, use curated research packs (Goldberg Variations featured) and still emit full step observability.
Research is cached into the knowledge base for RAG on later composes (FastEmbed local by default; lexical fallback if unavailable).
Ambient theme audio renders as a collapsed mini-player (expand for recording credit).

## Orchestration (SPEC-003 delta — agent-centric)

- **API must not** orchestrate `SkillRuntime.iter_listening_chain` / stepwise `run_trigger`.
- API injects RAG / optional LLM dossier into the job payload, then delegates to **aulos-agent** (`AgentProxy.run_listening`).
- Agent executes the listening skill tool chain (`run_listening_skill` per trigger) per ARCH-002 / ADR-003.
- Persistence and SSE remain in the API gateway.

## Verification

- pytest covers step shape, Goldberg detection, HTML presence, auth gate
- pytest covers publish/public, recompose slug stability, knowledge search
- pytest asserts listening path goes through AgentProxy (not API-local skill chain)
- web studio renders steps + sandboxed guide iframe; Re-compose + Update publish controls
