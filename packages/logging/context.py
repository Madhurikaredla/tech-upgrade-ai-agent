import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
bearer_token_var: ContextVar[str] = ContextVar("bearer_token", default="")
active_role_var: ContextVar[str] = ContextVar("active_role", default="")


def get_request_id() -> str:
    return request_id_var.get() or str(uuid.uuid4())


def get_user_id() -> str:
    return user_id_var.get()


def get_bearer_token() -> str:
    return bearer_token_var.get()


def set_request_id(value: str) -> None:
    request_id_var.set(value)


def set_user_id(value: str) -> None:
    user_id_var.set(value)


def set_bearer_token(value: str) -> None:
    bearer_token_var.set(value)


def get_active_role() -> str:
    return active_role_var.get()


def set_active_role(value: str) -> None:
    active_role_var.set(value)
