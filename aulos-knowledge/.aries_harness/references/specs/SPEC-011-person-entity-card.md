---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T07:20:00Z"
effective_status: "active"
effective_since: "2026-08-01T07:20:00Z"
content_fingerprint: "sha256:96807a686889082285eb8daa098a61d48e993cec21157720317f7b8af91623c7"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-011 — Person entity info card resolve

Upstream: REQ-011

## Endpoint

`POST /v1/kb/entities/person/resolve`

Body: `{ "name": string, "kind": "composer"|"performer"|"ensemble"|"person", "enrich": true }`

Auth: same admin/service token as other `/v1/kb` product reads that write (or admin).

## Behavior

1. Normalize name; reject blank.
2. **Local lookup (strict):** match `composers` by exact `name_en` / `name_zh` / aliases / id
   (case-insensitive). Latin surname-only match allowed **only when unique** in the table.
   **No** CJK substring soft match. Unrelated names (e.g. 朱莉亚尼) must never resolve to 巴赫.
3. **Local RAG:** only after a composer row match; filter snippets by `entity_id` / name
   compatibility. Orphan RAG hits alone never invent identity (`source=unresolved`).
4. If matched row has summary or owned snippets → `source: "knowledge"`.
5. Else if `enrich` (product API default true), authority order:
   1. **Discogs artist profile** (first) — search + `/artists/{id}` profile; ingest into KB
   2. Wikidata `wbsearchentities` (label/match must agree with query) + Wikipedia summary
6. Persist composer + knowledge doc; return `source: "enriched"` with provenance.
7. If all fail → `source: "unresolved"`.

## Card shape

```json
{
  "name": "...",
  "kind": "composer",
  "person_id": "mauro-giuliani",
  "display_name": "...",
  "lifespan": "",
  "era": "",
  "summary": "...",
  "portrait_url": "",
  "external_ids": {"discogs": "123", "wikidata": "Q…"},
  "snippets": [],
  "source": "knowledge|enriched|unresolved",
  "authority": "discogs|wikidata|",
  "provenance": [{"source_id": "discogs", "url": "..."}],
  "matched": true
}
```

## Acceptance

1. Offline: local composer with summary → `source=knowledge`, no network.
2. Offline: Bach corpus present; resolve `朱莉亚尼` / `Giuliani` with `enrich=false` →
   `unresolved`, never Bach summary.
3. Discogs mock profile → ingest → next resolve is knowledge.
4. Wikidata enrich only when Discogs miss; label must be name-compatible.
