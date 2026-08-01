---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T07:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T07:00:00Z"
content_fingerprint: "sha256:d3d83c044309d2d9061c43d2265c4e52212747de4c60efe35dce53ccbc9820f2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-019 — Listening diary (source + draft + publish)

Upstream: REQ-010 / DOM-004

## Data model

Table `listening_diary_posts`:

| Column | Notes |
| --- | --- |
| id | PK |
| user_id | FK users, CASCADE |
| status | `draft` \| `published` |
| source_provider | e.g. `discogs` |
| source_external_id | string |
| source_kind | `vinyl` \| `cd` \| … |
| title | denormalized from snapshot |
| cover_image_url | denormalized |
| listening_note | ≤500 chars |
| listened_on | date (UTC date string / Date) |
| snapshot_json | full ReleaseSnapshot |
| share_slug | unique, set on first publish |
| published_at | null until published |
| like_count, comment_count | denormalized ints |
| created_at, updated_at | UTC |

Table `diary_guide_links` (reserve):

| Column | Notes |
| --- | --- |
| id | PK |
| diary_post_id | FK CASCADE |
| guide_id | FK listening_guides SET NULL or CASCADE |
| aspect | short string |
| created_at | UTC |

## Snapshot builder (Discogs)

`build_diary_snapshot(payload) -> dict` beside `analyze_discogs_release`:

- cover from `images[0].uri` or `thumb`
- title, year, labels/catno, uri
- composers / performers / ensembles (orchestra|ensemble|choir roles)
- tracklist `{position, title, duration, type}`
- source_kind from Discogs formats (Vinyl→vinyl, CD→cd, else `release`)
- provenance: release_id, master_id, fetched_at

## API (auth required unless noted)

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/v1/listening-diary` | body `{provider, external_id, listening_note?, listened_on?, source_kind?}` → fetch snapshot → **201** draft |
| GET | `/v1/listening-diary` | my list; query `status=` |
| GET | `/v1/listening-diary/{id}` | owner detail |
| PATCH | `/v1/listening-diary/{id}` | note / listened_on |
| POST | `/v1/listening-diary/{id}/publish` | status published; allocate slug |
| POST | `/v1/listening-diary/{id}/unpublish` | back to draft; keep slug |
| DELETE | `/v1/listening-diary/{id}` | owner delete |

Unsupported provider → 400. Discogs miss → 404. Discogs down → 502.

## Acceptance

1. Offline: `build_diary_snapshot` from fixture has cover, composers, tracklist, ensembles when present.
2. Auth create draft from mocked Discogs; list shows draft; stranger cannot GET.
3. Publish sets published_at + share_slug; unpublish clears published_at.
4. schema_patches / create_all create tables on SQLite test DB.

## Non-goals

- Guide generation from diary
- Non-Discogs providers
