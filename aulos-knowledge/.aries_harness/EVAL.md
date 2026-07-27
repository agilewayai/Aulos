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
content_fingerprint: "sha256:e5c9ce39e242e0297b048dddb21013b3e9ad1656859017d6e6b2a1de4e6a0c51"
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

## Security (AUDIT-009 F5)

- Direct `/v1/admin/*` without `Authorization: Bearer <AULOS_KNOWLEDGE_ADMIN_TOKEN>` → 401
- Token unset → 503 on admin routes
- API ops proxy forwards the same bearer token
