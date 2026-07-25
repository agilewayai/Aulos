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
content_fingerprint: "sha256:91b38752a1ee0716f981b841db146de5feb47576db021c96e63f73c03d54254a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-006 — Ambient media delivery + work-identity hygiene

## Ambient selection order

1. Curated `ambient_audio` on the work dossier / family pack (`playlist_id` or `url`).
2. Adaptive related pack from `corpus/ambient-library.yaml` (composer / form / instrument / peer).
3. Default rotation pool.

Always resolve through `resolve_ambient_audio` so every URL gains `cache_src` + `proxy_src`.

## Playback tiers (client)

Order: **cache → proxy → origin**. Prefer same-origin `/v1/media/audio`.

API must serve cached files with `Content-Disposition: inline` (never `attachment`).

## Render contract

- `#aulos-ambient` / `data-ambient-player="v2"` present whenever ambient resolves.
- Floating fixed corner player; expandable playlist when `mode=playlist`.
- `ambient-why` / `why_zh` explaining curated vs related vs default selection.
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
- Curated ambient that carries conflict markers is discarded; related/default selection
  uses `ambient_ref` or facet instrument intersection (generic timbre gate).

## Eval gate

- Missing `id="aulos-ambient"` / `data-ambient-player` → **fail** (score capped & `pass=false`).
- Bilingual panes still scored; notes must mention missing ZH when corpus/synthesize hit.

## Studio / share surface

- Guide iframe must allow `allow-scripts allow-same-origin`.
- Inject `<base href="{origin}/">` for `srcDoc` / blob pages so `/v1/media/...` resolves.
- Public share pages may patch floating CSS at serve time; full ambient HTML still needs compose.
