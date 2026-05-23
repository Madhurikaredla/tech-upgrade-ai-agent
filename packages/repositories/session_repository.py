"""SessionRepository — thin facade over the program_config agent repository.

Provides a class-based interface for routes and services that need to
query session state without depending directly on the agent internals.
"""

from __future__ import annotations

from typing import Any

from packages.agents.program_config import repository as _repo
from packages.agents.program_config.schemas import SessionState


class SessionRepository:
    async def get_or_create(self, session_id: str, user_id: str = "") -> SessionState:
        return await _repo.get_or_create(session_id, user_id)

    async def save(self, session: SessionState) -> None:
        await _repo.save(session)

    async def list_sessions(self, user_id: str) -> list[dict[str, Any]]:
        return await _repo.list_sessions(user_id)

    async def get_display_messages(self, session_id: str) -> list[dict[str, Any]]:
        return await _repo.get_display_messages(session_id)

    async def delete_session(self, session_id: str) -> None:
        await _repo.delete_session(session_id)
