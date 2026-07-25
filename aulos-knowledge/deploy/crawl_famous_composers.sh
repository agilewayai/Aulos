#!/usr/bin/env bash
# Bootstrap knowledge plane on Postgres: catalog import + famous-composer crawls.
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

COMPOSE="${COMPOSE:-deploy/docker-compose.knowledge.yml}"
DSN_DEFAULT="postgresql+psycopg://aulos:aulos@127.0.0.1:5433/aulos_knowledge"
export AULOS_KNOWLEDGE_DB_URL="${AULOS_KNOWLEDGE_DB_URL:-$DSN_DEFAULT}"
export AULOS_KNOWLEDGE_ARTIFACT_ROOT="${AULOS_KNOWLEDGE_ARTIFACT_ROOT:-$root/data/persist/artifacts}"
export AULOS_KNOWLEDGE_SYNC_JOBS="${AULOS_KNOWLEDGE_SYNC_JOBS:-true}"
export AULOS_KNOWLEDGE_CATALOG_ROOT="${AULOS_KNOWLEDGE_CATALOG_ROOT:-$root/../aulos-skills/skills/aulos-listening-corpus/assets/catalog}"
mkdir -p "$AULOS_KNOWLEDGE_ARTIFACT_ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker required" >&2
  exit 1
fi

echo "==> Starting hardened compose ($COMPOSE)"
docker compose -f "$COMPOSE" up -d
echo "==> Waiting for postgres health..."
for i in $(seq 1 60); do
  if docker compose -f "$COMPOSE" exec -T postgres pg_isready -U aulos -d aulos_knowledge >/dev/null 2>&1; then
    echo "postgres ready"
    break
  fi
  sleep 1
done

. .venv/bin/activate 2>/dev/null || python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,postgres]" -q

python - <<'PY'
from __future__ import annotations

import time

from aulos_knowledge.config import get_settings
from aulos_knowledge import db as db_mod
from aulos_knowledge.seed import seed_default_sources
from aulos_knowledge.jobs import enqueue_and_maybe_run
from aulos_knowledge.famous_composers import FAMOUS_COMPOSERS
from aulos_knowledge.db import ComposerEntity, FetchJob, KnowledgeDocument, WorkEntity

get_settings.cache_clear()
s = get_settings()
print("dsn=", s.db_url)
db_mod.init_db(s.db_url)
assert db_mod.SessionLocal is not None
db = db_mod.SessionLocal()

try:
    print("seeded_sources=", seed_default_sources(db))

    # 1) Identity catalog → works/composers baseline
    job = enqueue_and_maybe_run(db, source_id="catalog-local", params={}, sync=True)
    print("catalog_job=", job.id, job.status, job.error or "")

    # 2) Wikidata composer dossiers (batched QIDs to reduce round-trips)
    qids = [c["wikidata_qid"] for c in FAMOUS_COMPOSERS]
    # one job per composer so provenance stays attributable
    for c in FAMOUS_COMPOSERS:
        j = enqueue_and_maybe_run(
            db,
            source_id="wikidata",
            params={"qids": [c["wikidata_qid"]], "composer_id": c["composer_id"]},
            sync=True,
        )
        print(f"wikidata {c['composer_id']}: job={j.id} status={j.status} err={j.error or ''}")
        time.sleep(0.35)  # polite pacing beyond source QPS

    # 3) MusicBrainz artist + representative works (≤1 req/s inside connector)
    for c in FAMOUS_COMPOSERS:
        ja = enqueue_and_maybe_run(
            db,
            source_id="musicbrainz",
            params={
                "mode": "artist",
                "query": c["musicbrainz_query"],
                "composer_id": c["composer_id"],
            },
            sync=True,
        )
        print(f"mb-artist {c['composer_id']}: job={ja.id} status={ja.status} err={ja.error or ''}")
        jw = enqueue_and_maybe_run(
            db,
            source_id="musicbrainz",
            params={
                "mode": "work",
                "query": c["work_query"],
                "composer_id": c["composer_id"],
            },
            sync=True,
        )
        print(f"mb-work {c['composer_id']}: job={jw.id} status={jw.status} err={jw.error or ''}")

    composers = db.query(ComposerEntity).count()
    works = db.query(WorkEntity).count()
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.status == "published").count()
    jobs_ok = db.query(FetchJob).filter(FetchJob.status == "succeeded").count()
    jobs_fail = db.query(FetchJob).filter(FetchJob.status == "failed").count()
    print("---")
    print(f"composers={composers} works={works} docs_published={docs} jobs_ok={jobs_ok} jobs_fail={jobs_fail}")
    print("CRAWL_BOOTSTRAP_OK")
finally:
    db.close()
PY
