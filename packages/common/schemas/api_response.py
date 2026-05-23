"""Unified APIResponse[T] wrapper — matches the envelope used by NestJS downstream.

Every API endpoint must wrap its return value in this schema:

    @router.get("/programs", response_model=APIResponse[list[ProgramSummary]])
    async def list_programs() -> APIResponse[list[ProgramSummary]]:
        data = await program_service.list()
        return success_response(data)
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: ErrorDetail | None = None
    request_id: str = ""


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
