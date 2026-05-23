"""Factory helpers for building APIResponse instances."""

from __future__ import annotations

from typing import TypeVar

from packages.logging.context import get_request_id

from ..schemas.api_response import APIResponse, ErrorDetail

T = TypeVar("T")


def success_response(data: T, request_id: str = "") -> APIResponse[T]:
    return APIResponse(
        success=True,
        data=data,
        request_id=request_id or get_request_id(),
    )


def error_response(
    code: str,
    message: str,
    status_code: int = 500,
    request_id: str = "",
) -> APIResponse[None]:
    return APIResponse(
        success=False,
        data=None,
        error=ErrorDetail(code=code, message=message),
        request_id=request_id or get_request_id(),
    )
