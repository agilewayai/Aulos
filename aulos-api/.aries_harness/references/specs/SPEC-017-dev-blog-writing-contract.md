---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-27T10:15:00Z"
effective_status: "active"
effective_since: "2026-07-27T10:15:00Z"
content_fingerprint: "sha256:725cd80621cfaa0dcc22d6038d196b39dcb75e31ee13815ce7f4a821d076e219"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Spec Package

## Document Control

- Spec ID: SPEC-017
- Title: Dev Blog internal writing contract
- Status: active
- Related: SPEC-009 (API), aulos-ops SPEC-002, REQ-002
- Code: `aulos_api/services/dev_blog_contract.py`

## Purpose

Dev Blog is an **internal development trace**, not a public product blog. Posts help operators and developers answer: *what changed on this evidence day, in which subsystem, with what user/ops impact?*

## Non-goals

- External marketing, community distill, or emotional narrative
- Replacing harness `JOURNAL.md`, `history/daily`, or git log
- Mandatory one-post-per-day cadence

## Voice rules (mandatory)

| Do | Don't |
| --- | --- |
| State facts from git + harness evidence | Exaggerate, hype, or add vision language |
| Name sub-projects (`aulos-api`, `deploy`, …) and AUDIT/SPEC when in evidence | Invent features not in evidence |
| Say plainly when there is no user-visible change | Imply benefits without evidence |
| Use calm engineer-to-colleague tone | PR / slogan / 「关键一步」式渲染 |

## Structure (unchanged headings)

1. `#` title — short factual line (may include date)
2. `## 今天产品多了什么` — capability / code deltas
3. `## 谁因此更好用了` — affected roles or paths; or explicit「无终端用户可见变化」
4. `## 系统怎么搭起来的` — module, API, auth, deploy facts

## Evidence sources (generation input)

- UTC-day `git log` for monorepo root
- Per-project harness: `JOURNAL.md`, `history/daily/{day}.md`, `STATE.md`
- Changed REQ/SPEC/STORY paths that day

## Generation

- System prompt: `dev_blog_contract.SYSTEM_PROMPT`
- Soft lint: `validate_dev_blog_body()` logs warnings (hype phrases, missing sections, known hallucination patterns)
- Fake/offline path: `render_fake_draft()` follows same factual minimal style

## Acceptance

- `pytest tests/test_dev_blog.py` includes contract lint tests
- SPEC-009 / SPEC-002 reference this document
- Ops UI lead copy states internal trace purpose
