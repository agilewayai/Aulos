from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.connectors.catalog_import import run_catalog_import
from aulos_knowledge.connectors.imslp import run_imslp
from aulos_knowledge.connectors.musicbrainz import run_musicbrainz
from aulos_knowledge.connectors.rism import run_rism
from aulos_knowledge.connectors.wikidata import run_wikidata
from aulos_knowledge.connectors.wikipedia import run_wikipedia
from aulos_knowledge.db import FetchJob, SourceAuthority

REGISTERED_CONNECTORS = frozenset(
    {"catalog_import", "wikidata", "musicbrainz", "wikipedia", "imslp", "rism"}
)


def connector_registered(name: str) -> bool:
    return (name or "").strip() in REGISTERED_CONNECTORS


def run_connector(db: Session, *, source: SourceAuthority, job: FetchJob, params: dict[str, Any]) -> None:
    name = (source.connector or "").strip()
    if name not in REGISTERED_CONNECTORS:
        raise ValueError(f"unsupported connector: {name or '(empty)'}")
    if name == "catalog_import":
        run_catalog_import(db, source=source, job=job, params=params)
        return
    if name == "wikidata":
        run_wikidata(db, source=source, job=job, params=params)
        return
    if name == "musicbrainz":
        run_musicbrainz(db, source=source, job=job, params=params)
        return
    if name == "wikipedia":
        run_wikipedia(db, source=source, job=job, params=params)
        return
    if name == "imslp":
        run_imslp(db, source=source, job=job, params=params)
        return
    if name == "rism":
        run_rism(db, source=source, job=job, params=params)
        return
    raise ValueError(f"unsupported connector: {name}")
