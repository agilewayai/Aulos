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

## Rollback

```bash
systemctl --user stop aulos-host.target
sudo kubectl delete -f deploy/k3s/aulos.yaml
```
