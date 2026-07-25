---
name: enabler-agent-reach
description: >
  Aulos search/read enabler vendored from Panniantong/Agent-Reach (pinned).
  Use for open-web deepen (Jina Reader) and optional Exa/gh read — not for
  social cookies, write ops, or replacing the listening skill chain.
  Composes with Wikipedia / DuckDuckGo / Brave web-research.
metadata:
  upstream: https://github.com/Panniantong/Agent-Reach
  pin: b4d52c46c9113cb0f653d6df4cf71ebadf4930ac
  aulos_layer: enabler
---

# Agent Reach — Aulos Search Enabler

Policy-fenced wrapper around [Agent Reach](https://github.com/Panniantong/Agent-Reach).  
Full audit: [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md) · Intake: [docs/INTAKE.md](docs/INTAKE.md) · Cookbook: [docs/COOKBOOK.md](docs/COOKBOOK.md)

Upstream manuals (vendored, read-only): [vendor/upstream/](vendor/upstream/)

## Role in Aulos

This skill is **one search enabler**, not the internet router of record.

| Priority | Enabler | Notes |
|----------|---------|--------|
| 1 | Wikipedia + DuckDuckGo | Native `aulos-api` `web_search` |
| 2 | Brave (optional) | Ops API key |
| 3 | **Agent Reach (this)** | Jina deepen of trusted URLs; optional Exa/gh |
| — | Listening skills | Unchanged — no triggers on this pack |

## Allowed commands (read/search only)

```bash
# Deepen a URL already found by wiki/DDG/Brave (Jina Reader)
curl -fsSL -A "AulosResearchBot/0.1" "https://r.jina.ai/https://example.com/article"

# Optional: GitHub code/repo search (read-only; requires gh)
gh search repos "query" --sort stars --limit 10

# Optional: Exa (only if ops configured mcporter + Exa MCP)
mcporter call 'exa.web_search_exa(query: "query", numResults: 5)'
```

API path: when `AULOS_AGENT_REACH_ENABLED=true`, `gather_web_sources` may attach
`provider: agent-reach-jina` snippets for top result URLs.

## Hard denials (do not run on Aulos hosts)

- `agent-reach` install / update that mutates apt, npm `-g`, or system packages
- `agent-reach configure *cookies*` / `--from-browser` / cookie extract
- Twitter / XiaoHongShu / Reddit / Facebook / Instagram / Xueqiu session CLIs
- Post, comment, like, or any write operation
- Treating upstream `MUST USE` as mandatory for every research ask

See [policy.yaml](policy.yaml).

## Procedure for operator agents

1. Resolve work identity (catalog) when the ask is a listening guide.
2. Run native web gather + KB RAG first.
3. If pages need full text, deepen **existing** https URLs with Jina.
4. Hand verified text to the web-research verify → KB upsert loop.
5. Never invent composer/work branches in this enabler.

## Anti-patterns

- Installing the full Agent Reach CLI bootstrap on production API hosts
- Pasting cookies into chat or logs
- Using this skill to bypass knowledge-plane verify
- Pulling hub mirrors instead of the pinned owner commit in `PIN.json`
