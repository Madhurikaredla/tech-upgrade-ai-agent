from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalyzedPayload(BaseModel):
    payload_id: str
    summary: str
    risk_level: RiskLevel
    details: dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0


class AnalysisRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    user_id: str = ""
    payload_id: str = ""


class AnalysisResponse(BaseModel):
    success: bool = True
    data: AnalyzedPayload | None = None
    message: str = ""
    request_id: str = ""
