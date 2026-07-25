---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:7e3dc385c478d9cc7e025a20d8203149f5bfa84ea55c1b684d43caff82a4a120"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ARCH-002 — Agent × Aulos Skills for music 导赏

## Document Control

- Architecture ID: ARCH-002
- Title: Skill-runtime architecture for classical listening guides
- Status: proposed → active (design baseline)
- Related: REQ-002, ADR-002, SPEC-003 (aulos-api listening guide)

## Design drivers

1. **Capability compounds in skills, not in chat prompts** — music knowledge, research method, and guide craft live in versioned skill packs.
2. **Agent is an orchestrator** — selects skills, runs procedures, emits observable steps, renders artifacts.
3. **Same pack serves humans and machines** — `SKILL.md` is readable by operators; structured sections are executable by the agent.
4. **Offline-first** — curated corpus + fake LLM still produce excellent guides; live LLM enriches.

## Two skill classes (do not conflate)

| Class | Audience | Examples | Runtime |
| --- | --- | --- | --- |
| **Operator / harness skills** | Coding agents & humans developing Aulos | `aulos-core`, `aulos-operating-defaults` | Cursor / CLI |
| **Domain / runtime skills** | Aulos listening agent at product runtime | `aulos-listening-*` | `aulos-agent` / `aulos-api` SkillRuntime |

REQ-002 expands the second class without abandoning the first.

## Target topology

```text
Listener (aulos-web studio)
        │
        ▼
   aulos-api  listening workflow
        │  loads manifests via aulos_skills.registry
        ▼
   SkillRuntime
        ├─ resolve triggers → skill packs
        ├─ inject references/ + corpus assets
        ├─ call tools (corpus, LLM, MCP)
        └─ emit WorkflowStep[] (observable)
        │
        ▼
   Guide artifact (HTML) + eval score
```

Optional later: `aulos-mcp` exposes `skills.list` / `skills.run` so external hosts can reuse the same packs.

## Skill pack contract (domain-runtime)

```text
skills/aulos-listening-<facet>/
  skill.yaml          # id, layer=domain-runtime, triggers, io schema
  SKILL.md            # procedure the agent must follow
  references/         # method notes, source ladders, anti-patterns
  assets/
    templates/        # prompt shapes, HTML section templates
    corpus/           # optional curated dossiers (JSON/MD)
  eval/
    rubric.md         # what “good 导赏” means for this facet
```

### `skill.yaml` fields (additive)

- `layer: domain-runtime`
- `runtime: agent`
- `triggers: [listening.intake | listening.width | …]`
- `inputs` / `outputs` (named dossier keys)
- `depends_on` (other skill ids)
- `observability_title` (shown in studio chain-of-thought)

### `SKILL.md` sections the SkillRuntime parses

1. **When to use** — trigger heuristics  
2. **Procedure** — ordered steps (become workflow thinking)  
3. **Research questions** — width vs depth question banks  
4. **Output schema** — fields that must appear in the dossier  
5. **Anti-patterns** — myths-as-facts, vague adjectives, spoilers without ear cues  
6. **Handoff** — what the next skill needs  

## How the agent uses skills (runtime loop)

```text
1. Intent → match triggers (intake skill)
2. Plan   → build skill chain from depends_on + umbrella router
3. Load   → SKILL.md + references + corpus slice into context pack
4. Act    → for each skill:
            - emit step.start(thinking from procedure)
            - retrieve corpus / call LLM with skill templates
            - validate output schema
            - emit step.complete(detail = structured summary)
5. Compose → listening-compose skill renders HTML from dossiers
6. Eval    → listening-eval scores; fail → retry compose or flag gaps
7. Persist → guide + skill trace (which skill versions ran)
```

### Context packing rule

Never dump all skills into the LLM. Pack only:

- umbrella router summary
- active skill `SKILL.md` procedure
- relevant `references/` excerpts
- matching corpus entry (e.g. Goldberg)
- prior dossier outputs (width → depth)

This mirrors aries-harness-context: sharp context beats bloated context.

## Umbrella skill map (proposed family)

| Skill id | Role in 导赏 |
| --- | --- |
| `aulos-listening` | Router: choose chain, define quality bar |
| `aulos-listening-intake` | Normalize work title, listener goal, experience level |
| `aulos-listening-width` | Era, patronage, reception, myth vs evidence |
| `aulos-listening-depth` | Form, section map, ear cues, practice listening |
| `aulos-listening-corpus` | Curated masterwork packs; offline excellence |
| `aulos-listening-compose` | Narrative voice + beautiful page structure |
| `aulos-listening-eval` | Rubric: specificity, ear-actionability, source hygiene |

## Development flywheel (how skills make us stronger)

```text
Studio session / eval fail
        │
        ▼
aulos-skills (TDD + harness)
  - improve SKILL procedure
  - add corpus dossier
  - tighten rubric
        │
        ▼
registry version bump
        │
        ▼
agent loads new pack → better guides
        │
        ▼
observability shows which skill version produced the guide
```

Operator coding agents use **`aulos-core` + `aulos-operating-defaults`** to develop these domain skills (REQ/SPEC/TDD). Product runtime uses **domain-runtime** skills. Same repo, two layers.

## Integration seams

| Seam | Contract |
| --- | --- |
| `aulos-skills` → `aulos-api` | Python import of `discover_skills` + SkillRuntime |
| `aulos-skills` → `aulos-agent` | Tool: `load_skill` / `run_skill_step`; graph nodes per trigger |
| `aulos-skills` → `aulos-mcp` | MCP tools wrapping skill list/run (phase 2) |
| `aulos-web` | Already shows WorkflowStep[]; map `step.id` to skill trigger |
| `aulos-ops` | Later: enable skill packs, view skill versions, eval scores |

## Migration from current MVP

1. Keep `listening_guide.py` as temporary orchestrator  
2. Move Goldberg dossier → `aulos-listening-corpus/assets/corpus/bwv-988.*`  
3. Replace hardcoded width/depth/copy with skill procedures  
4. Record `skill_versions` on `ListeningGuide` rows  
5. Delete hardcoded prose once skill path is green under pytest  

## Risks

- Skill sprawl without eval → mitigate with `aulos-listening-eval` gate  
- Context bloat → strict packing policy  
- Myth amplification (e.g. Keyserlingk legend) → width skill anti-patterns + corpus footnotes  

## Open decisions

- Sync vs streaming skill steps (SSE) for studio  
- Whether corpus is git-versioned only or also ops-editable  
