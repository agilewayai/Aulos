---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "task-stack"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T16:20:00Z"
content_fingerprint: "sha256:8b423c9bdc47b401fff8fd47d82727814a326d0d319dec7e70275a6b7f680e5e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Task Stack

## Now

- SPEC-034 Slice G shipped and deployed — multi-work guide sheets + synthesis
  fan-in: multi-work Discogs programs render one navigable work sheet per
  program work plus one synthesis/overview sheet; skill output exposes
  `guide_sheets[]` and a deterministic `program_parallel_plan` so later gateway
  workers can fan out per-work deepen safely and fan in to synthesis.
- SPEC-034 Slice F shipped and deployed — program fold-back hard gate for guide #59
  (`/discogs #7083684`, Hummel / Weber / Haydn piano-flute-cello trios):
  per-work composers propagate into `g.program`; final program-loop subject
  scalars override generic album/family layers; API failed eval gates persist as
  `failed` and cannot publish. Live guide #59 recompose remains pending.
- SPEC-034 / REQ-024 Discogs release-structure-first: Slices A–C shipped (emit + gate + program expand).
- SPEC-033 / REQ-023 Instrument-faithful thicken + multi-work Discogs shipped (anti-case; soloist gate / chained catalog nums / program title).
- SPEC-032 / REQ-022 Identity freeze + Catalog/facet hardening shipped (anti-case; probe class from multi-Köchel piano pressing).
- SPEC-031 / REQ-021 Dimensional thicken + promote-to-production shipped (anti-case; META-001 v6).
- SPEC-030 / REQ-020 Promote staging + ops surface shipped (staging craft write; Guide quality Stage).
- SPEC-029 / REQ-019 Unknown-Case Thicken Loop v1 shipped (FacetClassifier + archetype floor + promote dry-run).
- SPEC-028 / REQ-018 Catalog craft coverage + fleet dossier ensure shipped (10/10 craft; Dvořák dossier built).
- SPEC-027 / REQ-017 genre family coverage shipped (concerto/requiem/symphony/trio + Catalog lock).
- SPEC-026 / REQ-016 systemic cold-path thicken shipped (catalog floor + auto dossier + asset_depth).
- SPEC-025 / REQ-015 knowledge thicken + ProductScorecard shipped; guide #50 product 100% strong.
- SPEC-023 / REQ-013 product-prose hygiene shipped; guide #50 regen evaluated.
- SPEC-006Δ ambient fallback shipped (library rotation off; OPS embed|stream).
- SPEC-019 process scorecard + SPEC-018 adversarial review shipped.
- AUDIT-009 F2/F3/F10/F11 closed in code; F1 deferred to operator secret rotation.
- SPEC-009 decontam + family evidence gate shipped (Brahms Op.77 regression green)
- Keep SPEC-first + TDD on next listening-product slice (open RUN-* first)

## Next

- Recompose thin multi-work guides (STORY-PACK-002 Slice E) under SPEC-034 gates
- STORY-PACK-002 Slice D: Ops/聆乐 program-map chips after sheet contract lands
- Expand dimension voice tables from live Discogs facet histograms (dimensional only)
- Knowledge-plane auto-thicken after promote-production
- Recompose/patch historical guides that still embed Moonlight stand-in ambient (e.g. #48) after deploy
- Phase-2: gateway-stage scorecards + fleet adversarial review beyond listening atelier
- Deeper F10: split `listening_guide.py` / `runtime.py` / remaining ops App tabs when next touched

## Later

- Encryption-at-rest for `SystemSetting` secrets (post Sprint-1; see ADR-008)
- Align consumer facility layout with upstream `aries-harness-skills` docs if they add `.aries_harness/scripts` packaging
- Richer observability and production rollout

## Blocked

- (none for local iteration; F1 live rotation optional/deferred)
