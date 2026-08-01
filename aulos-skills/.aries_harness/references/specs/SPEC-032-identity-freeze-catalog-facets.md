---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:50:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:50:00Z"
content_fingerprint: "sha256:b7054c8d51552ce4f211d5d9749be56ebfa9a2b72e3e30ec3e481f7952c19095"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-032 — Identity freeze + Catalog/facet hardening

Upstream: REQ-022. Extends SPEC-008 / SPEC-009 / SPEC-029. **Anti-case.**

## Alias token boundary

Shared helper (e.g. `alias_in_text(alias, blob)`):

- Aliases with length ≥ 2 match as whole tokens (Unicode letter/digit boundaries),
  not raw `alias in blob` substrings.
- Applies to: synthesize `_match_composer_card`, IdentityResolver `_match_composer`,
  and short numeric `distinctive_tokens` (digit-only tokens must not match inside
  longer digit runs such as Discogs release ids).

## IntentLock composer freeze (synthesize)

Order of truth for dossier composer:

1. `intent_lock.composer` when non-empty
2. else intake `composer` / `composer_guess`
3. else composer-card name **only if** card aliases match the locked/intake composer
   (card must not replace a different locked name)

If a card matches the blob only via performer pollution, ignore the card.

## Catalog number scoring

In `IdentityResolver._score_work`:

- Exact / compact catalog-number match unchanged (strong path).
- `catalog-tok` path: intersection must include a token containing a digit;
  bare prefix tokens (`kv`, `k`, `op`, `bwv`, `hob`, …) alone never score.
- When the query extracts ≥1 normalized catalog number via `extract_catalog_numbers`
  and none intersect the work’s normalized numbers, do not award catalog-tok /
  weak facet-only wins that would invent a sibling work (score those paths at 0
  for that work when query numbers are present and disjoint).

In `resolve`:

- If query has ≥2 distinct catalog numbers and no work wins via exact catalog /
  strong alias (≥45 catalog or alias reason), return `composer_only` (or status
  `multi_work` with `work_id=None`) with reason `multi_catalog_numbers` — never a
  false `ambiguous` tie between unrelated Catalog works.

## FacetClassifier

- Form tokens: add common spellings `sonate`, `sonaten`, `rondo`, `rondos`, `rondò`,
  and 回旋曲 where missing.
- New archetype `solo-piano-sonata`: requires piano (+ soft infer) and form
  `sonata` and/or `rondo`; must outrank duo when cello is absent.
- `duo-cello-piano` rule: require **cello** in instruments (no soft piano-only
  unlock on sonata alone).
- Soft piano_family set includes `solo-piano-sonata`.

## Form-lock policy

Add `solo_keyboard` (or `piano_sonata`) family anchors: sonata/sonaten/奏鸣 +
keyboard/piano cues; aliens include orchestra/concerto/requiem/cello-duo rhetoric
when anchors hit without chamber ensemble cues.

## Promote candidate gate

`build_promote_candidate(..., *, locked_composer=None, allow=True)`:

- Return `None` when `allow` is False.
- Return `None` when `locked_composer` is set and normalizes unequal to dossier /
  argument composer.
- Runtime: pass `allow=False` when `review_failed` or `decontam_failed`; pass
  IntentLock composer as `locked_composer`.

## ProductScorecard identity

- If `intent_lock.composer` and final composer disagree → identity_clarity ≤ 0
  and high finding `product_composer_drift`.
- Packaging titles with multi-work separators alone do not grant full identity
  credit without composer lock agreement.
