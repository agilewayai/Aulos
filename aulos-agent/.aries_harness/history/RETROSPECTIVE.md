---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "history-retrospective"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T10:55:22Z"
generated_at: "2026-08-01T20:59:39+00:00"
effective_status: "generated"
effective_since: "2026-08-01T20:59:39+00:00"
content_fingerprint: "sha256:786130592e7d66f15011d3b071f95ac0bf3418932d8ccb7684bf7de88e32d7eb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Retrospective Snapshot

Generated at: `2026-08-01T20:59:39+00:00`

## Recent changes

- ARCH-002 / ADR-003 / SPEC-002: agent-orchestrated listening via skill tools + ListeningPlaybookFakeModel
- STORY-001 bootstrap complete for `aulos-agent`
- Applied aries-harness init + REQ/SPEC/STORY/ARCH/ADR ladder
- Scaffolded LangChain/LangGraph package: config, llm, prompts, tools, memory, graph, observability, cli
- initialized `.aries_harness/`
- wrote `ARIES_HARNESS_FINGERPRINT.json`

## What is working

- ARCH-002 / ADR-003 / SPEC-002: agent-orchestrated listening via skill tools + ListeningPlaybookFakeModel
- STORY-001 bootstrap complete for `aulos-agent`
- Applied aries-harness init + REQ/SPEC/STORY/ARCH/ADR ladder
- Scaffolded LangChain/LangGraph package: config, llm, prompts, tools, memory, graph, observability, cli

## What needs attention

- working tree is dirty with 330 tracked or untracked change(s)
- no explicit next-up slice is recorded

## Durable reminders

- 导赏 is Agent tool-chain (`run_listening_skill`), not API `iter_listening_chain`.
- See aulos-agent ARCH-002 / ADR-003 / SPEC-002.
- Source of truth: `git@github.com:agilewayai/aries-harness-skills.git` (not `AriesHarnessStudio` / `aries-studio`).
- Local reference clone: `/home/ubuntu/studio/aries-harness-skills` (keep in sync with origin).
- Harness scripts/templates: `.aries_harness/scripts/` + `.aries_harness/templates/` (not project-root `scripts/`/`templates/`).
- Invoke: `bash .aries_harness/scripts/aries-harness.sh <cmd> --project-root .`

## Promotion rule

- if a lesson is durable, move it into MEMORY, docs/insights, AGENTS, or a reusable harness asset
- do not let retrospective output become the only place where important operating knowledge lives
