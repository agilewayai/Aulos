from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.connectors.catalog_import import run_catalog_import
from aulos_knowledge.connectors.musicbrainz import run_musicbrainz
from aulos_knowledge.connectors.wikidata import run_wikidata
from aulos_knowledge.db import FetchJob, SourceAuthority


def run_connector(db: Session, *, source: SourceAuthority, job: FetchJob, params: dict[str, Any]) -> None:
    name = (source.connector or "").strip()
    if name == "catalog_import":
        run_catalog_import(db, source=source, job=job, params=params)
        return
    if name == "wikidata":
        run_wikidata(db, source=source, job=job, params=params)
        return
    if name == "musicbrainz":
        run_musicbrainz(db, source=source, job=job, params=params)
        return
    raise ValueError(f"unsupported connector: {name}")
