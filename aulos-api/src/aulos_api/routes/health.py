from fastapi import APIRouter

from aulos_api.config import get_settings
from aulos_api.services import AgentProxy

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    proxy = AgentProxy(settings)
    backends = await proxy.health_backends()
    return {
        "status": "ok",
        "service": "aulos-api",
        "version": "0.1.0",
        "backends": backends,
    }
