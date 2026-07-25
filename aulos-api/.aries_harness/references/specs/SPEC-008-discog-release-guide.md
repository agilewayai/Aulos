---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T19:00:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T19:00:00+00:00"
content_fingerprint: "sha256:5a9620670b9b3434011176535728c7c01936dc91d1c198c0ea1af909da7da5a2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-008 — `/discogs` release → listening guide

Upstream: REQ-008

## ID semantics

| Operator writes | System interprets |
| --- | --- |
| `/discogs #12345` / `/discogs 12345` | Discogs **release** id (primary) |
| `/discogs #423-287-1` / `/discogs 423 287-1` | Discogs **catalog number** → database search → best Classical release |
| same numeric id if release 404 | fallback Discogs **master** id |
| Discogs **Label** entity id | **out of scope** for this SPEC |

## Command grammar

```
/discogs\s+#?( <digits> | <catno with separators> )
```

Catalog numbers must include a separator (`-`, space, etc.) so they are not truncated
to a short release id (smoke: `423-287-1` must not become release `423`).

## Behavior

When `POST /v1/listening-guides` (or stream) receives a matching message:

1. **Parse** release id from slash command.
2. **Fetch** `GET https://api.discogs.com/releases/{id}` (User-Agent required).
   - Auth: `AULOS_DISCOGS_TOKEN` or `AULOS_DISCOGS_KEY` + `AULOS_DISCOGS_SECRET` when set.
   - On 404, try `GET /masters/{id}` and use `main_release` or master tracklist/artists.
3. **Analyze** (generic role heuristics, no composer branches):
   - composers ← `extraartists` roles matching compose/composed/composer
   - performers ← primary `artists` + instrument/conductor roles
   - work title candidates ← tracklist titles + release title (strip artist prefix)
   - label / catno / year for vinyl shelf
4. **Resolve identity** via Catalog (`resolve_identity`) on constructed `composer + work` text.
5. **Rewrite** gateway `message` / `work_hint` to a normal listening intent that names the
   recovered work and this release’s performers.
6. **Seed** `kb_dossier` (or merge) with:
   - `interpretations[]` entry for this pressing (`discogs_url` = canonical release URL)
   - `vinyl_and_discography[]` with label/catno/year/note
   - `_provenance.discogs` `{ release_id, master_id?, uri, fetched_at }`
7. Continue existing chain: identity → RAG → web research → LLM dossier → agent skills → HTML.

## Errors

| Case | User-visible |
| --- | --- |
| Bad command / missing id | 400 `Invalid /discogs command; expected /discogs #<release-id>` |
| Discogs 404 after release+master | 404 `Discogs release not found` |
| Rate limit / network | 502 `Discogs unavailable` with retry hint |
| Analyze succeeds but identity unknown | Still compose guide using Discogs-derived title/composer strings (no invented work_id) |

## Acceptance

1. Unit: command parser accepts `/discogs #20017387`, `/discogs 20017387`.
2. Unit: analyzer extracts composer + performers from a fixture release JSON (no live network).
3. Integration (fake agent): streaming compose with mocked Discogs returns completed guide whose
   research/context mentions Discogs release URL and recovered work title.
4. Regression: free-text Goldberg / Dumky intake unchanged.
5. No new composer `if/elif` trees in Python.

## Non-goals

- Marketplace, collection, wantlist
- Image download pipeline
- Full knowledge-plane Discogs ingest job
