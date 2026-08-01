---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T08:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T08:00:00Z"
content_fingerprint: "sha256:cdf548241ce0f913d7d01c1bd5d16598e5a61c1d07575a104e42d1d80ac152a8"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-012 — Multi-source person aggregate + bilingual card

Upstream: REQ-012 (extends SPEC-011 strict identity)

## Endpoints

### Knowledge

`POST /v1/kb/entities/person/aggregate`

```json
{
  "name": "Mauro Giuliani",
  "kind": "composer",
  "fragments": [
    {
      "source_id": "discogs",
      "display_name_en": "...",
      "summary_en": "...",
      "portrait_url": "...",
      "external_ids": {"discogs": "..."},
      "provenance": [{"source_id": "discogs", "url": "..."}]
    }
  ],
  "fetch_remote": true,
  "persist": true
}
```

`POST /v1/kb/entities/person/resolve` — returns the **same bilingual card shape**;
when `enrich=true` runs aggregate (Wikidata+Wikipedia). Discogs fragment is
supplied by the API gateway.

### API product

`GET|POST /v1/entities/person` orchestrates:

1. Local strict resolve (`enrich=false`)
2. If bilingual-complete → return
3. Else Discogs fragment + knowledge `aggregate` (WD/WP fan-in + merge)
4. If one locale missing → OPS LLM faithful translate → patch ingest
5. Return unified bilingual card

## Field-merge precedence (normative)

| Field | Priority (first non-empty wins) |
| --- | --- |
| `external_ids.wikidata` / lifespan | Wikidata > local > Discogs |
| `display_name_en` | Wikidata EN label > Discogs name > local > query |
| `display_name_zh` | Wikidata ZH label > Wikipedia ZH title > local > translated EN name |
| `summary_en` | Wikipedia EN extract > Discogs profile > Wikidata EN description > local |
| `summary_zh` | Wikipedia ZH extract > Wikidata ZH description > local > **translated** summary_en |
| `portrait_url` | Discogs primary image > Wikipedia thumbnail > local |
| `aliases` | union (dedupe, case-insensitive) |

Identity rules from SPEC-011 remain: no orphan RAG; no CJK soft match to wrong person.

## Card shape (bilingual)

```json
{
  "name": "Mauro Giuliani",
  "kind": "composer",
  "person_id": "mauro-giuliani",
  "display_name": "毛罗·朱利亚尼",
  "display_name_en": "Mauro Giuliani",
  "display_name_zh": "毛罗·朱利亚尼",
  "lifespan": "1781–1829",
  "era": "",
  "summary": "……",
  "summary_en": "...",
  "summary_zh": "……",
  "summary_en_origin": "wikipedia|discogs|wikidata|local|translated",
  "summary_zh_origin": "wikipedia|wikidata|local|translated",
  "portrait_url": "",
  "external_ids": {},
  "sources": [
    {"source_id": "discogs", "role": "catalog_profile", "url": "", "fields": ["summary_en", "portrait_url"]},
    {"source_id": "wikidata", "role": "identity", "url": "", "fields": ["lifespan", "names"]},
    {"source_id": "wikipedia", "role": "encyclopedia", "url": "", "fields": ["summary_en", "summary_zh"]}
  ],
  "snippets": [],
  "source": "knowledge|aggregated|unresolved",
  "matched": true,
  "locale_default": "zh"
}
```

Backward compatible: `summary` / `display_name` = locale_default preferred (zh if present else en).

## Translation

- Only when native text for a locale is empty and the other locale has ≥40 chars.
- Prompt: faithful literary translation for classical-music bios; no invented facts.
- Mark `summary_*_origin=translated` and `display_name_zh_origin=translated` when applicable.
- LLM lives in **aulos-api** (OPS provider); knowledge stores results only.

## Acceptance

1. Aggregate with Discogs+Wikipedia mocks fills EN from Discogs/WP and ZH from WP ZH or translate stub.
2. Giuliani never becomes Bach (SPEC-011 regression).
3. Second resolve returns `source=knowledge` with both locales persisted.
4. UI shows 中文 / English toggle on the person panel.
