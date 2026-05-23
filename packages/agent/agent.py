from pydantic_ai import Agent

from packages.config.model_factory import get_model
from packages.models.output import AnalyzedPayload
from packages.tools.data_tools import extract_entities, validate_data
from packages.tools.enrichment_tools import calculate_risk_score, enrich_context

from .prompts import SYSTEM_PROMPT

_agent: Agent[None, AnalyzedPayload] | None = None


def _build_agent() -> Agent[None, AnalyzedPayload]:
    return Agent(
        model=get_model(),
        result_type=AnalyzedPayload,
        system_prompt=SYSTEM_PROMPT,
        tools=[validate_data, extract_entities, enrich_context, calculate_risk_score],
    )


def get_agent() -> Agent[None, AnalyzedPayload]:
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent
