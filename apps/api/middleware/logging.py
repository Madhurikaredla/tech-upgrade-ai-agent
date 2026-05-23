import time
import uuid

import logfire
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from packages.logging.context import set_active_role, set_bearer_token, set_request_id, set_user_id


class LogfireLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        user_id = request.headers.get("X-User-ID", "")

        # Forward the caller's Bearer token to downstream NestJS calls
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""

        active_role = request.headers.get("active-role", "")

        set_request_id(request_id)
        set_user_id(user_id)
        set_bearer_token(token)
        set_active_role(active_role)

        start = time.perf_counter()

        with logfire.span(
            "http.request",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
            user_id=user_id,
        ):
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            logfire.info(
                "request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
                user_id=user_id,
            )

        response.headers["X-Request-ID"] = request_id
        return response
