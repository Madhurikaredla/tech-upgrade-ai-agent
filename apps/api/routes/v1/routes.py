"""V1 API router — aggregates all /api/v1/* routers."""

from fastapi import APIRouter

from ...controllers import agent_controller, auth_controller, program_config_controller

v1_router = APIRouter()

v1_router.include_router(auth_controller.router)
v1_router.include_router(agent_controller.router)
v1_router.include_router(program_config_controller.router)
