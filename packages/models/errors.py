from pydantic import BaseModel


class AppError(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ValidationError(AppError):
    field: str | None = None
