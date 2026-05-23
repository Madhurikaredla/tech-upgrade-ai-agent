import logfire
from fastapi import APIRouter

from packages.config.settings import get_settings

from ..dto.health_dto import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    logfire.debug("health check")
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)
