---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "request"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T16:55:00Z"
effective_status: "active"
effective_since: "2026-07-27T16:55:00Z"
content_fingerprint: "sha256:0c3330a40ec75662e208f5cfbc6e672e33fe8436442841265602364d8d2c1d1c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-010 — Composer Life Dossier & Works Tree

## Outcome

Operators can build and browse a **composer dossier**: dated life timeline events plus a hierarchical
works collection, ingested from authority sources (Wikidata + Wikipedia) via the async crawl queue,
starting from Explore seeds (Bach / Beethoven / Mozart first).

## Non-goals (S1)

- Movement-level IMSLP score trees
- Grove proprietary text
- Arbitrary web biography NLP
- Multi-process Redis/ARQ (use in-process `job_queue`)

## Data model

1. `composer_life_events` — typed dated events with place + provenance
2. `works` extended with `parent_work_id`, `work_kind`, `year_start`/`year_end`
3. `composers` extended with `era`, `summary_en`, `summary_zh`
4. RAG: timeline/work narrative docs + chunks after structured upsert

## Crawl

Wikidata connector `mode=composer_dossier`: entity claims → life events; SPARQL P86 works → tree;
optional Wikipedia sitelink narrative; portraits via existing P18 path. Async enqueue (META-001 §3.3).

## Acceptance

1. `POST /v1/admin/composers/{id}/build-dossier` returns 202 and completes life + works ingest.
2. `GET .../dossier` returns timeline (sortable) + works_tree + portrait meta.
3. Bach seed yields birth+death events and multiple works.
4. OPS **Composer dossier** module: pick composer → build → browse timeline + tree (no QID in primary UX).
5. Pytest with mocked Wikidata/SPARQL.

## Completeness, ordering & identity (Δ)

1. **Works ingest** — SPARQL P86 musical works only (exclude film / non-score noise); paginate to a soft
   cap (**2048**); prefer inception year + catalog number (BWV / K. / Op.) ordering; store genre facet with
   non-music genre labels dropped.
2. **Views** — dossier payload exposes `works_tree` (hierarchy), `works_by_year` (timeline), and
   `works_by_genre` (题材目录); OPS toggles 时间线 / 题材 (default 题材).
3. **Famous identity lock** — allowlisted `famous_composers` QID / canonical EN name win over polluted
   DB rows from person multi-source merge (REQ-012). `resolve_composer_qid` ignores dirty DB QID for
   famous ids. Rebuild replaces prior works for that composer_id.

## Related

- REQ-008 registry, REQ-009 explore seeds, REQ-012 famous QID lock, META-001 §3.3 / §3.4
- SPEC-009 / SPEC-010
