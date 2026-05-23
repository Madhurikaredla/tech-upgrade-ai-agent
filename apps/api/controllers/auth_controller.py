from fastapi import APIRouter

from ..dto.auth_dto import LoginRequest, OtpVerifyRequest, ResendOtpRequest
from ..services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(request: LoginRequest) -> dict:
    return await auth_service.login(request)


@router.post("/verify-otp")
async def verify_otp(request: OtpVerifyRequest) -> dict:
    return await auth_service.verify_otp(request)


@router.post("/resend-otp")
async def resend_otp(request: ResendOtpRequest) -> dict:
    return await auth_service.resend_otp(request)
