import logfire
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from packages.agent.runners import run_analysis, stream_analysis
from packages.logging.context import get_request_id
from packages.models.input import InputPayload, PromptRequest
from packages.models.output import AgentResponse

router = APIRouter(prefix="/api/v1", tags=["agent"])


@router.post("/analyze", response_model=AgentResponse)
async def analyze(request: PromptRequest) -> AgentResponse:
    with logfire.span("route.analyze", user_id=request.user_id):
        payload = InputPayload(request=request)
        try:
            return await run_analysis(payload)
        except Exception as exc:
            logfire.error("analysis failed", error=str(exc), request_id=get_request_id())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Analysis failed — see logs for details",
            ) from exc


@router.post("/prompt", response_model=AgentResponse)
async def prompt(request: PromptRequest) -> AgentResponse:
    """UI-facing alias for /analyze."""
    return await analyze(request)


@router.post("/chat")
async def chat_stream(request: PromptRequest) -> StreamingResponse:
    """Server-sent events stream of the agent's token output."""
    payload = InputPayload(request=request)

    async def event_generator():
        async for chunk in stream_analysis(payload):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
