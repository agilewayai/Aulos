"""Import Aulos Work Identity Catalog into the professional KB with provenance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.artifacts import write_artifact
from aulos_knowledge.publish_policy import document_status_for_source
from aulos_knowledge.config import get_settings
from aulos_knowledge.db import (
    ComposerEntity,
    FetchArtifact,
    FetchJob,
    KnowledgeChunk,
    KnowledgeDocument,
    SourceAuthority,
    WorkEntity,
)


EXTRACTOR_VERSION = "catalog_import/0.1.0"


def _default_catalog_root() -> Path:
    settings = get_settings()
    if settings.catalog_root:
        return Path(settings.catalog_root)
    # aulos-knowledge/ -> sibling aulos-skills catalog
    return (
        Path(__file__).resolve().parents[4]
        / "aulos-skills"
        / "skills"
        / "aulos-listening-corpus"
        / "assets"
        / "catalog"
    )


def run_catalog_import(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    params: dict[str, Any],
) -> None:
    root = Path(params["catalog_root"]) if params.get("catalog_root") else _default_catalog_root()
    index_path = root / "index.yaml"
    if not index_path.is_file():
        raise FileNotFoundError(f"catalog index missing: {index_path}")

    import yaml

    index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    bundle: dict[str, Any] = {"index": index, "composers": {}, "works": {}}

    for entry in index.get("composers") or []:
        path = root / str(entry.get("path") or "")
        if path.is_file():
            bundle["composers"][str(entry.get("id"))] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for entry in index.get("works") or []:
        path = root / str(entry.get("path") or "")
        if path.is_file():
            bundle["works"][str(entry.get("id"))] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    payload = json.dumps(bundle, ensure_ascii=False, indent=2).encode("utf-8")
    settings = get_settings()
    digest, rel, _ = write_artifact(
        root=Path(settings.artifact_root),
        source_id=source.id,
        job_id=job.id,
        payload=payload,
        suffix="json",
    )
    art = FetchArtifact(
        job_id=job.id,
        source_id=source.id,
        content_hash=digest,
        content_type="application/json",
        storage_path=rel,
        source_url=f"file://{index_path}",
        byte_size=len(payload),
    )
    db.add(art)
    db.flush()

    for cid, raw in bundle["composers"].items():
        composer_id = str(raw.get("composer_id") or cid)
        row = db.get(ComposerEntity, composer_id)
        if row is None:
            row = ComposerEntity(id=composer_id)
            db.add(row)
        row.name_en = str(raw.get("name_en") or "")
        row.name_zh = str(raw.get("name_zh") or "")
        row.aliases_json = json.dumps(raw.get("aliases") or [], ensure_ascii=False)
        row.lifespan = str((raw.get("lifespan") or ""))

    for wid, raw in bundle["works"].items():
        work_id = str(raw.get("work_id") or wid)
        composer_id = str(raw.get("composer_id") or "")
        row = db.get(WorkEntity, work_id)
        if row is None:
            row = WorkEntity(id=work_id, composer_id=composer_id)
            db.add(row)
        row.composer_id = composer_id
        row.title_en = str(raw.get("canonical_title") or "")
        row.title_zh = str(raw.get("canonical_title_zh") or "")
        row.aulos_work_id = work_id
        row.catalog_numbers_json = json.dumps(raw.get("catalog_numbers") or [], ensure_ascii=False)
        row.facets_json = json.dumps(raw.get("facets") or {}, ensure_ascii=False)

        body = "\n".join(
            [
                row.title_en,
                row.title_zh,
                "Aliases: " + ", ".join(str(a) for a in (raw.get("aliases") or [])),
                "Catalog: " + ", ".join(str(a) for a in (raw.get("catalog_numbers") or [])),
                "Facets: " + json.dumps(raw.get("facets") or {}, ensure_ascii=False),
                "Provenance: " + json.dumps(raw.get("provenance") or {}, ensure_ascii=False),
            ]
        )
        doc = KnowledgeDocument(
            title=row.title_en or work_id,
            entity_type="work",
            entity_id=work_id,
            aulos_work_id=work_id,
            body=body,
            status=document_status_for_source(source),
            source_id=source.id,
            artifact_id=art.id,
            job_id=job.id,
            extractor_version=EXTRACTOR_VERSION,
            license_class=source.license_class,
        )
        db.add(doc)
        db.flush()
        db.add(
            KnowledgeChunk(
                document_id=doc.id,
                section="identity",
                text=body,
                aulos_work_id=work_id,
                embedding_json="[]",
            )
        )
    db.commit()
