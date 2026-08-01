---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "request-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:50:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:50:00Z"
content_fingerprint: "sha256:18daa9fc63036a00b5e7f3fb4b4c2d0165871cb06b05603635ca58ea519f97bb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-022 — Identity freeze + Catalog/facet hardening (anti-case)

## Outcome

Listening guides for Discogs / multi-work / unknown pressings must keep the
**locked composer and form class** through synthesize → compose → promote.
Performer surnames, bare Köchel prefixes (`KV`), and packaging titles must not
rewrite identity or invent a false Catalog work tie.

## Probe class (not a case patch)

Failures observed on a multi-Köchel piano-sonata pressing are treated as a
**class**: any performer name containing a composer alias substring; any message
with multiple catalog numbers matching none of the Catalog works; German/Italian
form spellings; English piano sonata ≠ cello duo.

Acceptance tests must cover **≥2 unrelated identities** for each gate.

## Non-goals

- Hand-authored per-work craft YAML for the probe pressing
- One-off Mozart / Eschenbach / Bach string tables
- Changing the agent-orchestrated listening chain topology

## Acceptance

1. Composer-card / Catalog composer alias match uses token boundaries — performer
   surnames that merely contain an alias do not unlock that composer card.
2. When IntentLock has a composer, synthesize must not overwrite dossier composer
   from a mismatched card.
3. Catalog scoring must not award work points for bare prefix tokens (`kv`, `op`,
   `bwv`) without the numeric part; multi unmatched catalog numbers yield
   `composer_only` / `multi_work`, not a false near-tie between unrelated works.
4. FacetClassifier recognizes solo keyboard sonata/rondo morphology (incl. common
   non-English spellings) and must not map bare piano+sonata → duo-cello-piano.
5. `build_promote_candidate` refuses when locked composer ≠ dossier composer, or
   when review/decontam hard-fail flags are set.
6. ProductScorecard identity dimension fails closed on IntentLock composer drift.
