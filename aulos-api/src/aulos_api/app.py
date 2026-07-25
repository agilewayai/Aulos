from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aulos_api.config import get_settings
from aulos_api.routes import chat_router, health_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Aulos API Gateway",
        version="0.1.0",
        description="HTTP gateway for Aulos web GUI, agents, and MCP integrations",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
