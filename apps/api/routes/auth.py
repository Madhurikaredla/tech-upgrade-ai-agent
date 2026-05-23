import httpx
import logfire
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from packages.auth.service import (
    resend_otp_email,
    resend_otp_phone,
    send_otp_email,
    send_otp_phone,
    verify_otp_email,
    verify_otp_phone,
)
from packages.logging.context import get_request_id

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    login_type: str = "phone"
    phone_number: str | None = None
    country_code: str = "+91"
    email: str | None = None


class OtpVerifyRequest(BaseModel):
    login_type: str = "phone"
    phone_number: str | None = None
    country_code: str = "+91"
    email: str | None = None
    otp: str


class ResendOtpRequest(BaseModel):
    login_type: str = "phone"
    phone_number: str | None = None
    country_code: str = "+91"
    email: str | None = None


def _nestjs_error(exc: httpx.HTTPStatusError) -> HTTPException:
    try:
        detail = exc.response.json().get("message", exc.response.text)
    except Exception:
        detail = exc.response.text or "Auth service error"
    return HTTPException(status_code=exc.response.status_code, detail=detail)


def _unreachable(exc: httpx.RequestError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Auth service unreachable — {exc}",
    )


@router.post("/login")
async def login(request: LoginRequest) -> dict:
    """Send OTP via NestJS auth/login."""
    with logfire.span("route.auth.login", request_id=get_request_id()):
        try:
            if request.login_type == "phone":
                if not request.phone_number:
                    raise HTTPException(status_code=400, detail="phone_number is required")
                result = await send_otp_phone(request.phone_number, request.country_code)
            else:
                if not request.email:
                    raise HTTPException(status_code=400, detail="email is required")
                result = await send_otp_email(request.email)
        except httpx.HTTPStatusError as exc:
            raise _nestjs_error(exc) from exc
        except httpx.RequestError as exc:
            raise _unreachable(exc) from exc
        return {"message": "OTP sent successfully", "data": result}


@router.post("/verify-otp")
async def verify_otp(request: OtpVerifyRequest) -> dict:
    """Verify OTP via NestJS and return the NestJS token directly."""
    with logfire.span("route.auth.verify_otp", request_id=get_request_id()):
        try:
            if request.login_type == "phone":
                if not request.phone_number:
                    raise HTTPException(status_code=400, detail="phone_number is required")
                result = await verify_otp_phone(request.phone_number, request.otp, request.country_code)
            else:
                if not request.email:
                    raise HTTPException(status_code=400, detail="email is required")
                result = await verify_otp_email(request.email, request.otp)
        except httpx.HTTPStatusError as exc:
            raise _nestjs_error(exc) from exc
        except httpx.RequestError as exc:
            raise _unreachable(exc) from exc

        # NestJS token passed through as-is — UI stores and uses it directly
        logfire.info("auth.success", phone=request.phone_number)
        return result


@router.post("/resend-otp")
async def resend_otp(request: ResendOtpRequest) -> dict:
    """Resend OTP via NestJS auth/resend-otp."""
    with logfire.span("route.auth.resend_otp", request_id=get_request_id()):
        try:
            if request.login_type == "phone":
                if not request.phone_number:
                    raise HTTPException(status_code=400, detail="phone_number is required")
                result = await resend_otp_phone(request.phone_number, request.country_code)
            else:
                if not request.email:
                    raise HTTPException(status_code=400, detail="email is required")
                result = await resend_otp_email(request.email)
        except httpx.HTTPStatusError as exc:
            raise _nestjs_error(exc) from exc
        except httpx.RequestError as exc:
            raise _unreachable(exc) from exc
        return {"message": "OTP resent successfully", "data": result}
