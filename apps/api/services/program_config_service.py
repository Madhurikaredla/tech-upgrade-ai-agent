import logfire
from fastapi import HTTPException, status

from packages.agents.program_config.runners import run_chat
from packages.agents.program_config.schemas import AgentChatRequest, AgentChatResponse
from packages.logging.context import get_request_id


async def chat(request: AgentChatRequest) -> AgentChatResponse:
    with logfire.span("service.program_config.chat", session_id=request.session_id):
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
