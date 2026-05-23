"""Auth service — proxies all OTP operations to the NestJS auth API.

Auth API base : https://api.portal.dev.divami.com
Endpoints     :
  POST auth/login         — send OTP to phone / email
  POST auth/validate-otp  — verify OTP, returns NestJS token
  POST auth/resend-otp    — resend OTP

NestJS issues the token. We pass it straight through to the UI.
No secondary JWT is issued by this service.
"""

import httpx
import logfire
from passlib.context import CryptContext

from packages.config.settings import get_settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Password helpers (used only for local DB seed)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# ---------------------------------------------------------------------------
# NestJS proxy
# ---------------------------------------------------------------------------

def _nestjs_url(path: str) -> str:
    base = get_settings().nestjs_base_url.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


async def _post(path: str, body: dict) -> dict:
    url = _nestjs_url(path)
    with logfire.span("nestjs.auth_post", path=path):
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Send OTP
# ---------------------------------------------------------------------------

async def send_otp_phone(phone: str, country_code: str = "+91") -> dict:
    logfire.info("auth.send_otp", phone=phone)
    return await _post("auth/login", {
        "loginType": "phone",
        "phoneNumber": phone,
        "countryCode": country_code,
    })


async def send_otp_email(email: str) -> dict:
    logfire.info("auth.send_otp_email", email=email)
    return await _post("auth/login", {"loginType": "email", "email": email})


# ---------------------------------------------------------------------------
# Verify OTP — returns NestJS token as-is
# ---------------------------------------------------------------------------

async def verify_otp_phone(phone: str, otp: str, country_code: str = "+91") -> dict:
    logfire.info("auth.verify_otp", phone=phone)
    return await _post("auth/validate-otp", {
        "loginType": "phone",
        "phoneNumber": phone,
        "countryCode": country_code,
        "otp": otp,
    })


async def verify_otp_email(email: str, otp: str) -> dict:
    logfire.info("auth.verify_otp_email", email=email)
    return await _post("auth/validate-otp", {"loginType": "email", "email": email, "otp": otp})


# ---------------------------------------------------------------------------
# Resend OTP
# ---------------------------------------------------------------------------

async def resend_otp_phone(phone: str, country_code: str = "+91") -> dict:
    logfire.info("auth.resend_otp", phone=phone)
    return await _post("auth/resend-otp", {
        "loginType": "phone",
        "phoneNumber": phone,
        "countryCode": country_code,
    })


async def resend_otp_email(email: str) -> dict:
    logfire.info("auth.resend_otp_email", email=email)
    return await _post("auth/resend-otp", {"loginType": "email", "email": email})
