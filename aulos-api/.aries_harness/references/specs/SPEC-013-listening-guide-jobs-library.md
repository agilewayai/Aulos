---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T18:00:00Z"
effective_status: "active"
effective_since: "2026-07-26T18:00:00Z"
content_fingerprint: "sha256:d19cc75b85e44e2fb03d038a1a1444bcb0ad8c59bff3f377a91d082480332718"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-013 — Listening guide jobs + library

Upstream: REQ-009. Queue pattern mirrors SPEC-011 mail queue.

## Status machine

`queued` → `running` → `completed` | `failed`

Row created at enqueue with `message`, placeholder `work_title`, `steps_json=[]`.

## Endpoints

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/v1/listening-guides/jobs` | 202 enqueue compose |
| POST | `/v1/listening-guides/{id}/recompose/jobs` | 202 enqueue recompose |
| GET | `/v1/listening-guides/{id}/events` | SSE reconnect-safe (DB poll) |
| DELETE | `/v1/listening-guides/{id}` | owner hard-delete |
| POST/DELETE | `/v1/listening-guides/{id}/favorite` | set/clear `favorited_at` |
| PATCH | `/v1/listening-guides/{id}/tags` | replace `tags` array |
| GET | `/v1/listening-guides` | `q`, `status`, `published`, `favorited`, `tag`, `limit`, `offset` |

Legacy `POST …/stream` enqueues then attaches to job events.

## Columns

`message`, `error_detail`, `updated_at`, `favorited_at`, `tags_json`

## Worker

Redis `aulos:listening:queue` LPUSH/BRPOP; thread fallback when Redis unavailable. Persist steps on each `on_step`.

## Countable chain plan (progress)

Jobs seed a fixed plan in `steps_json` (gateway + expected agent skills). Each stage carries `index` / `total` and updates `pending → running → done|skip|failed`.

`GET …/events` emits `progress` snapshots whenever steps/status change (reconnect-safe; in-place updates visible).

## Robust recovery

- Client reconnects SSE with backoff and hydrates from `GET /{id}` between attempts.
- `POST /{id}/retry` re-queues `failed` or stale `running` (>20m) jobs with a fresh plan.
- Failed/timeout SSE errors include `retryable: true`.
