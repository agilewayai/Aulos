---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T10:30:00Z"
effective_status: "active"
effective_since: "2026-07-27T10:30:00Z"
content_fingerprint: "sha256:7968c856251bfec396edda6e39f26ab02d69c536b35e03e50039926ecd212a9e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-018 — Ops background task queue + dashboard

Upstream: operator request — slow Ops jobs (dev blog generate/regenerate) must not block HTTP; unified visibility by task type and source.

## Goals

1. Enqueue long-running Ops work instead of holding the request open.
2. Durable task rows in Postgres (`ops_tasks`) + Redis queue `aulos:ops:tasks:queue`.
3. Ops portal **Tasks** tab: queue depth, worker status, filterable task list, payload/result detail.
4. Dashboard aggregates mail + listening + ops queues for a single pane.

## Status machine

`queued` → `running` → `completed` | `failed`

## Task types (initial)

| task_type | source | Handler |
| --- | --- | --- |
| `dev_blog.generate` | `ops.dev_blog` | `dev_blog.generate_post` |

## API

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/v1/ops/dev-blog/{day}/generate` | **202** `{ task_id, status, task_type, source, post_id? }` |
| GET | `/v1/ops/tasks/dashboard` | superadmin — queues + recent + counts |
| GET | `/v1/ops/tasks` | filters: `status`, `task_type`, `source`, `limit` |
| GET | `/v1/ops/tasks/{id}` | single row |

## Settings

- `AULOS_TASK_QUEUE_ENABLED` (default true) — worker + Redis enqueue
- `AULOS_TASK_QUEUE_SYNC` (default false) — run inline in request thread (tests)

## Worker

Thread worker started in app lifespan (`start_task_worker`). BRPOP Redis queue; on miss or no Redis, poll DB for `queued` rows.

## Schema

`ops_tasks`: `task_type`, `source`, `status`, `payload_json`, `result_json`, `error_detail`, `created_by_user_id`, timestamps. Patch: `apply_ops_tasks_patches`.

## Ops UI (`aulos-ops`)

- Tab **Tasks** — `TaskQueuePanel.tsx`
- Dev Blog generate/regenerate polls `GET /tasks/{id}` (sync mode returns completed immediately)

## Tests

- `tests/test_task_queue.py`
- `tests/test_dev_blog.py` (202 + sync)

## Future

Migrate other slow Ops endpoints into `task_queue.enqueue` with new `task_type` + handler registrations.
