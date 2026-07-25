---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:01:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:01:00+00:00"
content_fingerprint: "sha256:26656052723405f0ff8455126c738a733dba576a64176e837da7978e5f7a2cf2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-008 — Work Identity Catalog & Identity Resolver

## Authority

Canonical catalog lives under:

`aulos-listening-corpus/assets/catalog/`

- `composers/<composer_id>.yaml`
- `works/<work_id>.yaml`
- `index.yaml`
- `policies/weak_tokens.yaml`

Runtime must **not** hardcode work-specific identity branches (`elif "goldberg"`,
`elif "cello"`, Chopin/Mahler name checks, etc.). New works = new catalog records.

## Work record schema (minimum)

| Field | Required | Notes |
| --- | --- | --- |
| `work_id` | yes | Stable dotted id |
| `composer_id` | yes | FK to composer card |
| `canonical_title` / `canonical_title_zh` | yes | Professional titles |
| `aliases[]` | yes | EN/ZH query surface |
| `catalog_numbers[]` | yes when known | BWV / Op. / … |
| `facets.instruments/ensemble/forms/era` | yes | Identity dimensions |
| `family_id` | optional | Scaffold shelf |
| `corpus_key` | optional | Full dossier key when present |
| `ambient_ref` | optional | Ambient library entry id |
| `identity.distinctive_tokens[]` | yes | Non-weak tokens that prove this work |
| `identity.conflict_work_ids[]` | recommended | Works that must not leak into this shelf |
| `provenance` | yes | Authority + uncertainty notes |

## Resolver contract

`IdentityResolver.resolve(query, work_hint="")` returns one of:

- `status=work` — matched `work_id`, `confidence`, `family_id`, `corpus_keys`,
  `conflict_markers` (derived from conflict works' distinctive tokens ∪ markers)
- `status=composer_only` — composer aliases hit, no distinctive work win
- `status=ambiguous` — multiple works tied without distinctive winner
- `status=unknown`

Scoring (generic for all composers):

1. Alias / catalog_number / distinctive_token / facet overlap
2. Weak tokens from `policies/weak_tokens.yaml` never award distinctive points
3. Same-composer multi-work requires distinctive/catalog/facet victory

## Downstream wiring

| Stage | Rule |
| --- | --- |
| Intake | Call Resolver only; emit `work_id`, `family_hints`, `corpus_keys`, `conflict_markers` |
| RAG | Attach `kb_dossier` only when doc `work_id`/`corpus_key` matches resolved identity |
| Scrub | Use `conflict_markers` from context — no hardcoded flagship tuples |
| Ambient | Prefer `ambient_ref`; else facet instrument intersection; drop curated packs that carry conflict markers |

## Acceptance

- Bach cello suites resolve to `bach.cello-suites.bwv-1007-1012`, not Goldberg.
- Chopin / Mahler catalog slots resolve without any Chopin/Mahler Python branches.
- Adding a new work YAML requires **zero** Resolver code changes for identity.
- Code review gate: no new work-proper-name `elif` in `runtime.py` / `ambient_agent.py`.
