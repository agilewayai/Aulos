---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "request-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T22:10:00Z"
effective_status: "active"
effective_since: "2026-08-01T22:10:00Z"
content_fingerprint: "sha256:b56c46d12bd86cc56abec5217a9aa2413931bc9e2ba8bd574414259f0653fcc5"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-024 — Discogs release structure before deepen

## Why now

Multi-work classical pressings (e.g. Bach violin + double concertos on one Philips
disc) were collapsing into a thin `family:violin-concerto` scaffold because intake
never built a faithful **album program map** before synthesize/thicken. Listeners
got generic “speech contract” prose instead of work-by-work depth.

## Outcome

For every Discogs-sourced listening job:

1. **Fetch complete** release/master metadata (credits, tracklist, formats, label, images).
2. **Identify structure** — program works, catalog numbers, soloist hints, shelf shape.
3. **Gate** — deepen/thicken must not proceed until `structure_ready`.
4. **Expand by layers** — release metadata → program map → per-work deepen → pressing synthesis.

This is a **fleet-grade covenant** (META-001 §4.1), not a case patch.

## Non-goals

- Hand-authored craft YAML per Discogs release id
- Replacing Catalog / IdentityResolver for canonical work ids
- UI redesign of 聆乐 surfaces in this request

## Acceptance

- ≥2 unrelated multi-work identities produce `multi_work_program` with ≥2 program works
- Empty/partial payloads are `structure_ready=false` with explicit gaps
- Analyze + diary snapshot both emit `release_structure`
- Covenant promoted into META-001; ARCH/ADR record the pipeline order

## Delta 2026-08-02 — program fold-back and persist gate

Guide `#59` (`/discogs #7083684`, Hummel / Weber / Haydn piano-flute-cello trios)
proved that "program loop ran" is not sufficient. The gateway correctly built a
three-work program map and gathered evidence per work, but the final guide still
collapsed into `Unknown composer` + generic `family:piano-trio` prose because
album-level LLM/family layers could overwrite the folded program subject. The API
then persisted `eval_pass=false` as `completed`.

Additional acceptance:

- Program-loop folds must carry per-work composer/title/catalog identity into final
  thesis, introduction, map, related works, and provenance.
- Later LLM/family layers must not overwrite program-loop identity scalars for
  ready multi-work pressings.
- A guide with `eval_pass=false`, process hard gate, review failure, or missing
  required ambient must retain diagnostic HTML/trace but must not be stored as
  `completed` / ready for review.
