from pydantic import BaseModel


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


class OtpSentResponse(BaseModel):
    message: str
    data: dict


class OtpResendResponse(BaseModel):
    message: str
    data: dict
