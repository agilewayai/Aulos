---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "story-pack"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T22:10:00Z"
effective_status: "active"
effective_since: "2026-08-01T22:10:00Z"
content_fingerprint: "sha256:9555070ae40037b105148868fc713348892d228060daf37bb28aac5e3ef4e2f0"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# STORY-PACK-002 — Discogs release structure meta harness

Upstream: REQ-024 / SPEC-034 / ARCH-002 / ADR-006 / META-001 §4.1

## Slice A — Structure domain + emit (done)

- `release_structure.py` + tests
- Discogs analyze + diary snapshot emit `release_structure`
- META/REQ/SPEC/ADR/ARCH/DOM registered

**Verify:** skills `test_release_structure.py`; API `test_analyze_emits_release_structure_program`

## Slice B — Runtime hard-gate (done)

- Intake lifts `release_structure`; IntentLock merges program catalogs
- `apply_structure_gate` → `refuse_families` when multi-work not ready
- Process scorecard identity hard-fails `release_structure_not_ready`
- Gateway persists `release_structure` / `structure_hard_fails` / `program_expand_applied` in `research_json`
- Trace milestone `discogs.structure`

## Slice C — Per-work expand orchestration (done v1)

- `build_program_expand_dossier` builds per-work `listening_map` + `variation_deepdives` (+ zh)
- Synthesize inserts `release-program-expand` layer after family floor
- Pressing-level interpretations / vinyl from Discogs credits
- Tests: multi-BWV + multi-Köchel program expand (no case craft)

## Slice CΔ — Iterative / recursive program deepen (done)

- Gateway `g.program` loops program works (force web + LLM → `program_iterations`)
- Web: `force_action` + partial `rag_hits` on verify_failed (no hard community skip)
- Album `g.web` → `delegated_to_program_loop`
- Synthesize folds `release-program-loop`; strips generic family map cues
- META-001 v8 §4.1 stage 4; ARCH-002 Layer 2 rewritten as loop

## Slice D — Operator visibility (later)

- Ops / 聆乐 show program map chips before generate
- Structure gaps surfaced in atelier trail

## Slice E — Live recompose (optional next)

- Recompose thin multi-work guides (e.g. Bach violin concertos pressing) after deploy

## Slice F — Program fold-back hard gate (active 2026-08-02)

- Fix guide `#59` class: program loop evidence must own final subject, not be
  overwritten by album LLM / family scaffold.
- Carry composer attribution into program works when release-level composer-like
  artists positionally match program count.
- Persist failed quality gates as failed/diagnostic, not completed/ready.
- Tests: skills program-fold regression + API failed-eval persist gate.
