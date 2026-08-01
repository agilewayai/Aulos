# Aulos Knowledge — professional music knowledge plane

Independent from `aulos-api` business SQLite. See `.aries_harness/` REQ-007 / ARCH-005 / STORY-PACK-007.

## Run (dev SQLite)

```bash
cd aulos-knowledge
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
export AULOS_KNOWLEDGE_DB_URL="sqlite:///./data/knowledge.db"
aulos-knowledge
# → http://127.0.0.1:5095/health
```

## Postgres + pgvector (S1 production path)

Security defaults in `deploy/docker-compose.knowledge.yml`:

- Images **digest-pinned** (see `deploy/IMAGE_DIGESTS.md`) — Hub pull from Docker Engine official apt, not snap mirrors
- Ports bound to **127.0.0.1** only
- `no-new-privileges`, `cap_drop: ALL` (+ minimal adds for postgres/redis)
- Healthchecks required before crawl/smoke
- **Durable bind mounts** (not anonymous Docker volumes): `data/persist/postgres`, `data/persist/redis` — survive container recreate, daemon restart, and `compose down -v`. See `deploy/PERSISTENCE.md`.

1. Start infra:

```bash
docker compose -f deploy/docker-compose.knowledge.yml up -d
# Postgres: localhost:5433  user/pass/db = aulos/aulos/aulos_knowledge
# Redis: localhost:6379
```

2. Install driver extras and point DSN:

```bash
pip install -e ".[dev,postgres]"
export AULOS_KNOWLEDGE_DB_URL="postgresql+psycopg://aulos:aulos@127.0.0.1:5433/aulos_knowledge"
export AULOS_KNOWLEDGE_ARTIFACT_ROOT="$(pwd)/data/persist/artifacts"
aulos-knowledge
```

3. Smoke (creates schema + seeds allowlisted sources):

```bash
bash deploy/pg_smoke.sh
# expect: PG_SMOKE_OK
```

4. Bootstrap KB from famous composers (catalog → Wikidata → MusicBrainz):

```bash
bash deploy/crawl_famous_composers.sh
# expect: CRAWL_BOOTSTRAP_OK
```

5. Backup durable data (Postgres + Redis + artifact inventory):

```bash
bash deploy/backup_persist.sh
bash deploy/persist_smoke.sh   # recreate postgres container; counts must match
```

Schema is SQLAlchemy `create_all` on boot (`db.init_db`). Embeddings remain JSON columns in MVP;
pgvector ANN indexes are a Later TASK_STACK item — relational isolation is the S1 gate.

## Workers

Default **async** crawl queue (META-001 §3.3): `AULOS_KNOWLEDGE_SYNC_JOBS=false` enqueues
`fetch_jobs` and runs connectors on background threads; HTTP returns **202**. Poll
`GET /v1/admin/jobs/{id}`. Set `SYNC_JOBS=true` only for pytest / local smoke escape hatch.
See `docs/worker.md`.

## OPS

Enable plane from API: `AULOS_KNOWLEDGE_PLANE_ENABLED=true` and
`AULOS_KNOWLEDGE_BASE_URL=http://127.0.0.1:5095`. Audit via aulos-ops **Knowledge** tab.
