from pydantic import BaseModel


class SessionSummary(BaseModel):
    session_id: str
    user_id: str
    created_at: str | None = None
    updated_at: str | None = None


class SessionMessage(BaseModel):
    role: str
    content: str
    created_at: str | None = None
