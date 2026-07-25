# Worker / job execution (aulos-knowledge)

## Default: sync-only (dev)

`AULOS_KNOWLEDGE_SYNC_JOBS=true` (default) runs connectors **in-process** immediately
after enqueue (`enqueue_and_maybe_run` → `run_job`). No Redis/ARQ required for local
smoke and OPS “Import catalog” clicks.

## Async path (future ARQ)

When `AULOS_KNOWLEDGE_SYNC_JOBS=false`:

1. `POST /v1/admin/jobs` creates a row with `status=queued` and returns without running.
2. An ARQ (or equivalent) worker should call `run_job(db, job_id)` for queued rows.
3. Until a worker exists, jobs remain `queued` — OPS will show that status.

There is **no ARQ stub process** in this repo yet; production deploy should either keep
sync jobs behind a dedicated worker process that shares the knowledge DB, or add ARQ
and point `REDIS_URL` at the compose stack.

## Retry / failure contract

| Case | HTTP / job status | `error` field |
| --- | --- | --- |
| Unknown source | **400** — job not created | n/a |
| Disabled source at enqueue | **400** — job not created | n/a |
| Source disabled mid-flight | job `failed` | `source missing or disabled` |
| Connector exception | job `failed` | exception text (≤2000 chars) |
| Success | job `succeeded` | empty |

Re-enqueue is the retry mechanism: create a new job for the same `source_id` after
fixing enablement / params. There is no automatic retry loop in-process.

## Ops checklist

1. Confirm source `enabled=true` before enqueue.
2. If status=`failed`, open job detail / list `error` and fix source or params.
3. Quarantine bad published docs via `/v1/admin/documents/{id}/quarantine`.
