from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aulos_knowledge.config import get_settings
from aulos_knowledge import db as db_mod
from aulos_knowledge.routes import admin_router, router
from aulos_knowledge.seed import seed_default_sources


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    Path(settings.artifact_root).mkdir(parents=True, exist_ok=True)
    db_url = settings.db_url
    if db_url.startswith("sqlite:///./"):
        Path("data").mkdir(parents=True, exist_ok=True)
    db_mod.init_db(db_url)
    assert db_mod.SessionLocal is not None
    db = db_mod.SessionLocal()
    try:
        seed_default_sources(db)
    finally:
        db.close()
    from aulos_knowledge.job_queue import start_job_drain_loop, stop_job_drain_loop

    start_job_drain_loop()
    try:
        yield
    finally:
        stop_job_drain_loop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5090",
            "http://127.0.0.1:5091",
            "http://127.0.0.1:5092",
            "https://aulos.purezen.ai",
            "https://aulos-ops.purezen.ai",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.include_router(admin_router)
    return app


app = create_app()
