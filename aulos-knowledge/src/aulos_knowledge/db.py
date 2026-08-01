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
    # REQ-008 Authority Source Registry
    verification_status: Mapped[str] = mapped_column(String(32), default="candidate")
    # candidate|review|verified|rejected|suspended
    verified_by: Mapped[str] = mapped_column(String(128), default="")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tos_notes: Mapped[str] = mapped_column(Text, default="")
    attribution_template: Mapped[str] = mapped_column(Text, default="")
    allowed_path_prefixes_json: Mapped[str] = mapped_column(Text, default="[]")
    connector_semver: Mapped[str] = mapped_column(String(32), default="")
    origin_class: Mapped[str] = mapped_column(String(32), default="encyclopedia")
    # encyclopedia|identity_seed|media|editorial
    registry_revision: Mapped[str] = mapped_column(String(64), default="")
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
    era: Mapped[str] = mapped_column(String(64), default="")
    summary_en: Mapped[str] = mapped_column(Text, default="")
    summary_zh: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ComposerLifeEvent(Base):
    """REQ-010 — dated life / career event on a composer timeline."""

    __tablename__ = "composer_life_events"

    id: Mapped[str] = mapped_column(String(220), primary_key=True)
    composer_id: Mapped[str] = mapped_column(String(128), ForeignKey("composers.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(48), default="other", index=True)
    # birth|death|baptism|education|appointment|residence|marriage|travel|premiere|composition_milestone|other
    title_en: Mapped[str] = mapped_column(String(512), default="")
    title_zh: Mapped[str] = mapped_column(String(512), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    date_start: Mapped[str] = mapped_column(String(32), default="", index=True)
    date_end: Mapped[str] = mapped_column(String(32), default="")
    place_label: Mapped[str] = mapped_column(String(255), default="")
    place_qid: Mapped[str] = mapped_column(String(32), default="")
    significance: Mapped[str] = mapped_column(String(16), default="minor")  # major|minor
    external_ids_json: Mapped[str] = mapped_column(Text, default="{}")
    source_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    artifact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fetch_artifacts.id"), nullable=True)
    job_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fetch_jobs.id"), nullable=True)
    sort_key: Mapped[str] = mapped_column(String(64), default="", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkEntity(Base):
    __tablename__ = "works"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    composer_id: Mapped[str] = mapped_column(String(128), ForeignKey("composers.id"), index=True)
    parent_work_id: Mapped[str | None] = mapped_column(
        String(160), ForeignKey("works.id"), nullable=True, index=True
    )
    work_kind: Mapped[str] = mapped_column(String(32), default="work")
    # work|collection|cycle|movement|arrangement
    title_en: Mapped[str] = mapped_column(String(512), default="")
    title_zh: Mapped[str] = mapped_column(String(512), default="")
    aulos_work_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    catalog_numbers_json: Mapped[str] = mapped_column(Text, default="[]")
    facets_json: Mapped[str] = mapped_column(Text, default="{}")
    external_ids_json: Mapped[str] = mapped_column(Text, default="{}")
    year_start: Mapped[str] = mapped_column(String(16), default="")
    year_end: Mapped[str] = mapped_column(String(16), default="")
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
    status: Mapped[str] = mapped_column(String(32), default="quarantine")  # published|quarantine
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


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    trigger: Mapped[str] = mapped_column(String(64), default="ops")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    suite_revision: Mapped[str] = mapped_column(String(64), default="")
    registry_revision: Mapped[str] = mapped_column(String(64), default="")
    report_json: Mapped[str] = mapped_column(Text, default="{}")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BenchmarkDiagnosis(Base):
    __tablename__ = "benchmark_diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    benchmark_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark_runs.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="open")
    diagnosis_json: Mapped[str] = mapped_column(Text, default="{}")
    markdown: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SourceDiscoveryRun(Base):
    __tablename__ = "source_discovery_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    trigger: Mapped[str] = mapped_column(String(64), default="ops")
    composer_id: Mapped[str] = mapped_column(String(128), default="")
    wikidata_qid: Mapped[str] = mapped_column(String(32), default="")
    graph_json: Mapped[str] = mapped_column(Text, default="{}")
    candidates_json: Mapped[str] = mapped_column(Text, default="[]")
    stats_json: Mapped[str] = mapped_column(Text, default="{}")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImprovementAction(Base):
    __tablename__ = "improvement_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    diagnosis_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark_diagnoses.id"), index=True)
    item_id: Mapped[str] = mapped_column(String(128), default="")
    action_type: Mapped[str] = mapped_column(String(64), default="")
    layer: Mapped[str] = mapped_column(String(8), default="L1")
    auto_safe: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="proposed")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


_engine = None
SessionLocal = None


def init_db(url: str):
    global _engine, SessionLocal
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _engine = create_engine(url, future=True, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(_engine)
    apply_source_authority_patches(_engine)
    apply_benchmark_run_patches(_engine)
    apply_composer_dossier_patches(_engine)
    return _engine


def apply_source_authority_patches(engine) -> list[str]:
    """Add REQ-008 columns on existing source_authorities tables."""
    from sqlalchemy import inspect, text

    applied: list[str] = []
    insp = inspect(engine)
    if not insp.has_table("source_authorities"):
        return applied
    cols = {c["name"] for c in insp.get_columns("source_authorities")}
    dialect = engine.dialect.name
    additions: list[tuple[str, str]] = [
        ("verification_status", "VARCHAR(32) DEFAULT 'candidate'"),
        ("verified_by", "VARCHAR(128) DEFAULT ''"),
        ("verified_at", "TIMESTAMP" if dialect != "sqlite" else "DATETIME"),
        ("tos_notes", "TEXT DEFAULT ''"),
        ("attribution_template", "TEXT DEFAULT ''"),
        ("allowed_path_prefixes_json", "TEXT DEFAULT '[]'"),
        ("connector_semver", "VARCHAR(32) DEFAULT ''"),
        ("origin_class", "VARCHAR(32) DEFAULT 'encyclopedia'"),
        ("registry_revision", "VARCHAR(64) DEFAULT ''"),
    ]
    with engine.begin() as conn:
        for name, col_type in additions:
            if name in cols:
                continue
            conn.execute(text(f"ALTER TABLE source_authorities ADD COLUMN {name} {col_type}"))
            applied.append(f"source_authorities.{name}")
        # Backfill known production sources to verified if still empty/candidate after upgrade
        if "verification_status" in cols or any(a.endswith("verification_status") for a in applied):
            conn.execute(
                text(
                    "UPDATE source_authorities SET verification_status = 'verified', "
                    "origin_class = CASE id WHEN 'catalog-local' THEN 'identity_seed' ELSE COALESCE(NULLIF(origin_class, ''), 'encyclopedia') END "
                    "WHERE id IN ('catalog-local', 'wikidata', 'musicbrainz') "
                    "AND (verification_status IS NULL OR verification_status = '' OR verification_status = 'candidate')"
                )
            )
    return applied


def apply_benchmark_run_patches(engine) -> list[str]:
    """Add async benchmark columns on existing benchmark_runs tables."""
    from sqlalchemy import inspect, text

    applied: list[str] = []
    insp = inspect(engine)
    if not insp.has_table("benchmark_runs"):
        return applied
    cols = {c["name"] for c in insp.get_columns("benchmark_runs")}
    dialect = engine.dialect.name
    ts_type = "TIMESTAMP" if dialect != "sqlite" else "DATETIME"
    additions: list[tuple[str, str]] = [
        ("error", "TEXT DEFAULT ''"),
        ("started_at", ts_type),
        ("finished_at", ts_type),
    ]
    with engine.begin() as conn:
        for name, col_type in additions:
            if name in cols:
                continue
            conn.execute(text(f"ALTER TABLE benchmark_runs ADD COLUMN {name} {col_type}"))
            applied.append(f"benchmark_runs.{name}")
    return applied


def apply_composer_dossier_patches(engine) -> list[str]:
    """REQ-010 — era/summary on composers; parent/work_kind/years on works."""
    from sqlalchemy import inspect, text

    applied: list[str] = []
    insp = inspect(engine)
    dialect = engine.dialect.name

    if insp.has_table("composers"):
        cols = {c["name"] for c in insp.get_columns("composers")}
        additions: list[tuple[str, str]] = [
            ("era", "VARCHAR(64) DEFAULT ''"),
            ("summary_en", "TEXT DEFAULT ''"),
            ("summary_zh", "TEXT DEFAULT ''"),
        ]
        with engine.begin() as conn:
            for name, col_type in additions:
                if name in cols:
                    continue
                conn.execute(text(f"ALTER TABLE composers ADD COLUMN {name} {col_type}"))
                applied.append(f"composers.{name}")

    if insp.has_table("works"):
        cols = {c["name"] for c in insp.get_columns("works")}
        additions = [
            ("parent_work_id", "VARCHAR(160)"),
            ("work_kind", "VARCHAR(32) DEFAULT 'work'"),
            ("year_start", "VARCHAR(16) DEFAULT ''"),
            ("year_end", "VARCHAR(16) DEFAULT ''"),
        ]
        with engine.begin() as conn:
            for name, col_type in additions:
                if name in cols:
                    continue
                conn.execute(text(f"ALTER TABLE works ADD COLUMN {name} {col_type}"))
                applied.append(f"works.{name}")

    # composer_life_events is created via create_all; no column patch needed for greenfield.
    _ = dialect
    return applied


def get_session():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
