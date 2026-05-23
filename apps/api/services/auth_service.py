import httpx
import logfire
from fastapi import HTTPException

from packages.auth.service import (
    resend_otp_email,
    resend_otp_phone,
    send_otp_email,
    send_otp_phone,
    verify_otp_email,
    verify_otp_phone,
)
from packages.logging.context import get_request_id

from ..common.errors import nestjs_error, service_unreachable
from ..dto.auth_dto import LoginRequest, OtpVerifyRequest, ResendOtpRequest


async def login(request: LoginRequest) -> dict:
    with logfire.span("service.auth.login", request_id=get_request_id()):
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
            raise nestjs_error(exc) from exc
        except httpx.RequestError as exc:
            raise service_unreachable(exc, "Auth service") from exc
        return {"message": "OTP sent successfully", "data": result}


async def verify_otp(request: OtpVerifyRequest) -> dict:
    with logfire.span("service.auth.verify_otp", request_id=get_request_id()):
        try:
            if request.login_type == "phone":
                if not request.phone_number:
                    raise HTTPException(status_code=400, detail="phone_number is required")
                result = await verify_otp_phone(
                    request.phone_number, request.otp, request.country_code
                )
            else:
                if not request.email:
                    raise HTTPException(status_code=400, detail="email is required")
                result = await verify_otp_email(request.email, request.otp)
        except httpx.HTTPStatusError as exc:
            raise nestjs_error(exc) from exc
        except httpx.RequestError as exc:
            raise service_unreachable(exc, "Auth service") from exc
        logfire.info("auth.success", phone=request.phone_number)
        return result


async def resend_otp(request: ResendOtpRequest) -> dict:
    with logfire.span("service.auth.resend_otp", request_id=get_request_id()):
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
            raise nestjs_error(exc) from exc
        except httpx.RequestError as exc:
            raise service_unreachable(exc, "Auth service") from exc
        return {"message": "OTP resent successfully", "data": result}
