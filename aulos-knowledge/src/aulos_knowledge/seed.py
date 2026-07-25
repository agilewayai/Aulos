"""Seed allowlisted authority sources (ADR-006)."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from aulos_knowledge.db import SourceAuthority

DEFAULT_SOURCES = [
    {
        "id": "catalog-local",
        "name": "Aulos Work Identity Catalog",
        "tier": "S",
        "connector": "catalog_import",
        "base_urls": [],
        "license_class": "internal",
        "rate_limit_qps": 100.0,
        "notes": "Product identity cards under aulos-skills catalog/",
    },
    {
        "id": "wikidata",
        "name": "Wikidata",
        "tier": "S",
        "connector": "wikidata",
        "base_urls": ["https://www.wikidata.org/", "https://query.wikidata.org/"],
        "license_class": "CC0",
        "rate_limit_qps": 2.0,
        "notes": "Composer/work structured data via WB API / SPARQL",
    },
    {
        "id": "musicbrainz",
        "name": "MusicBrainz",
        "tier": "S",
        "connector": "musicbrainz",
        "base_urls": ["https://musicbrainz.org/", "https://www.musicbrainz.org/ws/2/"],
        "license_class": "ODbL",
        "rate_limit_qps": 1.0,
        "notes": "Works/recordings/releases — respect UA + rate limit; ODbL share-alike on extracts",
    },
    {
        "id": "wikipedia",
        "name": "Wikipedia (EN/ZH summaries)",
        "tier": "A",
        "connector": "wikipedia",
        "base_urls": ["https://en.wikipedia.org/", "https://zh.wikipedia.org/"],
        "license_class": "CC-BY-SA",
        "rate_limit_qps": 1.0,
        "notes": "Summary extracts only via Action API — attribution required",
        "enabled": False,
    },
]


def seed_default_sources(db: Session) -> int:
    n = 0
    for row in DEFAULT_SOURCES:
        existing = db.get(SourceAuthority, row["id"])
        if existing:
            continue
        db.add(
            SourceAuthority(
                id=row["id"],
                name=row["name"],
                tier=row["tier"],
                connector=row["connector"],
                base_urls_json=json.dumps(row.get("base_urls") or [], ensure_ascii=False),
                license_class=row["license_class"],
                rate_limit_qps=float(row.get("rate_limit_qps") or 1.0),
                enabled=bool(row.get("enabled", True)),
                notes=row.get("notes") or "",
            )
        )
        n += 1
    if n:
        db.commit()
    return n
