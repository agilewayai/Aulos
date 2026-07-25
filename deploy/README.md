# Aulos host deploy

Persistent host daemons + k3s Ingress for public HTTPS.

| URL | Backend |
| --- | --- |
| https://aulos.purezen.ai | `aulos-web.service` → `:5091` |
| https://aulos-ops.purezen.ai | `aulos-ops.service` → `:5092` |
| (local) API | `aulos-api.service` → `127.0.0.1:5090` (proxied by both portals) |

## One-shot deploy / restart

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
bash deploy/start-host.sh
```

## Persistence

- systemd **user** units under `~/.config/systemd/user/`
- `loginctl linger` enabled for `ubuntu` so units survive logout / Cursor session close
- k3s `Service` + `EndpointSlice` + `Ingress` in `deploy/k3s/aulos.yaml`

## Status

```bash
systemctl --user status aulos-host.target aulos-api aulos-web aulos-ops
curl -fsS https://aulos.purezen.ai/health
curl -fsS https://aulos-ops.purezen.ai/health
```

## Asset versioning

Each portal build writes `dist/version.json` (`buildId`) and injects the same id into the JS bundle.
Browsers poll `/version.json` (no-cache). On mismatch, a small corner tip offers **Reload** (dismissible for the session).

Override the id with `AULOS_BUILD_ID=...` when building if needed.

## Rate limits & abuse detection

- **API** (`aulos-api`): per-IP sliding windows — strict on `/v1/auth/*`, compose streams, public guides, knowledge; `/v1/chat` requires auth. Exceeded requests return `429` + `Retry-After`. Repeated blocks escalate to `abuse_suspected` logs (`AULOS_ABUSE_STRIKE_LIMIT`, default 8 / 5min).
- **Static host** (`deploy/serve.py`): limits `/version.json`, `/g/*`, proxied `/v1/*`, and assets. Client version checks back off on `429`.
- Toggle: `AULOS_RATE_LIMIT_ENABLED`, `AULOS_TRUST_PROXY` (honor `X-Forwarded-For` behind ingress).

## Ambient audio failover

Guide players try the origin CDN first. On block / stall / error they fail over to:

1. `/v1/media/audio?mode=cache` — local disk cache on the API host  
2. `/v1/media/audio?mode=proxy` — reverse-proxy stream through Aulos  

Hosts are allowlisted (Wikimedia / archive.org / purezen). Cache dir: `AULOS_MEDIA_CACHE_DIR` (default `data/media-cache`). Corpus ambient URLs are prefetched on API start.


## Auth bootstrap

Default host unit boots a superadmin from env (override in `.run/host.env`):

- `AULOS_BOOTSTRAP_SUPERADMIN_EMAIL`
- `AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD`

Ops portal (https://aulos-ops.purezen.ai) requires the `superadmin` role. Configure Mailgun there (domain, API key, from, region). With `AULOS_MAIL_PROVIDER=auto` (default), live sends start as soon as Mailgun is enabled and complete in ops — no API restart required. Use the Test Mailgun button and the delivery log panel to confirm sends; API logs under `.run/api.log` include `mail_send_*` lines.

LLM providers (DeepSeek + Grok) are configured under the **LLM** tab. Set API keys/models, choose the active provider, then Test. When a live provider is active and complete, `/v1/chat` uses it (source=`deepseek` or `grok`).
