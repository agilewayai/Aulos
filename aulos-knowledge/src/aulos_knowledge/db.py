from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SourceAuthority(Base):
    __tablename__ = "source_authorities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    tier: Mapped[str] = mapped_column(String(8), default="A")  # S/A/B
    connector: Mapped[str] = mapped_column(String(64), default="")
    base_urls_json: Mapped[str] = mapped_column(Text, default="[]")
    license_class: Mapped[str] = mapped_column(String(64), default="unknown")
    rate_limit_qps: Mapped[float] = mapped_column(Float, default=1.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    owner: Mapped[str] = mapped_column(String(128), default="aulos")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FetchJob(Base):
    __tablename__ = "fetch_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(64), ForeignKey("source_authorities.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued|running|succeeded|failed
    params_json: Mapped[str] = mapped_column(Text, default="{}")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped[SourceAuthority] = relationship()


class FetchArtifact(Base):
    __tablename__ = "fetch_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("fetch_jobs.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    content_type: Mapped[str] = mapped_column(String(128), default="application/json")
    storage_path: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    byte_size: Mapped[int] = mapped_column(Integer, default=0)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ComposerEntity(Base):
    __tablename__ = "composers"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name_en: Mapped[str] = mapped_column(String(255), default="")
    name_zh: Mapped[str] = mapped_column(String(255), default="")
    aliases_json: Mapped[str] = mapped_column(Text, default="[]")
    external_ids_json: Mapped[str] = mapped_column(Text, default="{}")
    lifespan: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkEntity(Base):
    __tablename__ = "works"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    composer_id: Mapped[str] = mapped_column(String(128), ForeignKey("composers.id"), index=True)
    title_en: Mapped[str] = mapped_column(String(512), default="")
    title_zh: Mapped[str] = mapped_column(String(512), default="")
    aulos_work_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    catalog_numbers_json: Mapped[str] = mapped_column(Text, default="[]")
    facets_json: Mapped[str] = mapped_column(Text, default="{}")
    external_ids_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RecordingEntity(Base):
    __tablename__ = "recordings"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    work_id: Mapped[str] = mapped_column(String(160), ForeignKey("works.id"), index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    artists_json: Mapped[str] = mapped_column(Text, default="[]")
    label: Mapped[str] = mapped_column(String(255), default="")
    year: Mapped[str] = mapped_column(String(32), default="")
    external_ids_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MediaAsset(Base):
    """Durable crawled media: images, free/PD audio, and music-file metadata JSON."""

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(32), default="image", index=True)  # image|audio|meta
    title: Mapped[str] = mapped_column(String(512), default="")
    entity_type: Mapped[str] = mapped_column(String(32), default="", index=True)
    entity_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    aulos_work_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    source_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    artifact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fetch_artifacts.id"), nullable=True)
    job_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fetch_jobs.id"), nullable=True)
    source_url: Mapped[str] = mapped_column(Text, default="")
    storage_path: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    content_type: Mapped[str] = mapped_column(String(128), default="")
    byte_size: Mapped[int] = mapped_column(Integer, default=0)
    license_class: Mapped[str] = mapped_column(String(128), default="")
    meta_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KnowledgeDocument(Base):
    __tablename__ = "kb_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    entity_type: Mapped[str] = mapped_column(String(32), default="work")  # work|composer|recording|history
    entity_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    aulos_work_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="published")  # published|quarantine
    source_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    artifact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fetch_artifacts.id"), nullable=True)
    job_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fetch_jobs.id"), nullable=True)
    extractor_version: Mapped[str] = mapped_column(String(64), default="0.1.0")
    license_class: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KnowledgeChunk(Base):
    __tablename__ = "kb_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("kb_documents.id"), index=True)
    section: Mapped[str] = mapped_column(String(64), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    embedding_json: Mapped[str] = mapped_column(Text, default="[]")
    aulos_work_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


_engine = None
SessionLocal = None


def init_db(url: str):
    global _engine, SessionLocal
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _engine = create_engine(url, future=True, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(_engine)
    return _engine


def get_session():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
