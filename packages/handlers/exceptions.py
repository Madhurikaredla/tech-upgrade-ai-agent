"""Typed exception hierarchy for ai-platform.

All application errors should subclass AppError so they are handled
consistently by the FastAPI exception handlers in http_handlers.py.
"""


class AppError(Exception):
    """Base class for all application errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred") -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", identifier: str = "") -> None:
        suffix = f" '{identifier}'" if identifier else ""
        super().__init__(f"{resource}{suffix} not found")


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message)


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"

    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__(message)


class AgentProcessingError(AppError):
    """Raised when the AI agent fails to process a request."""

    status_code = 502
    code = "AGENT_ERROR"

    def __init__(self, message: str = "Agent processing failed", agent: str = "") -> None:
        prefix = f"[{agent}] " if agent else ""
        super().__init__(f"{prefix}{message}")
        self.agent = agent


class ExternalServiceError(AppError):
    """Raised when a downstream service (NestJS, DB) returns an error."""

    status_code = 502
    code = "EXTERNAL_SERVICE_ERROR"

    def __init__(self, service: str, message: str = "External service error") -> None:
        super().__init__(f"{service}: {message}")
        self.service = service


class ConfigurationError(AppError):
    """Raised when required configuration is missing or invalid."""

    status_code = 500
    code = "CONFIGURATION_ERROR"
