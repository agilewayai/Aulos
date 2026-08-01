---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "request"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T12:50:00Z"
effective_status: "active"
effective_since: "2026-07-27T12:50:00Z"
content_fingerprint: "sha256:69c496392d0a95c8e9b0a4162dfc4c4c055188e1cb8d12bacb38d0ed5b049da8"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-009 — Authority Source Discovery (Graph Search)

## Outcome

Operators can **explore beyond the registered authority manifest** using a bounded
depth+breadth graph search that discovers candidate sources on the open web, scores them,
and registers them into REQ-008 lifecycle (`candidate` → verify → enable crawl).

**Product entry (META-001 §3.4):** operators pick a **composer by name** (A–Z / Famous /
portraits), not a Wikidata QID. QIDs and crawl params are derived server-side.

The same graph engine seeds **composer/work knowledge expansion** (entity → external IDs →
authority URLs → crawl jobs).

## Non-goals

- Unbounded web crawl or HTML scraping without fetch policy
- Auto-verify sources without human/agent review
- Replacing Work Identity Catalog

## Algorithm (normative)

1. **Seeds** — verified registry sources; optional `composer_id` / `wikidata_qid` / `work_id`.
2. **Breadth** — lateral expansion across known authority neighborhoods (registry peers,
   shared domain families, manifest `candidates`).
3. **Depth** — follow Wikidata URL claims (P856, P973, P1343) and external-ID resolvers
   (MusicBrainz, IMSLP, RISM) up to `max_depth`.
4. **Score** — domain tier hints, claim type, duplication with registry; penalize social/streaming.
5. **Output** — durable `source_discovery_runs` row with graph + ranked candidates.
6. **Register** — top candidates → `POST` as `candidate` sources (disabled, no connector).
7. **Enqueue crawl** — when `enqueue_crawl=true`, enqueue verified Wikidata/Wikipedia/MusicBrainz/IMSLP
   jobs for the seed entity (composer/work KB expansion).
8. **Diagnosis hook** — KB-DIAG proposes `explore_sources` L1 actions for corpus/registry/retrieval gaps.

## Acceptance

1. `POST /v1/admin/sources/explore` returns graph + candidates within configured bounds.
2. Explorer uses only allowlisted discovery fetchers (Wikidata entity API on verified source).
3. `POST .../explore/runs/{id}/register-candidates` creates candidate rows, skips duplicates.
4. `enqueue_crawl` / `POST .../enqueue-crawl` enqueues authority crawl jobs for verified sources only.
5. Diagnosis `explore_sources` action is auto-safe and executes via improve cycle.
6. OPS **Explore sources** module shows interactive graph, scores, register + crawl actions.
7. Pytest covers mocked Wikidata expansion, crawl enqueue, and register flow.

## Related

- REQ-008 Authority Source Registry
- KB-DIAG / KB-IMPROVE (corpus gaps may trigger explore in future)
- ADR-006 allowlisted fetch policy
