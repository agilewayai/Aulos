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
content_fingerprint: "sha256:4e7d7eb7b7a47ee0bf7a14217508500075c5be967506d6c5f4cb65cf8e04cced"
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
5. Eval could pass (score ≥ 8) without an ambient player.

## Desired outcome

Every compose output must ship:

1. **Bilingual** EN/ZH panes when a `zh` pack exists (family, corpus, or LLM).
2. **Ambient player** (`data-ambient-player=v2`) with cache→proxy→origin failover,
   floating corner UI, optional playlist, and a “why this music” note.
3. **Openly licensed** audio only; serve via `/v1/media/audio` as `inline`.
4. **Work-identity hygiene** — foreign flagship chambers (e.g. Goldberg) must not appear
   in unrelated cold-path dossiers.
5. **Eval hard-fail** when ambient is missing.

## Non-goals

- Hosting commercial recordings
- Replacing curated Goldberg playlist excellence with generic singles
- Auto-fixing every historical published guide without recompose (serve-time chrome helps UI only)
