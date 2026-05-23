"""In-memory session store for program config agent conversations.

Each session tracks stage, partial DTO, and pydantic-ai message history.
Message histories are stored separately (not in the Pydantic model) because
they contain typed pydantic-ai objects that don't round-trip cleanly through JSON.
"""

import threading
from typing import Any

from .models import SessionState

_sessions: dict[str, SessionState] = {}
_message_histories: dict[str, list[Any]] = {}
_lock = threading.Lock()


def get_or_create(session_id: str, user_id: str = "") -> SessionState:
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = SessionState(session_id=session_id, user_id=user_id)
        return _sessions[session_id]


def save(session: SessionState) -> None:
    with _lock:
        _sessions[session.session_id] = session


def get_message_history(session_id: str) -> list[Any]:
    with _lock:
        return _message_histories.get(session_id, [])


def save_message_history(session_id: str, messages: list[Any]) -> None:
    with _lock:
        _message_histories[session_id] = messages
