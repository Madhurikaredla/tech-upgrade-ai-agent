import logfire
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from packages.agents.analysis.runners import run_analysis, stream_analysis
from packages.agents.analysis.schemas import AnalysisResponse
from packages.logging.context import get_request_id
from packages.models.input import InputPayload, PromptRequest


async def analyze(request: PromptRequest) -> AnalysisResponse:
    with logfire.span("service.agent.analyze", user_id=request.user_id):
        payload = InputPayload(request=request)
        try:
            return await run_analysis(payload)
        except Exception as exc:
            logfire.error("analysis failed", error=str(exc), request_id=get_request_id())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Analysis failed — see logs for details",
            ) from exc


async def chat_stream(request: PromptRequest) -> StreamingResponse:
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
