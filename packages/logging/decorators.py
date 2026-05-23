import asyncio
import functools
from typing import Any, Callable, TypeVar

import logfire

from .context import get_request_id, get_user_id

F = TypeVar("F", bound=Callable[..., Any])


def log_span(name: str, **extra_attrs: Any) -> Callable[[F], F]:
    """Wrap any async or sync callable in a named logfire span."""

    def decorator(func: F) -> F:
        base_attrs = extra_attrs

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with logfire.span(name, request_id=get_request_id(), user_id=get_user_id(), **base_attrs):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with logfire.span(name, request_id=get_request_id(), user_id=get_user_id(), **base_attrs):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper  # type: ignore[return-value]

    return decorator


def log_agent_run(agent_name: str) -> Callable[[F], F]:
    """Wrap an async agent runner in a named span that includes agent metadata."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            with logfire.span(
                f"agent_run:{agent_name}",
                **{"agent.name": agent_name, "request_id": get_request_id(), "user_id": get_user_id()},
            ):
                return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
