import logfire
from fastapi import APIRouter
from pydantic import BaseModel

from packages.config.settings import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    logfire.debug("health check")
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)
