#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
UNIT_DIR="$HOME/.config/systemd/user"
RUN_DIR="$ROOT/.run"

mkdir -p "$RUN_DIR" "$UNIT_DIR"
touch "$RUN_DIR/host.env"

export PATH="${PATH}:/home/ubuntu/.nvm/versions/node/v26.4.0/bin"

echo "[1/5] Ensure aulos-api venv"
if [ ! -x "$ROOT/aulos-api/.venv/bin/aulos-api" ]; then
  python3 -m venv "$ROOT/aulos-api/.venv"
  "$ROOT/aulos-api/.venv/bin/pip" install -e "$ROOT/aulos-api/[dev]"
fi

echo "[2/5] Build aulos-web"
(
  cd "$ROOT/aulos-web"
  npm install --silent
  npm run build
)

echo "[3/5] Build aulos-ops"
(
  cd "$ROOT/aulos-ops"
  npm install --silent
  npm run build
)

echo "[4/5] Install systemd user units"
cp -f "$ROOT/deploy/systemd/user/"*.service "$UNIT_DIR/"
cp -f "$ROOT/deploy/systemd/user/"*.target "$UNIT_DIR/"
systemctl --user daemon-reload
systemctl --user enable --now aulos-host.target
systemctl --user restart aulos-api.service aulos-web.service aulos-ops.service

echo "[5/5] Apply k3s Ingress"
sudo kubectl apply -f "$ROOT/deploy/k3s/aulos.yaml"

echo
systemctl --user --no-pager --plain status aulos-api.service aulos-web.service aulos-ops.service | sed -n '1,80p'
echo
sudo kubectl get ingress aulos-web aulos-ops
echo
echo "Local smoke:"
curl -fsS "http://127.0.0.1:5090/health" && echo
curl -fsSI "http://127.0.0.1:5091/" | head -5
curl -fsSI "http://127.0.0.1:5092/" | head -5
echo "Public hosts (may need a few seconds for ingress):"
curl -fsSI "https://aulos.purezen.ai/" | head -8 || true
curl -fsSI "https://aulos-ops.purezen.ai/" | head -8 || true
