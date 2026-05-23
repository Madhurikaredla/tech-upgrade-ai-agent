import uuid

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class InputPayload(BaseModel):
    payload_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: PromptRequest
    metadata: dict[str, str] = Field(default_factory=dict)
