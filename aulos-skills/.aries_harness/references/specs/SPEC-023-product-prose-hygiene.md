---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T18:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T18:30:00Z"
content_fingerprint: "sha256:18c3ac80d7328d9a028a8289947dff2404c571c72993036cc21cc9d941d5ba4e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-023 — Product-prose hygiene (cold path / bilingual / review)

Upstream: REQ-013. Complements SPEC-009, SPEC-018, SPEC-019, SPEC-022.

## Modules

| Module | Contract |
| --- | --- |
| `prose_hygiene.clean_packaging_work_title` | Discogs multi-lang / truncated packaging → listening-work title |
| `prose_hygiene.strip_process_locks` | Remove `CRITIQUE LOCK` / `REVIEW REPAIR` / critique-code prefixes |
| `prose_hygiene.partition_dossier_languages` | Move mostly-CJK EN fields into `zh`; scrub locks |
| `prose_hygiene.infer_form_label` | Replace "Large-scale work…" for miniature / cycle shelves |
| `prose_hygiene.strip_ambient_from_html` | Review HTML without ambient chrome |
| `prose_hygiene.looks_like_packaging_dump` | Drop packaging RAG bullets from width points |

## Pipeline hooks

1. **Discogs intake** — `_guess_work_title` runs `clean_packaging_work_title`.
2. **Synthesize / compose / revise_repair** — never pin process locks into thesis; park
   corrections in `myths_and_caveats`; call `partition_dossier_languages` before render.
3. **Depth cold path** — `infer_form_label` + miniature listening map when form matches.
4. **External review** — ambient-stripped HTML + chamber inventory; filter empty-body LLM
   claims when dossier is rich; deterministic hard flaws:
   `process_lock_in_product_prose`, `packaging_title_pollution`, `en_layer_cjk_pollution`,
   `form_scale_mismatch`.
5. **Score / scan** — `scan_hard_flaws` includes process-lock and packaging checks so v2
   cannot claim 0 flaws while locks remain in product HTML.

## Catalog / family floor

- Composer: `felix-mendelssohn`
- Work: `mendelssohn.lieder-ohne-worte`
- Family: `lyric-piano-miniatures` (form scaffold for Songs Without Words / lyric rooms)

## Acceptance gates

- `tests/test_prose_hygiene.py`
- `tests/test_external_review_hygiene.py`
- Regenerated guide #50: eval_pass true; no process locks in HTML; clean title; bilingual
  theses partitioned; form not large-scale.
