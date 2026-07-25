# Persistence & durability — aulos-knowledge Docker + crawl media

## What must not be lost

| Data | Where it lives | Survives container recreate? | Survives `compose down -v`? |
| --- | --- | --- | --- |
| Knowledge DB (entities, docs, jobs, provenance, media rows) | `data/persist/postgres/` | Yes | **Yes** |
| Vectors / embeddings (JSON cols / future pgvector) | Same Postgres data dir | Yes | Yes |
| Redis (job queue / ARQ, AOF+RDB) | `data/persist/redis/` | Yes | Yes |
| Crawl JSON artifacts | `data/persist/artifacts/json/` | Yes (host) | Yes |
| **Images** (Commons portraits, Cover Art Archive) | `data/persist/artifacts/media/image/` | Yes | Yes |
| **Audio** (Wikidata P51 / Commons PD only) | `data/persist/artifacts/media/audio/` | Yes | Yes |
| **Music-file metadata** (MB recordings/releases JSON) | `data/persist/artifacts/media/meta/` | Yes | Yes |

All of the above sit under **`aulos-knowledge/data/persist/`** — one durable tree. Do not point
`AULOS_KNOWLEDGE_ARTIFACT_ROOT` at a temp or container-writable ephemeral path.

## Media policy (security + license)

- Binary downloads only from allowlisted hosts (Commons / upload.wikimedia.org / Cover Art Archive / archive.org).
- Commercial audio masters are **not** scraped; MusicBrainz contributes **recording file information** (MBID, length, titles) as `kind=meta` JSON.
- Each media file is content-addressed (`sha256`) with provenance rows in `media_assets` + `fetch_artifacts`.

## Guarantees

- **Docker daemon restart / host reboot** — bind mounts remount; `restart: unless-stopped`.
- **`docker compose down` / `down -v`** — host `data/persist/*` is **not** deleted by Compose.
- Destroying data requires deleting those host directories (or disk failure without backups).

## Backup

```bash
bash deploy/backup_persist.sh
# → data/persist/backups/knowledge-YYYYMMDD-HHMMSS.tar.gz
```

Includes: `pg_dump`, Redis AOF/RDB, **full** `data/persist/artifacts` tree (JSON + images + audio + meta)
unless `BACKUP_SKIP_MEDIA_BLOBS=1` (then inventory only).

## Ops checklist

1. `bash deploy/backup_persist.sh`
2. `docker compose -f deploy/docker-compose.knowledge.yml up -d`
3. `curl -fsS http://127.0.0.1:5095/v1/kb/stats` — check `media_images` / `media_meta`
4. Confirm files under `data/persist/artifacts/media/`
