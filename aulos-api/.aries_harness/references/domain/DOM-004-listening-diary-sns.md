---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "domain-analysis"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T07:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T07:00:00Z"
content_fingerprint: "sha256:346a49f80e6e6d17059fe78fb5ffcafc0ff6a2011ac9db50fb42cff60bd1fe81"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# DOM-004 — Listening diary + plaza SNS

Upstream: REQ-010

## Bounded contexts

| Context | Owns | Does not own |
| --- | --- | --- |
| ListeningDiary | Diary post, source snapshot, note, publish lifecycle | Guide HTML / agent chain |
| ListeningSocial | Follow, plaza feeds, like, comment | Auth identity creation |
| DiscogsConnector | Fetch/search Discogs → diary snapshot | Catalog identity |
| ListeningGuide (existing) | Guide aggregate | Diary identity |

## Ubiquitous language

- **ListeningSource** — provider + external_id + source_kind
- **ReleaseSnapshot** — immutable display copy at create time
- **ListeningDiaryPost** — aggregate root (draft | published)
- **ListeningNote** — optional short note (≤500 chars)
- **DiaryGuideLink** — diary ↔ guide attachment by aspect (multi)
- **ListeningPlaza** — discovery of published diaries
- **UserListeningBlog** — user’s published diaries (+ future shared guides)

## Aggregates & invariants

### ListeningDiaryPost

- Create requires supported provider (v1: `discogs`) + external_id; snapshot fetched sync.
- Default status `draft`; only owner mutates note / publish / unpublish / delete.
- Public read only when `published`.
- Same user may post the same release multiple times (different `listened_on`).
- Snapshot is immutable after create (no silent Discogs refresh in v1).

### ListeningSource / ReleaseSnapshot

- Common shape: title, cover, composers, performers, ensembles, year, label, catno, tracklist.
- Provider-specific raw kept under snapshot `provider_raw` / provenance.
- Future providers map into the same shape; unknown provider → 400.

### DiaryGuideLink

- One diary may attach many guides (per work/aspect).
- Guide remains independent aggregate; link does not cascade-delete guide on diary delete
  without explicit policy (v1: ON DELETE CASCADE link rows only).

### UserFollow / Like / Comment

- No self-follow.
- Like/comment only on `published` posts via public APIs.
- Unpublish hides from plaza; stored interactions remain for owner metrics.

## Events (logical)

- DiaryCreated, DiaryPublished, DiaryUnpublished, DiaryDeleted
- UserFollowed, UserUnfollowed
- PostLiked, PostUnliked, CommentAdded

## Extension points

| Provider | source_kind examples | Status |
| --- | --- | --- |
| discogs | vinyl, cd | **v1** |
| netease / qq_music / apple_music | digital_album | later |
| youtube | video_performance | later |
