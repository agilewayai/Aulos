# Worker / job execution (aulos-knowledge)

## Async default (META-001 §3.3)

Crawl / ingest jobs are **long-running work**. HTTP must not block on connectors.

1. `POST /v1/admin/jobs` creates a durable `fetch_jobs` row (`queued`).
2. When `AULOS_KNOWLEDGE_SYNC_JOBS=false` (production) **or** `?async=true`:
   - Response is **202** with `{ id, status: queued|running, async: true }`.
   - A **background thread** runs `run_job` (same process); a drain loop picks up
     orphaned `queued` rows after restart.
3. OPS / clients **poll** `GET /v1/admin/jobs/{id}` (or the jobs list) until
   `succeeded` | `failed`.

State machine: `queued` → `running` → `succeeded` | `failed`.

## Sync escape hatch (CI / local smoke only)

`AULOS_KNOWLEDGE_SYNC_JOBS=true` runs connectors **in-process** immediately after
enqueue (`enqueue_and_maybe_run` → `run_job`) and returns **200**. Use for pytest
and quick OPS smoke — **not** as the production UX path.

## Architecture

| Layer | Role |
| --- | --- |
| `fetch_jobs` table | Durable queue + audit |
| `job_queue.dispatch_job` | Daemon thread per job |
| `job_queue` drain loop | Lifespan background: reclaim stuck `queued` |
| Future ARQ / Redis | Optional multi-process scale-out (`REDIS_URL`) — same state machine |

## Retry / failure contract

| Case | HTTP / job status | `error` field |
| --- | --- | --- |
| Unknown source | **400** — job not created | n/a |
| Disabled / unverified source at enqueue | **400** — job not created | n/a |
| Source disabled mid-flight | job `failed` | message |
| Connector exception | job `failed` | exception text (≤2000 chars) |
| Success | job `succeeded` | empty |

Re-enqueue is the retry mechanism: create a new job for the same `source_id` after
fixing enablement / params. There is no automatic retry loop.

## Ops checklist

1. Confirm source `verified` + `enabled` before enqueue.
2. After enqueue, watch Jobs module for `queued` → `running` → `succeeded`.
3. If `failed`, read `error` and fix source / params, then re-enqueue.
4. Quarantine bad published docs via `/v1/admin/documents/{id}/quarantine`.
