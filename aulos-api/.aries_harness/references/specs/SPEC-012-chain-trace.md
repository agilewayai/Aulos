---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T17:15:00Z"
effective_status: "active"
effective_since: "2026-07-26T17:15:00Z"
content_fingerprint: "sha256:c05962901bead86136953e33154826b1229987c1c00ff52bdbb9a764b025423a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-012 — Listening chain diagnostic log (复盘 trace)

Upstream: Mozart→Beethoven pollution postmortem; observability skill.

## Outcome

Every listening-guide generation (compose + recompose) persists a structured
**chain_trace** so operators can retrospectively see *which milestone* first
diverged (identity, Discogs lock, RAG, synthesize family, LLM, compose).

## Storage

- Persist under `listening_guides.research_json.chain_trace` (no new table for MVP).
- Schema id: `aulos.chain_trace/v1`.
- Keep payload bounded (truncate long strings; no full HTML; no raw LLM dump > 1.5k chars).

## Trace shape (normative)

```json
{
  "schema": "aulos.chain_trace/v1",
  "trace_id": "uuid",
  "started_at": "…Z",
  "finished_at": "…Z",
  "input": { "message": "…", "work_hint": "…" },
  "identity_arc": [
    { "stage": "input|discogs|catalog|locked|final", "composer": "", "work_title": "", "work_id": null }
  ],
  "milestones": [
    {
      "id": "discogs.resolve|identity.resolve|identity.lock|rag|web_research|llm_enrich|skill.intake|skill.synthesize|skill.compose|persist",
      "status": "ok|skip|warn|fail",
      "at": "…Z",
      "summary": "one-line operator English",
      "facts": {},
      "signals": ["optional.machine.code"]
    }
  ],
  "deviations": [
    {
      "code": "composer_drift|title_drift|family_without_work_id|synthesize_foreign_family",
      "at_milestone": "skill.synthesize",
      "summary": "…",
      "facts": {}
    }
  ]
}
```

## Gateway behavior

1. `_run_chain_core` builds a `ChainTraceBuilder` for the request.
2. Record Discogs resolve/skip, Catalog identity, Discogs lock overrides, RAG mode,
   web research meta, LLM enrich source, then skill-reported diagnostics from
   `report.context` (`synthesize_source`, `identity_status`, `family_hints`, …).
3. After final report: compare identity_arc stages → append `deviations` when
   locked/discogs composer|title drifts from final, or synthesize attaches a
   `family:*` source without a Catalog `work_id`.
4. Persist via existing `_research_payload` → `research_json`.

## Read APIs

| Route | Auth | Purpose |
| --- | --- | --- |
| `GET /v1/listening-guides/{id}/trace` | owner | Studio / owner 复盘 |
| `GET /v1/ops/listening-guides/{id}/trace` | ops | Fleet diagnosis |

Response: `{ "guide_id", "work_title", "composer", "created_at", "chain_trace" }`.
404 when guide missing / not owned (owner route). Empty `chain_trace: null` for
pre-SPEC-012 rows.

## Non-goals

- Full prompt/completion archival
- Streaming partial traces mid-SSE (MVP persists at done)
- Replacing `steps_json` UI trail (trace is diagnostic sibling)

## Acceptance

1. Fake-agent compose persists `chain_trace.schema == aulos.chain_trace/v1` with ≥1 milestone.
2. Discogs mocked compose includes `discogs.resolve` + identity_arc stage `discogs`/`locked`.
3. Owner `GET …/trace` returns the same object; unauthenticated → 401.
4. Ops route returns trace for any guide id (ops auth).
5. Deviation helper flags `family_without_work_id` when synthesize_source has `family:` and work_id empty.
