---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "eval"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T08:45:00Z"
effective_status: "active"
effective_since: "2026-07-27T08:45:00Z"
content_fingerprint: "sha256:6b0ad64633069818f9cde0e4d723fd31aa9e950cb9a4dea7a2a99637917602ec"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evaluation

## Gates

| Gate | Command | Expect |
| --- | --- | --- |
| Unit/API | `cd aulos-knowledge && .venv/bin/pytest -q` | all green |
| Admin auth | `tests/test_admin_auth.py` | 401 without bearer; 200 with token |
| Work-id RAG | `tests/test_work_id_rag.py` | retrieve hits match `aulos_work_id` |
| Source registry | `tests/test_source_registry.py` | unverified enqueue→400; URL policy; verify lifecycle |
| S2/S3 connectors | `tests/test_s2_s3_connectors.py` | wiki/imslp/rism mock ingest + chunk provenance |

## Security (AUDIT-009 F5)

- Direct `/v1/admin/*` without `Authorization: Bearer <AULOS_KNOWLEDGE_ADMIN_TOKEN>` → 401
- Token unset → 503 on admin routes
- API ops proxy forwards the same bearer token

## Authority registry (REQ-008)

- Unverified / unknown / connector-missing sources cannot enqueue jobs
- Fetch URLs outside registered `base_urls` fail
- Retrieve only returns `published` documents
