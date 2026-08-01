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
content_fingerprint: "sha256:fdb3a4a60bd84058fe2c49d2f7769b393c48dd63552fa04155c4152c9dfe7dfb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-020 — Listening plaza SNS

Upstream: REQ-010 / DOM-004 / SPEC-019

## Tables

`user_follows`: follower_id, followee_id, created_at; UNIQUE(follower, followee); no self-follow.

`listening_diary_likes`: post_id, user_id, created_at; UNIQUE(post_id, user_id).

`listening_diary_comments`: id, post_id, user_id, body (≤1000), created_at, deleted_at nullable.

## API

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| GET | `/v1/plaza/feed` | optional | published posts newest-first; pagination `limit`/`offset` |
| GET | `/v1/plaza/posts/{slug}` | optional | public detail; 404 if draft/missing |
| GET | `/v1/plaza/home` | required | published posts from followees |
| POST | `/v1/social/follows/{user_id}` | required | follow; 400 self |
| DELETE | `/v1/social/follows/{user_id}` | required | unfollow |
| GET | `/v1/social/users/{user_id}` | optional | public profile + published diary list |
| POST | `/v1/plaza/posts/{id}/likes` | required | like published |
| DELETE | `/v1/plaza/posts/{id}/likes` | required | unlike |
| GET | `/v1/plaza/posts/{id}/comments` | optional | list non-deleted |
| POST | `/v1/plaza/posts/{id}/comments` | required | add comment on published |

Public payloads include author display_name, cover, title, note, listened_on, counts — never draft posts.

## Acceptance

1. Draft never appears in plaza feed or by slug.
2. Follow + home feed only followees’ published posts.
3. Like increments like_count; duplicate like is idempotent 200.
4. Comment soft-delete hides from GET.

## Non-goals

- Notifications, DMs, block lists, ranking algorithms
