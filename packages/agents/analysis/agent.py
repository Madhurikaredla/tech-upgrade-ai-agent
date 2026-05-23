from pydantic_ai import Agent

from packages.config.model_factory import get_model

from .prompts import SYSTEM_PROMPT
from .schemas import AnalyzedPayload
from .tools import calculate_risk_score, enrich_context, extract_entities, validate_data

_agent: Agent[None, AnalyzedPayload] | None = None


def _build_agent() -> Agent[None, AnalyzedPayload]:
    return Agent(
        model=get_model(),
        output_type=AnalyzedPayload,
        system_prompt=SYSTEM_PROMPT,
        tools=[validate_data, extract_entities, enrich_context, calculate_risk_score],
    )


def get_analysis_agent() -> Agent[None, AnalyzedPayload]:
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent
