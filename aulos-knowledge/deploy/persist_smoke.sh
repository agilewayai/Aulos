#!/usr/bin/env bash
# Prove Postgres data survives container recreate (bind-mount durability smoke).
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
COMPOSE="$root/deploy/docker-compose.knowledge.yml"
cd "$root"

before=$(docker compose -f "$COMPOSE" exec -T postgres \
  psql -U aulos -d aulos_knowledge -Atc "SELECT count(*) FROM composers;")
echo "composers_before=$before"
test -n "$before"
test "$before" -gt 0

echo "==> recreate postgres container"
docker compose -f "$COMPOSE" up -d --force-recreate postgres
for i in $(seq 1 40); do
  if docker compose -f "$COMPOSE" exec -T postgres pg_isready -U aulos -d aulos_knowledge >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

after=$(docker compose -f "$COMPOSE" exec -T postgres \
  psql -U aulos -d aulos_knowledge -Atc "SELECT count(*) FROM composers;")
echo "composers_after=$after"
test "$before" = "$after"
echo "PERSIST_SMOKE_OK"
