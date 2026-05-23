from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from packages.agents.analysis.schemas import AnalysisResponse
from packages.models.input import PromptRequest

from ..services import agent_service

router = APIRouter(prefix="/api/v1", tags=["agent"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: PromptRequest) -> AnalysisResponse:
    return await agent_service.analyze(request)


@router.post("/prompt", response_model=AnalysisResponse)
async def prompt(request: PromptRequest) -> AnalysisResponse:
    """UI-facing alias for /analyze."""
    return await agent_service.analyze(request)


@router.post("/chat")
async def chat_stream(request: PromptRequest) -> StreamingResponse:
    return await agent_service.chat_stream(request)
