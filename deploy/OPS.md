# Aulos host operations runbook

Canonical operator guide for the production stack on the `ubuntu` host. **Agents and humans must follow this document** for deploy, smoke, rollback, and secret handling.

Entry point: **`bash deploy/aulos-ctl.sh`** (alias: `bash deploy/start-host.sh deploy`).

## Architecture

```text
Internet (HTTPS)
    │
    ▼
k3s Ingress ──► aulos.purezen.ai      ──► aulos-web.service  :5091 ─┐
             └──► aulos-ops.purezen.ai ──► aulos-ops.service  :5092 ─┤
                                                                       ├──► deploy/serve.py proxy ──► aulos-api :5090
aulos-knowledge.service :5095 ◄── API proxy (/v1/knowledge/*) ─────────┘
    │
    ├── Postgres :5433 (aulos + aulos_knowledge)
    ├── Redis :6379
    └── artifact disk under aulos-knowledge/data/persist/
```

| Component | Unit | Port | Log |
| --- | --- | --- | --- |
| API gateway | `aulos-api.service` | 127.0.0.1:5090 | `.run/api.log` |
| Web portal | `aulos-web.service` | 0.0.0.0:5091 | `.run/web.log` |
| Ops portal | `aulos-ops.service` | 0.0.0.0:5092 | `.run/ops.log` |
| Knowledge plane | `aulos-knowledge.service` | 127.0.0.1:5095 | `.run/knowledge.log` |
| Stack target | `aulos-host.target` | — | — |

Persistence: **systemd user units** under `~/.config/systemd/user/` (from `deploy/systemd/user/`), with **`loginctl linger`** so daemons survive logout.

## Operator workflow

### First-time bootstrap

```bash
cd /home/ubuntu/hackathon/aulos
bash deploy/aulos-ctl.sh secrets init    # creates .run/host.env (600) with random secrets
# Edit .run/host.env — set AULOS_BOOTSTRAP_SUPERADMIN_EMAIL
bash deploy/aulos-ctl.sh doctor          # preflight
bash deploy/aulos-ctl.sh deploy          # build + install + smoke
```

