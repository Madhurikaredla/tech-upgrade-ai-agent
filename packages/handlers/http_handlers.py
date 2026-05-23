"""FastAPI exception handlers — registered in main.py at startup.

All handlers return the standard APIResponse envelope so clients always
receive a consistent error shape:

    {"success": false, "error": {"code": "...", "message": "..."}, "request_id": "..."}
"""

from __future__ import annotations

import logfire
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from packages.logging.context import get_request_id

from .exceptions import AppError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logfire.warning(
        "app_error",
        code=exc.code,
        message=exc.message,
        path=request.url.path,
        request_id=get_request_id(),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": exc.code, "message": exc.message},
            "request_id": get_request_id(),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logfire.warning(
        "http_exception",
        status=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        request_id=get_request_id(),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": "HTTP_ERROR", "message": str(exc.detail)},
            "request_id": get_request_id(),
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    logfire.warning(
        "validation_error",
        errors=errors,
        path=request.url.path,
        request_id=get_request_id(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    str(err["loc"]): err["msg"] for err in errors
                },
            },
            "request_id": get_request_id(),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logfire.exception(
        "unhandled_exception",
        path=request.url.path,
        request_id=get_request_id(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again or contact support.",
            },
            "request_id": get_request_id(),
        },
    )
