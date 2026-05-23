from pydantic_ai import Agent

from packages.config.model_factory import get_model

from .prompts import SYSTEM_PROMPT
from .schemas import ProgramConfigTurn

_agent: Agent[None, ProgramConfigTurn] | None = None


def _build_agent() -> Agent[None, ProgramConfigTurn]:
    return Agent(
        model=get_model(),
        output_type=ProgramConfigTurn,
        system_prompt=SYSTEM_PROMPT,
        model_settings={"temperature": 0},
    )


def get_program_config_agent() -> Agent[None, ProgramConfigTurn]:
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent
