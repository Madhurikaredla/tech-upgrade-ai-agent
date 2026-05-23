from typing import Any

from fastapi import APIRouter, Depends, Query, status

from packages.agents.program_config.schemas import AgentChatRequest, AgentChatResponse

from ..repositories.session_repository import SessionRepository
from ..services import program_config_service

router = APIRouter(prefix="/api/v1/program-config", tags=["program-config"])


def _get_session_repo() -> SessionRepository:
    return SessionRepository()


@router.post("/chat", response_model=AgentChatResponse)
async def chat(request: AgentChatRequest) -> AgentChatResponse:
    return await program_config_service.chat(request)


@router.get("/sessions", response_model=list[dict[str, Any]])
async def list_sessions(
    userId: str = Query(...),
    repo: SessionRepository = Depends(_get_session_repo),
) -> list[dict[str, Any]]:
    return await repo.list_sessions(userId)


@router.get("/sessions/{session_id}/messages", response_model=list[dict[str, Any]])
async def get_session_messages(
    session_id: str,
    repo: SessionRepository = Depends(_get_session_repo),
) -> list[dict[str, Any]]:
    return await repo.get_display_messages(session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    repo: SessionRepository = Depends(_get_session_repo),
) -> None:
    await repo.delete_session(session_id)
