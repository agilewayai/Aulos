#!/usr/bin/env bash
# Snapshot durable knowledge data: Postgres + Redis + artifacts/media tree.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
COMPOSE="${COMPOSE:-deploy/docker-compose.knowledge.yml}"
STAMP=$(date -u +%Y%m%d-%H%M%S)
OUT_DIR="$root/data/persist/backups"
WORKDIR="$OUT_DIR/staging-$STAMP"
ART_ROOT="${AULOS_KNOWLEDGE_ARTIFACT_ROOT:-$root/data/persist/artifacts}"
mkdir -p "$WORKDIR/redis" "$WORKDIR/artifacts"

echo "==> pg_dump (custom + plain)"
docker compose -f "$COMPOSE" exec -T postgres \
  pg_dump -U aulos -d aulos_knowledge -Fc \
  > "$WORKDIR/aulos_knowledge.dump"
docker compose -f "$COMPOSE" exec -T postgres \
  pg_dump -U aulos -d aulos_knowledge --no-owner --no-acl \
  | gzip -c > "$WORKDIR/aulos_knowledge.sql.gz"

echo "==> redis BGSAVE + copy AOF/RDB"
docker compose -f "$COMPOSE" exec -T redis redis-cli BGSAVE >/dev/null || true
sleep 1
docker run --rm \
  -v "$root/data/persist/redis:/from:ro" \
  -v "$WORKDIR/redis:/to" \
  alpine:3.20 \
  sh -c 'cd /from && tar cf - . | (cd /to && tar xpf -)'

echo "==> artifacts + media (images / audio / music-file meta)"
if [ -d "$ART_ROOT" ]; then
  (cd "$ART_ROOT" && find . -type f | sort | head -n 20000) > "$WORKDIR/artifacts/file-list.txt" || true
  du -sh "$ART_ROOT" > "$WORKDIR/artifacts/du.txt" || true
  du -sh "$ART_ROOT"/media/* 2>/dev/null > "$WORKDIR/artifacts/media-du.txt" || true
  if [ "${BACKUP_SKIP_MEDIA_BLOBS:-0}" != "1" ]; then
    docker run --rm \
      -v "$ART_ROOT:/from:ro" \
      -v "$WORKDIR/artifacts:/to" \
      alpine:3.20 \
      sh -c 'mkdir -p /to/tree && cd /from && tar cf - . | (cd /to/tree && tar xpf -)'
  else
    echo "BACKUP_SKIP_MEDIA_BLOBS=1 — inventory only" > "$WORKDIR/artifacts/SKIPPED_BLOBS.txt"
  fi
fi

META="$WORKDIR/META.txt"
{
  echo "stamp=$STAMP"
  echo "host=$(hostname)"
  echo "artifact_root=$ART_ROOT"
  docker compose -f "$COMPOSE" exec -T postgres \
    psql -U aulos -d aulos_knowledge -Atc \
    "SELECT 'composers='||count(*) FROM composers UNION ALL SELECT 'docs='||count(*) FROM kb_documents UNION ALL SELECT 'jobs='||count(*) FROM fetch_jobs UNION ALL SELECT 'media='||count(*) FROM media_assets;"
} > "$META"

ARCHIVE="$OUT_DIR/knowledge-$STAMP.tar.gz"
docker run --rm \
  -v "$OUT_DIR:/backups" \
  alpine:3.20 \
  sh -c "cd /backups && tar czf knowledge-$STAMP.tar.gz staging-$STAMP && rm -rf staging-$STAMP"
echo "BACKUP_OK $ARCHIVE"
ls -lh "$ARCHIVE"
