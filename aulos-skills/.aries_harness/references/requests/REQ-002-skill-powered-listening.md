---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:dce043eb44a0285d0daba2d2fe4ca123d9da775e7fd785a5241753a03cdf91cb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-002 — Skill-powered classical listening (导赏) capability

## Why now

The listening-guide MVP proves the product moment, but research/compose logic is still hardcoded in `aulos-api`. Aulos’s durable advantage should come from **self-owned domain skills** in `aulos-skills`, continuously developed and loaded by the agent — not one-off prompts.

## Outcome

Aulos agent runs music 导赏 workflows by **discovering, selecting, and executing** domain skill packs from `aulos-skills`, with observable skill steps in the studio UI. New musical capabilities ship as skill packs first, then wire into the agent.

## Problem / anti-pattern today

- Guide quality lives in Python constants (`listening_guide.py`), hard to iterate by music/product experts
- Operator skills (`aulos-core`, etc.) serve coding agents, not the listening runtime
- No skill contract for inputs/outputs/eval, so capability growth is ad hoc

## Target capability model

Treat 导赏 as a **skill-orchestrated atelier**:

1. Intake skill — normalize work / listener intent  
2. Width skill — historical & cultural frame  
3. Depth skill — form, ear cues, listening map  
4. Compose skill — professional narrative + page design tokens  
5. Corpus skill — curated masterwork dossiers (Goldberg first)  
6. Eval skill — rubric for guide quality / hallucination risk  

## Non-goals (this request)

- Full marketplace publishing
- Replacing LLM providers
- Real-time audio alignment / score following (later)

## Acceptance (design phase)

- ARCH-002 + ADR-002 describe agent↔skills runtime contract
- Umbrella skill `aulos-listening` and at least one domain skill pack exist under `skills/`
- Clear next implementation slices for agent SkillLoader + workflow binding
