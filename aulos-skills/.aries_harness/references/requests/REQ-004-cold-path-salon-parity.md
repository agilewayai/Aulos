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
content_fingerprint: "sha256:c68fd126f0e5df71b28aeeac2bfcbb1ff8d38c09cf2f97f5b5b94a0bb8ae1c83"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-004 — Cold-path Salon Codex parity via skill synthesis

## Problem

Flagship corpus works (e.g. Goldberg) yield museum-grade Salon Codex guides.
Cold-path requests (e.g. Chinese: Beethoven cello sonatas & variations) collapse to
thin generic bullets because intake fails multilingual normalization and width/depth
have no dossier chambers to fill.

## Desired outcome

Any recognizable classical listening intent should reach near-flagship chamber coverage
through **skill orchestration**, not one-off hardcoded HTML for each work:

1. Intake normalizes work + composer (EN/ZH).
2. Corpus loads a curated work dossier when present.
3. **Synthesize** compounds composer cards + genre-family scaffolds (+ optional LLM JSON)
   into a Salon Codex dossier when corpus is missing or thin.
4. Width / depth / compose / eval consume that dossier uniformly.

## Non-goals

- Hardcoding a full Beethoven guide page in the web app
- Replacing curated corpus excellence for flagship works
- Inventing Discogs/YouTube IDs when neither scaffold nor LLM supplies them
