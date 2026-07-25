---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "managed-doc"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:45:00Z"
effective_status: "active"
effective_since: "2026-07-25T16:45:00Z"
content_fingerprint: "sha256:89c6671db5dc45150b8aa2e9eede134dd2f4a2407c45f2ab7782f3a86cecbb52"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evolution cycle — Harness process, facility layout, canonical source

date: 2026-07-25
source_findings:
  - AUDIT-001: listening-product work landed code-first; SPEC/TDD/RUN late or missing
  - Facility scripts/templates sat at project-root `scripts/` + `templates/` (looked like product code)
  - AGENTS/CLAUDE treated aries-harness as soft preference, not forced default
  - Risk of pulling obsolete `AriesHarnessStudio` / `aries-studio` instead of `aries-harness-skills`

## Triggering signal

Operator asked to (1) mandate Aries Harness in charter files, (2) put facility assets under
`.aries_harness/`, (3) confirm canonical library is `agilewayai/aries-harness-skills`, then
close the day with well-organized + history-refresh + self-evolution promotion.

## Repeated finding / pattern

1. **Chat-shipped product work without harness artifacts** → future agents cannot resume gates.
2. **Harness tooling leaked outside `.aries_harness/`** → polluted package roots; wrong mental model.
3. **Soft process language** → agents skip SPEC/TDD unless forced.
4. **Ambiguous library provenance** → old studio clones still on disk; easy to cite the wrong repo.

## Evidence from recent runs

- AUDIT-001 report under `runs/reports/`
- Fleet AGENTS.md / CLAUDE.md rewritten with “mandatory default (forced)”
- Facility move: all six `aulos-*` projects now have `.aries_harness/scripts/` + `templates/`;
  project-root `scripts/` / `templates/` removed
- Script content (path-normalized) matches `aries-harness-skills` `0.10.0-preview.10`;
  differs from obsolete `AriesHarnessStudio` (`runs-inspect` missing; older `memory-inspect`)
- Cursor `aries-harness*` SKILL.md set: 20/20 identical to `aries-harness-skills`
- Smoke: `history-status` / `memory-inspect` / `well-organized` via
  `bash .aries_harness/scripts/aries-harness.sh …`

## Future behavior that should improve

- Open REQ/SPEC (or delta) + RUN before broad listening-product edits
- Invoke harness CLI only from `.aries_harness/scripts/`
- Treat `agilewayai/aries-harness-skills` as the only library source; ignore studio clones
- End slices with well-organized + history-refresh + insight/evolution when lessons are strategic

## Promotion targets

| Finding | Durable asset | Status |
| --- | --- | --- |
| Soft harness preference | Fleet AGENTS/CLAUDE + operating-defaults 0.3.x | done |
| Facility pollution | `.aries_harness/{scripts,templates}` + README facility section + ARCH-001 note | done |
| Chat-only incomplete | operating-defaults non-negotiable loop + AUDIT-001 | done |
| Wrong library source | insights.md + MEMORY + this evolution memo | done |
| Closeout discipline | TASK_STACK / STATE + today history refresh | in progress |

## Before → after (measured)

| Metric | Before | After |
| --- | --- | --- |
| Charter wording | “prefer / work under harness” | “mandatory default (forced)” in workspace + 6 packages |
| Facility path | `scripts/aries-harness`, `templates/aries_harness` at package root | `.aries_harness/scripts`, `.aries_harness/templates` |
| Root `scripts/` / `templates/` dirs | present (harness-only) | absent |
| Script lineage vs skills repo | unverified | path-normalized equal to `aries-harness-skills` |
| Script lineage vs AriesHarnessStudio | — | diverged (not source of truth) |
| Invoke smoke (`history-status`) | old path | new path exit 0 |

## What stays in insights only

- Day-of narrative color; one-off path typos while migrating.

## What became reusable family behavior

- Forced harness loop in operating-defaults
- Facility layout rule for every `aulos-*` bootstrap
- Canonical library pin: `git@github.com:agilewayai/aries-harness-skills.git`

## Remaining uncertainty

- Upstream skills library still packages tooling at repo-root `scripts/aries-harness/`
  (library layout). Consumer projects keep the `.aries_harness/scripts/` policy until
  upstream documents a consumer facility layout.
- Formal RUN-* template adoption still later (TASK_STACK).

## Next-run behavior change

Agents reading AGENTS / MEMORY / operating-defaults will: refuse chat-only closeout,
call `.aries_harness/scripts/aries-harness.sh`, and never treat studio repos as harness source.
