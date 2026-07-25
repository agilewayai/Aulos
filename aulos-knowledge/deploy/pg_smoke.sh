#!/usr/bin/env bash
# S1 smoke: bring up Postgres+Redis (optional) and ping knowledge health against PG DSN.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

COMPOSE="${COMPOSE:-deploy/docker-compose.knowledge.yml}"
DSN_DEFAULT="postgresql+psycopg://aulos:aulos@127.0.0.1:5433/aulos_knowledge"

if ! command -v docker >/dev/null 2>&1; then
  echo "SKIP: docker not available — Postgres smoke not run (record as S1 residual risk)"
  exit 0
fi

echo "Starting compose: $COMPOSE"
docker compose -f "$COMPOSE" up -d
echo "Waiting for postgres..."
for i in $(seq 1 30); do
  if docker compose -f "$COMPOSE" exec -T postgres pg_isready -U aulos >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

export AULOS_KNOWLEDGE_DB_URL="${AULOS_KNOWLEDGE_DB_URL:-$DSN_DEFAULT}"
export AULOS_KNOWLEDGE_ARTIFACT_ROOT="${AULOS_KNOWLEDGE_ARTIFACT_ROOT:-$root/data/persist/artifacts}"
mkdir -p "$AULOS_KNOWLEDGE_ARTIFACT_ROOT"

. .venv/bin/activate 2>/dev/null || true
pip install -e ".[dev,postgres]" -q

python - <<'PY'
from aulos_knowledge.config import get_settings
from aulos_knowledge import db as db_mod
from aulos_knowledge.seed import seed_default_sources

get_settings.cache_clear()
s = get_settings()
print("dsn=", s.db_url)
db_mod.init_db(s.db_url)
assert db_mod.SessionLocal is not None
db = db_mod.SessionLocal()
try:
    n = seed_default_sources(db)
    print("seeded_sources=", n)
    from aulos_knowledge.db import SourceAuthority
    print("sources=", db.query(SourceAuthority).count())
finally:
    db.close()
print("PG_SMOKE_OK")
PY
