import pytest

from packages.models.input import InputPayload, PromptRequest
from packages.agents.analysis.schemas import AnalysisResponse as AgentResponse, AnalyzedPayload, RiskLevel


def test_prompt_request_defaults():
    req = PromptRequest(prompt="hello world", user_id="u1")
    assert req.session_id  # auto-generated UUID


def test_input_payload_defaults():
    req = PromptRequest(prompt="test", user_id="u1")
    payload = InputPayload(request=req)
    assert payload.payload_id
    assert payload.metadata == {}


def test_analyzed_payload_round_trip():
    ap = AnalyzedPayload(
        payload_id="pid-1",
        summary="All looks fine.",
        risk_level=RiskLevel.LOW,
    )
    assert ap.model_dump()["risk_level"] == "low"


def test_agent_response_default_success():
    resp = AgentResponse()
    assert resp.success is True
    assert resp.data is None
