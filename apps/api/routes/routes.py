"""Root router — includes /health and all versioned API routers."""

from fastapi import APIRouter

from ..controllers.health_controller import router as health_router
from .v1.routes import v1_router

root_router = APIRouter()

root_router.include_router(health_router)
root_router.include_router(v1_router)