### Routine deploy (code or config change)

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)   # optional; ctl sets this automatically
bash deploy/aulos-ctl.sh deploy
```

Deploy sequence (automated):

1. Build API/knowledge venvs + `aulos-skills` editable install
2. `npm run build` for `aulos-web` and `aulos-ops`
3. Validate `.run/host.env` (no placeholders / tracked defaults)
4. Install systemd units + `daemon-reload`
5. Restart `aulos-{api,web,ops,knowledge}.service`
6. `kubectl apply` k3s Ingress/Service/EndpointSlice
7. Smoke: local `:5090/:5091/:5092/:5095` + public HTTPS `/health`

### Partial operations

| Intent | Command |
| --- | --- |
| Build only | `bash deploy/aulos-ctl.sh build` |
| Restart one service | `bash deploy/aulos-ctl.sh restart api` |
| Status | `bash deploy/aulos-ctl.sh status` |
| Smoke (no deploy) | `bash deploy/aulos-ctl.sh smoke` |
| Tail logs | `bash deploy/aulos-ctl.sh logs api` / `logs -f web` |
| Deploy tests | `bash deploy/aulos-ctl.sh test` |
| Secrets check | `bash deploy/aulos-ctl.sh secrets check` |
| Units only | `bash deploy/aulos-ctl.sh units install` |
| Ingress only | `bash deploy/aulos-ctl.sh ingress apply` |

## Secrets policy

**Never commit** `.run/host.env` or live credentials.

| Key | Purpose | Rotation notes |
| --- | --- | --- |
| `AULOS_JWT_SECRET` | Session/JWT signing | Rotating invalidates all sessions — schedule maintenance window |
| `AULOS_BOOTSTRAP_SUPERADMIN_EMAIL` | First superadmin identity | Create-only; changing email does not rename existing user |
| `AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD` | Bootstrap password | Used only when account is first created |
| `AULOS_KNOWLEDGE_ADMIN_TOKEN` | Knowledge `/v1/admin/*` bearer | Must match on API + knowledge units (shared `host.env`) |

Template: `deploy/host.env.example`. Init: `aulos-ctl secrets init`.

Deploy **refuses** placeholder values (`REPLACE_WITH_*`, `ChangeMe`, `aulos-dev-jwt-secret*`, etc.).

Mailgun, LLM keys, and other integration secrets are configured in the **Ops portal** (`SystemSetting` DB) — see ADR-008 for Sprint-1 plaintext storage risk.

## Verification gates

A deploy is **not complete** until:

1. `aulos-ctl smoke` exits 0 (GET `/health`, not HEAD)
2. `aulos-ctl status` shows all four services `active (running)`
3. For behavior changes: sub-project pytest green before deploy
4. For deploy-layer changes: `aulos-ctl test` green

Recommended pre-deploy:

```bash
cd aulos-api && .venv/bin/pytest -q          # API contract
bash deploy/aulos-ctl.sh test                # static host + headers + rate gate
bash deploy/aulos-ctl.sh doctor              # host readiness
```

## Rollback

There is no blue/green release — rollback is **redeploy previous git revision**:

```bash
git checkout <known-good-sha>
bash deploy/aulos-ctl.sh deploy
```

If only a service misbehaves:

```bash
bash deploy/aulos-ctl.sh restart api
# or stop:
systemctl --user stop aulos-api.service
```

**Rollback owner:** operator on call for the host (human). Capture `aulos-ctl status`, last 200 log lines, and smoke output in the harness JOURNAL when rollback occurs.

## Database & schema

- Production primary: **Postgres** (`AULOS_DB_URL` in unit file).
- Failover mirror: SQLite (`AULOS_DB_FAILOVER_URL`).
- After ORM changes: ship `schema_patches.py`, deploy, verify PG columns (see `aulos-operating-defaults` DB closeout).

Knowledge plane has separate DB `aulos_knowledge` on the same Postgres instance.

## Asset versioning

Portal builds emit `dist/version.json`. Browsers poll it; mismatch shows a reload tip. Override with `AULOS_BUILD_ID=...` at build time if needed.

## Security baseline

- API rate limits + abuse strikes (`deploy/README.md`).
- Static/proxy security headers (`deploy/security_headers.py`, `aulos-ctl test`).
- Session cookies HttpOnly (`aulos_session`) — no JWT in `localStorage`.
- Knowledge admin only via API proxy with bearer from `host.env`.

## Human approval boundaries

Agents **must ask** before:

- Production `aulos-ctl deploy` unless the operator explicitly requested it in the current turn
- Secret rotation on live host
- `kubectl` changes beyond tracked `deploy/k3s/aulos.yaml`
- Destructive DB operations

## Harness integration

DevOps slices close in **aulos-skills** harness:

1. Update this runbook or `deploy/README.md` when topology/commands change
2. `JOURNAL.md` entry for production deploys / incidents
3. **Honeycomb** (`bash deploy/honeycomb.sh`) when the slice closes a milestone
4. Optional deployment memo under `.aries_harness/runs/deployments/` for high-risk releases

**Honeycomb** = fleet `well-organized` + `history-refresh` on every `aulos-*` harness project. See `aulos-operating-defaults`.

## Related docs

- [`deploy/README.md`](README.md) — quick reference, rate limits, Mailgun/LLM ops
- [`AGENTS.md`](../AGENTS.md) — workspace agent guide
- [`aulos-skills/skills/aulos-operating-defaults/SKILL.md`](../aulos-skills/skills/aulos-operating-defaults/SKILL.md) — canonical policy
- [`aulos-knowledge/deploy/PERSISTENCE.md`](../aulos-knowledge/deploy/PERSISTENCE.md) — knowledge artifact backup
