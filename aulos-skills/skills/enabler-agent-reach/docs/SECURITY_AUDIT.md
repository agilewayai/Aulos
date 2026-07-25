# Security audit — Agent Reach (Aulos intake)

**Date:** 2026-07-25 (UTC)  
**Pinned commit:** `b4d52c46c9113cb0f653d6df4cf71ebadf4930ac`  
**Source:** https://github.com/Panniantong/Agent-Reach (owner-maintained, MIT)  
**Verdict:** **Conditional allow** — install as **search/read enabler only**; fence social cookies, browser extract, CLI system install, and write ops.

## Trust ladder

| Gate | Result |
|------|--------|
| Discovery | GitHub search / hubs point at Agent-Reach; mirrors exist (openclaw hub, Skillselion) |
| Install truth | **Owner repo** `Panniantong/Agent-Reach` `agent_reach/skill/` — not hub HTML |
| License | MIT |
| Maintenance | Active (pushed 2026-07-25); includes PR #530 credential hardening |
| Stars / signal | High popularity; still treat as third-party supply chain |

## Findings

### Acceptable for Aulos search enabler

- **No `shell=True`** in Python package (subprocess uses argv lists).
- Upstream skill explicitly excludes **post/comment/like** write operations.
- Recent hardening: explicit platform cookie extract, `0o600` credential files, doctor does not expand editor imports blindly.
- Public read patterns we adopt:
  - Jina Reader (`https://r.jina.ai/{url}`)
  - Optional Exa via mcporter (ops-gated)
  - `gh` read/search (already on host; no cookie scrape)

### Risks (fenced off)

| Risk | Severity | Aulos mitigation |
|------|----------|------------------|
| Browser cookie extract / social session tokens | High | **Deny** `cookie_extract`, twitter/xhs/reddit/fb/ig configure |
| `agent-reach` install runs `apt-get` / `npm -g` | High | **Do not run** CLI install on aulos hosts; vendor docs only |
| Upstream skill `MUST USE` for all internet research | Medium | Aulos wrapper overrides: compose with native web_search |
| SSRF via Jina/URL fetch | Medium | Only fetch http(s); prefer URLs already returned by wiki/DDG/Brave |
| yt-dlp / social CLIs supply chain | Medium | Not installed; video/social refs vendored as reference-only |
| Credential logging | Medium | Policy: never echo cookies/tokens in logs or skill output |

### Not installed

- Full `pip install agent-reach` + `agent-reach` system bootstrap
- `browser-cookie3` / Playwright extras
- Social platform CLIs (twitter-cli, rdt-cli, OpenCLI, xhs)

## Residual acceptance

Safe as an **enabler skill + Jina deepen step** inside the existing verify→KB loop. Re-audit on update (`PIN.json` commit bump).
