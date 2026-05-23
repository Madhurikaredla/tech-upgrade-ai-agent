import httpx
from fastapi import HTTPException, status


def nestjs_error(exc: httpx.HTTPStatusError) -> HTTPException:
    try:
        detail = exc.response.json().get("message", exc.response.text)
    except Exception:
        detail = exc.response.text or "Auth service error"
    return HTTPException(status_code=exc.response.status_code, detail=detail)


def service_unreachable(exc: httpx.RequestError, service: str = "Service") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{service} unreachable — {exc}",
    )
