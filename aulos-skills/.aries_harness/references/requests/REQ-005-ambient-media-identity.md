---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:6065e951641db7002a42c85bb6929163f1304e0e109c49ec3c4ee0302b131af9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-005 — Ambient media, floating player, and work-identity hygiene

## Problem

Flagship and cold-path guides can look “complete” on Salon Codex chambers while still
failing as listening products:

1. Stored HTML used a legacy English-only renderer → no bilingual panes, no ambient player.
2. Studio `srcDoc` iframes blocked scripts; media returned `Content-Disposition: attachment`.
3. Origin CDN (Wikimedia) is often unreachable; same-origin cache/proxy was secondary.
4. Cold-path LLM/RAG still smuggled Goldberg chambers into Beethoven cello guides.
5. Unrelated `ambient-library.yaml` related/defaults rotation played foreign works as
   “stand-in” (e.g. Mozart K.488 → Beethoven Moonlight).
6. Eval hard-failed whenever ambient DOM was missing, even when no work-matched open
   recording existed.

## Desired outcome

Every compose output must ship:

1. **Bilingual** EN/ZH panes when a `zh` pack exists (family, corpus, or LLM).
2. **Work-matched ambient only** — catalog `ambient_ref` or curated dossier CC0/open
   recording for **this** work. **No** related/defaults library rotation.
3. When no work-matched open recording exists → **video-platform fallback** controlled by
   OPS `listening.ambient_fallback_mode`:
   - `embed` (default, compliance-first): official YouTube / Bilibili iframe
   - `stream` (ops opt-in): server-side yt-dlp audio URL via `/v1/media/audio`
4. **Openly licensed** audio when in audio mode; serve via `/v1/media/audio` as `inline`.
5. **Work-identity hygiene** — foreign flagship chambers must not appear in unrelated
   dossiers; peer/stand-in curated ambient is discarded.
6. **Eval**: missing ambient is a soft score note (not hard-fail) when no matched audio
   and no platform fallback resolved; embed/stream DOM still required when resolved.

## Non-goals

- Hosting commercial recordings
- Crawling arbitrary audio sites
- Guaranteeing long-term stream-extract stability (OPS may switch back to embed)
- Replacing curated Goldberg playlist excellence with generic singles
- Auto-fixing every historical published guide without recompose (serve-time chrome helps UI only)
