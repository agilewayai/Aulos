---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:10:00Z"
effective_status: "active"
effective_since: "2026-07-25T17:10:00Z"
content_fingerprint: "sha256:700ab4d1a49654e44f84a5c31de447a3e4cd94a891f7c8af8fe2871e2ee44ae1"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-002 — Agent-orchestrated listening run

## Behavior

`run_listening_via_agent` (in-process) and optional `POST /v1/listening/run`:

Request context:

```json
{
  "message": "string",
  "work_hint": "string?",
  "llm_enrichment": "string?",
  "llm_dossier": {},
  "kb_dossier": {},
  "rag_hits": [],
  "rag_mode": "string?",
  "disabled_skill_ids": []
}
```

Response:

```json
{
  "steps": [ { "id", "title", "status", "thinking", "detail", "skill_id", "skill_version", "started_at", "finished_at" } ],
  "guide_html": "string",
  "summary": "string",
  "work_title": "string",
  "composer": "string",
  "eval_pass": true,
  "eval_score": 0,
  "skill_versions": {},
  "context": {},
  "source": "agent-skills"
}
```

## Tool contract

1. Agent must call `run_listening_skill` for each trigger in the playbook order from `aulos-listening` SKILL.md (route → intake → corpus → synthesize → width → depth → compose → eval).
2. Each tool result returns `{ "step": {...}, "context": {...} }`; context accumulates.
3. Product path must not use `run_listening_skill_chain`.

## Offline

`AULOS_LLM_PROVIDER=fake` uses `ListeningPlaybookFakeModel` to emit the trigger sequence deterministically.

## Verification

- Registry includes `run_listening_skill` (+ `list_aulos_skills`).
- Fake agent run on Goldberg message yields steps with skill_ids, guide_html, ambient needles.
