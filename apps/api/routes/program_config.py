from typing import Any

import logfire
from fastapi import APIRouter, HTTPException, Query, status

from packages.logging.context import get_request_id
from packages.program_config import db_session
from packages.program_config.models import AgentChatRequest, AgentChatResponse
from packages.program_config.runners import run_chat

router = APIRouter(prefix="/api/v1/program-config", tags=["program-config"])


@router.post("/chat", response_model=AgentChatResponse)
async def chat(request: AgentChatRequest) -> AgentChatResponse:
    """Single endpoint for the full program configuration conversation.

    The client sends every message here with the same session_id.
    The agent maintains stage and context across turns.

    Stages returned in the response:
      COLLECTING       — agent is gathering required fields
      PROGRAM_PREVIEW  — agent is awaiting admin confirmation to create
      PROGRAM_CREATED  — program written to DB (status: DRAFT)
      FORM_PREVIEW     — agent is awaiting admin approval of form questions
      FORM_ATTACHED    — questions attached to the program
      READY_TO_PUBLISH — awaiting admin 'publish' command
      PUBLISHED        — program is live
    """
    with logfire.span("route.program_config.chat", session_id=request.session_id):
        try:
            return await run_chat(request)
        except Exception as exc:
            logfire.exception(
                "program_config.chat failed",
                session_id=request.session_id,
                request_id=get_request_id(),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent error — see logs for details",
            ) from exc


@router.get("/sessions", response_model=list[dict[str, Any]])
async def list_sessions(userId: str = Query(...)) -> list[dict[str, Any]]:
    """List the 40 most-recent sessions for a user, newest first."""
    return await db_session.list_sessions(userId)


@router.get("/sessions/{session_id}/messages", response_model=list[dict[str, Any]])
async def get_session_messages(session_id: str) -> list[dict[str, Any]]:
    """Return the human-readable chat messages for a session."""
    return await db_session.get_display_messages(session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str) -> None:
    """Delete a session and its message history."""
    await db_session.delete_session(session_id)
