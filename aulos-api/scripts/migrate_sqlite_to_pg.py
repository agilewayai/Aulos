#!/usr/bin/env python3
"""One-shot: copy business SQLite → Postgres primary (schema + rows)."""

from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import create_engine, insert, text
from sqlalchemy.orm import sessionmaker


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--from-url",
        default=os.environ.get("AULOS_DB_FAILOVER_URL")
        or os.environ.get("AULOS_MIGRATE_FROM")
        or "sqlite:////home/ubuntu/hackathon/aulos/aulos-api/data/aulos.db",
    )
    p.add_argument(
        "--to-url",
        default=os.environ.get("AULOS_DB_URL")
        or "postgresql+psycopg://aulos:aulos@127.0.0.1:5433/aulos",
    )
    args = p.parse_args()
    if args.from_url == args.to_url:
        print("from and to URLs are identical", file=sys.stderr)
        return 2

    # Ensure target DB exists (Postgres)
    if args.to_url.startswith("postgresql"):
        # connect to maintenance db
        admin = args.to_url.rsplit("/", 1)[0] + "/postgres"
        dbname = args.to_url.rsplit("/", 1)[-1]
        eng_admin = create_engine(admin, isolation_level="AUTOCOMMIT", future=True)
        with eng_admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname=:n"),
                {"n": dbname},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{dbname}"'))
                print("created database", dbname)
        eng_admin.dispose()

    os.environ["AULOS_DB_URL"] = args.to_url
    os.environ["AULOS_DB_FAILOVER_URL"] = ""
    from aulos_api.config import get_settings

    get_settings.cache_clear()

    from aulos_api.db.session import Base, init_db
    from aulos_api.db import models  # noqa: F401

    src = create_engine(
        args.from_url,
        future=True,
        connect_args={"check_same_thread": False} if args.from_url.startswith("sqlite") else {},
    )
    dst = create_engine(args.to_url, future=True, pool_pre_ping=True)
    Base.metadata.create_all(bind=dst)

    tables = list(Base.metadata.sorted_tables)
    with src.connect() as sconn, dst.begin() as dconn:
        for table in reversed(tables):
            dconn.execute(table.delete())
        for table in tables:
            rows = [dict(r) for r in sconn.execute(table.select()).mappings().all()]
            if rows:
                dconn.execute(insert(table), rows)
            print(f"{table.name}: {len(rows)}")
    
    # Realign SERIAL sequences after explicit PK inserts
    with dst.begin() as dconn:
        dconn.execute(text("""
        DO $$
        DECLARE r record;
        BEGIN
          FOR r IN
            SELECT c.relname AS tbl, a.attname AS col
            FROM pg_class c
            JOIN pg_namespace n ON n.oid=c.relnamespace
            JOIN pg_attribute a ON a.attrelid=c.oid
            JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
            WHERE n.nspname='public' AND c.relkind='r'
              AND pg_get_expr(d.adbin,d.adrelid) LIKE 'nextval%'
          LOOP
            EXECUTE format(
              'SELECT setval(pg_get_serial_sequence(%L,%L), COALESCE((SELECT MAX(%I) FROM %I),1))',
              r.tbl, r.col, r.col, r.tbl
            );
          END LOOP;
        END$$;
        """))

    print("MIGRATE_OK", args.from_url, "→", args.to_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
