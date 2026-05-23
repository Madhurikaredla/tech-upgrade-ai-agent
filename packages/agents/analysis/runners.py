from collections.abc import AsyncIterator

import logfire

from packages.logging.context import get_request_id
from packages.logging.decorators import log_agent_run
from packages.models.input import InputPayload

from .agent import get_analysis_agent
from .prompts import ANALYSIS_PROMPT_TEMPLATE
from .schemas import AnalysisResponse


@log_agent_run("analysis")
async def run_analysis(payload: InputPayload) -> AnalysisResponse:
    agent = get_analysis_agent()
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        payload_id=payload.payload_id,
        content=payload.request.prompt,
        metadata=str(payload.metadata),
    )

    with logfire.span("agent.run", payload_id=payload.payload_id):
        result = await agent.run(prompt)

    return AnalysisResponse(
        success=True,
        data=result.output,
        request_id=get_request_id(),
    )


async def stream_analysis(payload: InputPayload) -> AsyncIterator[str]:
    agent = get_analysis_agent()
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        payload_id=payload.payload_id,
        content=payload.request.prompt,
        metadata=str(payload.metadata),
    )

    async with agent.run_stream(prompt) as result:
        async for chunk in result.stream_text():
            yield chunk
