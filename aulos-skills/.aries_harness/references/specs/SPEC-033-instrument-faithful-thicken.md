---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T21:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T21:30:00Z"
content_fingerprint: "sha256:b52ae93596764a5654771f28a2afc62b938b4687cdf2293b3e315a97e2ac8940"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-033 — Instrument-faithful family match + multi-work intake

Implements REQ-023.

## 1. Family match soloist gate

`listening_enrich.synthesize._match_family`:

When `family.match.instruments` lists any **soloist-class** token (piano, violin,
cello, viola, oboe, flute, clarinet, horn, trumpet, guitar, voice / 钢琴·小提琴·
大提琴·中提琴·双簧管·长笛·单簧管·圆号·小号·吉他·人声), require ≥1 hit from that
soloist subset in the blob.

Ensemble-class tokens (orchestra, strings, choir / 管弦·弦乐·合唱) and form
tokens alone must **not** unlock the family.

If the blob already names a conflicting soloist (e.g. violin/oboe present, piano
absent) and the candidate family’s required soloist is piano (or vice versa),
refuse the match.

## 2. Chained catalog-number extraction

`identity_lock.extract_catalog_numbers` (or shared helper): when a prefix
(`BWV`, `K.`, `KV`, `Op.`, `Hob.`, …) is followed by a first number and then
separators (`•`, `/`, `,`, `and`, `und`, `·`) and bare subsequent numbers, emit
all siblings with the same prefix.

## 3. Discogs multi-work title

`discogs` intake / `_guess_work_title`: before collapsing to the “richest” single
track, extract catalog numbers from release title + tracklist. If ≥2 distinct
normalized catalog ids are present, return a program-level title that preserves
the release title (or a joined multi-work shelf), so IntentLock sees `multi_work`
rather than a single BWV/K./Op.

## 4. Product / process identity

`ProductScorecard` (or equivalent identity check): if IntentLock / title blob
locks non-piano solo scoring and draft/HTML heavily substitutes piano-concerto
rhetoric (or the inverse), emit a high/critical identity finding and fail closed
alongside existing composer-drift gates.

## 5. Facet (optional dimensional)

Prefer adding `violin-concerto` / `double-concerto` archetypes so instrument-
correct thickness can win without piano packs — still dimensional, not per-work.

## Tests

Cross-identity only (≥2 unrelated titles). No Grumiaux/Bach craft fixtures as
acceptance criteria names.
