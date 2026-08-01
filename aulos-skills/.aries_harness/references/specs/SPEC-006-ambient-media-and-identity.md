---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:c6faf2e8da1f181cae725af162fb8452377f9f0d22365e02d68e27cd349215be"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-006 — Ambient media delivery + work-identity hygiene

## Ambient selection order

1. Catalog `ambient_ref` — only when the library entry id matches (work-bound catalog
   authority). Resolve through `resolve_ambient_audio`.
2. Curated `ambient_audio` on the work dossier — **keep** only honest work-matched
   open recordings. **Discard** peer / stand-in / 公开授权库轮换 copy (and any ambient
   that hits catalog `conflict_markers`).
3. **Do not** score or rotate `ambient-library.yaml` `related` / `defaults`.
4. Video-platform fallback via `ambient_video.resolve_ambient_video`, mode from OPS
   `listening.ambient_fallback_mode` (`embed` | `stream`, default `embed`):
   - Prefer concrete video ids from appreciation / interpretation links.
   - Never blind-embed a search-results page; search URLs are external links only
     unless a concrete id is resolved (optional yt-dlp `ytsearch`).
   - `embed` → `mode=embed` + `embed_src` (YouTube `youtube.com/embed/{id}` or
     Bilibili `player.bilibili.com/player.html?bvid=...`).
   - `stream` → extract audio URL (yt-dlp, optional dep); play via HTML5 + media proxy;
     `selection_source=video-stream`. On extract failure, degrade to embed when an id
     exists, else empty.
5. Else → no ambient player (honest absence).

Locale hint: prefer Bilibili candidates for Chinese UI; YouTube first otherwise.

## OPS contract

| Key | Values | Default |
| --- | --- | --- |
| `listening.ambient_fallback_mode` | `embed` \| `stream` | `embed` |

Stored in `system_settings` (same path as `listening.review_llm`). Compose context
receives `ambient_fallback_mode` from API → agent.

## Playback tiers (client, audio mode)

Order: **cache → proxy → origin**. Prefer same-origin `/v1/media/audio`.

API must serve cached files with `Content-Disposition: inline` (never `attachment`).

## Render contract

- Audio: `#aulos-ambient` `<audio>` + `data-ambient-player="v2"` when URL/tracks resolve.
- Embed: same aside chrome + iframe; `data-ambient-player="v2-embed"`; marker
  `id="aulos-ambient"` on a non-audio element (JS audio path no-ops without `<audio>`).
- `ambient-why` / `why_zh` must be honest about curated vs video embed vs video stream.
- Chinese listener messages prefer Chinese summary when `zh` thesis exists.

## Synthesize identity rules

- **Catalog is identity authority** (SPEC-008 / ADR-004). Intake uses `IdentityResolver`;
  runtime must not add work-proper-name `elif` branches.
- KB dossier injection requires **positive** identity match (`work_id` / `corpus_key` /
  distinctive catalog tokens). Empty `work_title` → refuse.
- Catalog prefixes (`bwv`, `op`, …) and generic form words are **weak** (see
  `catalog/policies/weak_tokens.yaml`) — they never prove same-work alone.
- Intake shelves come from resolved `family_id`, not hardcoded Bach/Beethoven trees.
- When a genre-family scaffold matches and corpus missed, **family structural lists win**
  over LLM/RAG merge appends.
- Scrub uses **catalog-derived `conflict_markers`** (from `conflict_work_ids`), applied to
  lists **and** scalars (`listening_thesis`, `work_introduction`, `ambient_audio`).

## Eval gate

- When ambient resolves (audio or embed), DOM must include `id="aulos-ambient"` and/or
  `data-ambient-player`.
- When no work-matched audio and no platform fallback → **soft** ambient score (0);
  **do not** hard-fail / force `pass=false` solely for missing ambient.
- Bilingual panes still scored; notes must mention missing ZH when corpus/synthesize hit.

## Studio / share surface

- Guide iframe must allow `allow-scripts allow-same-origin`.
- Inject `<base href="{origin}/">` for `srcDoc` / blob pages so `/v1/media/...` resolves.
- Public share pages may patch floating CSS at serve time; full ambient HTML still needs compose.
