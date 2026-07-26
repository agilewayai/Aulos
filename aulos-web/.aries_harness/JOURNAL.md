---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "journal"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:42Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:42Z"
content_fingerprint: "sha256:3b6c0356b2839af42f74423aaf12a3f73f57c78b012da07283678d1c3c72180c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Journal

## 2026-07-26T16:50:00Z

- SPEC-002: Forgot password + reset UI (`forgot` / `reset` modes, `/?reset_token=`)
- API clients: `forgotPassword` / `resetPassword`
- Verify: `npm run build` green; upstream `pytest tests/test_auth.py` 7 passed

## 2026-07-25T17:00:00Z

- Added ``src/time.ts``; guide history/meta show OS-local timestamps

## 2026-07-25T11:07:42Z

- initialized `.aries_harness/`
- wrote `ARIES_HARNESS_FINGERPRINT.json`
- no execution history recorded yet
