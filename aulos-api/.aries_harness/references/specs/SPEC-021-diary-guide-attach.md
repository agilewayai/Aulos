---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T08:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T08:30:00Z"
content_fingerprint: "sha256:1e1b1b554c38bd7c468a20fb40a38f641937117e464e7354ad0117dd732a55a4"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-021 — Diary → ListeningGuide queue, review, publish

Upstream: REQ-010 S6 / STORY-PACK-010 S6 / SPEC-019 diary_guide_links  
Delta: REQ-011 review lifecycle (revise / unpublish / dismiss / delete)

## Outcome

From a 聆乐 diary post, author clicks **生成聆乐导赏** → job enters the existing
listening-guide queue → author sees tasks in 我的聆乐 backend → on completion
the UI prompts review → after author **发布导赏**, the guide is attached and
visible on the diary / plaza blog surface.

Authors can **submit review notes → recompose**, **unpublish**, **dismiss**, or
**delete** the diary↔guide link (SPEC-021Δ / REQ-011).

## Link model (`diary_guide_links`)

| Column | Notes |
| --- | --- |
| id | PK |
| diary_post_id | FK CASCADE |
| guide_id | FK listening_guides SET NULL |
| aspect | e.g. `作品导赏` / `演奏诠释` (default `作品导赏`) |
| status | `queued` \| `ready_for_review` \| `published` \| `failed` \| `dismissed` |
| review_notes | Text — latest author revision notes (UTC write) |
| revised_at | UTC — last notes-driven recompose enqueue |
| notified_at | UTC when author was first shown ready banner |
| published_at | UTC when attached guide published to diary |
| created_at | UTC |

`status` is also **derived** when listing: if link not terminal (`published`/`dismissed`),
map from `listening_guides.status` (`queued|running`→queued, `completed`→ready_for_review,
`failed`→failed).

### State transitions (SPEC-021Δ)

| From | Action | To |
| --- | --- | --- |
| — | enqueue | queued |
| queued | guide completed | ready_for_review |
| queued | guide failed | failed |
| ready_for_review / failed / published | revise(notes) | queued (auto-unpublish if published) |
| ready_for_review | publish | published |
| published | unpublish | ready_for_review |
| ready_for_review / published / failed | dismiss | dismissed (unpublish first if needed) |
| ready_for_review / dismissed / failed | delete | physical delete of link (+ guide if exclusive & not public) |

## API

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/v1/listening-diary/{id}/guides` | body `{aspect?}` → create queued guide from snapshot + link → **202** |
| GET | `/v1/listening-diary/{id}/guides` | owner: all links for post |
| GET | `/v1/listening-diary/guide-tasks` | owner: all diary-linked guide tasks (queue view) |
| POST | `/v1/listening-diary/guides/{link_id}/publish` | publish guide + set link `published` |
| POST | `/v1/listening-diary/guides/{link_id}/unpublish` | unpublish guide + link → `ready_for_review` |
| POST | `/v1/listening-diary/guides/{link_id}/revise` | body `{notes}` → store notes → recompose → `queued` |
| POST | `/v1/listening-diary/guides/{link_id}/dismiss` | mark dismissed (unpublish first if published) |
| POST | `/v1/listening-diary/guides/{link_id}/ack` | set `notified_at` (ack ready toast) |
| DELETE | `/v1/listening-diary/guides/{link_id}` | delete link; hard-delete guide if sole link & unpublished |

List/detail payload includes `review_notes`, `revised_at`, and derived
`actions: { can_publish, can_revise, can_unpublish, can_dismiss, can_delete }`.

Public diary / plaza detail includes `guides: [{…}]` **only published** links.

## Guide seed message

Built from Discogs snapshot: title, composers, performers, ensembles, year,
label/catno, aspect, Discogs URI, optional listening_note. Uses
`create_queued_guide` + listening_queue (SPEC-013).

Revise appends `Author revision notes:` to the guide message and calls
`enqueue_recompose_guide`.

## Acceptance

1. Enqueue returns 202 with `link.status=queued` and `guide_id`.
2. After guide `completed`, list tasks shows `ready_for_review`.
3. Publish → guide `published` + link `published`; plaza detail shows guide summary + share path.
4. Revise with notes → `queued` + `review_notes` persisted; after complete → `ready_for_review`.
5. Unpublish → plaza hides guide; link `ready_for_review`.
6. Delete removes link; exclusive unpublished guide row removed.
7. Unrelated user cannot enqueue/publish/revise/delete another's diary.
