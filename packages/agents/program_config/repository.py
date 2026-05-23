"""DB-backed session repository for the program config agent.

Tables: agent_sessions, agent_message_history (see packages/db/session_tables.sql).
All public methods are async and return typed domain models — never raw DB rows.
"""

from __future__ import annotations

import json
from typing import Any

import logfire
from pydantic import TypeAdapter
from sqlalchemy import text

from packages.db.database import SessionLocal

from .schemas import SessionState

# ---------------------------------------------------------------------------
# pydantic-ai message serialisation helpers
# ---------------------------------------------------------------------------

try:
    from pydantic_ai.messages import ModelMessage as _ModelMessage  # type: ignore[attr-defined]

    _messages_ta: TypeAdapter[Any] = TypeAdapter(list[_ModelMessage])
    _HAS_TA = True
except Exception:
    _messages_ta = None  # type: ignore[assignment]
    _HAS_TA = False


def _serialise_messages(messages: list[Any]) -> str:
    if _HAS_TA and messages:
        try:
            return _messages_ta.dump_json(messages).decode()
        except Exception:
            logfire.warning("message_history.serialise_failed — storing empty")
    return "[]"


def _deserialise_messages(raw: str | None) -> list[Any]:
    if not raw or raw == "[]" or not _HAS_TA:
        return []
    try:
        return _messages_ta.validate_json(raw)
    except Exception:
        logfire.warning("message_history.deserialise_failed — returning empty")
        return []


# ---------------------------------------------------------------------------
# Public repository functions
# ---------------------------------------------------------------------------


async def get_or_create(session_id: str, user_id: str = "") -> SessionState:
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                text("SELECT state_json FROM agent_sessions WHERE session_id = :sid"),
                {"sid": session_id},
            )
            row = result.fetchone()

            if row and row[0]:
                try:
                    state = SessionState.model_validate_json(row[0])
                    state.session_id = session_id
                    if not state.user_id:
                        state.user_id = user_id
                    # Ensure program_type_key is always set so the type announcement
                    # never re-fires for sessions that already confirmed the type.
                    if state.partial_dto.sub_program_type and not state.program_type_key:
                        from packages.agents.program_config.db_lookup import normalize_admin_type
                        state.program_type_key = normalize_admin_type(
                            state.partial_dto.sub_program_type
                        )
                    return state
                except Exception:
                    logfire.warning(
                        "repository.state_json_corrupt — starting fresh",
                        session_id=session_id,
                    )

            await db.execute(
                text(
                    "INSERT INTO agent_sessions (session_id, user_id, stage, state_json) "
                    "VALUES (:sid, :uid, 'COLLECTING', :state) "
                    "ON CONFLICT (session_id) DO NOTHING"
                ),
                {
                    "sid": session_id,
                    "uid": user_id,
                    "state": SessionState(session_id=session_id, user_id=user_id).model_dump_json(),
                },
            )
            await db.commit()
    except Exception:
        logfire.exception("repository.get_or_create failed — using in-memory fallback")

    return SessionState(session_id=session_id, user_id=user_id)


async def save(session: SessionState) -> None:
    state_json = session.model_dump_json()
    try:
        async with SessionLocal() as db:
            await db.execute(
                text(
                    "UPDATE agent_sessions "
                    "SET stage = :stage, "
                    "    program_id = :program_id, "
                    "    user_id = :user_id, "
                    "    state_json = :state_json, "
                    "    updated_at = NOW() "
                    "WHERE session_id = :sid"
                ),
                {
                    "sid": session.session_id,
                    "stage": session.stage.value,
                    "program_id": session.program_id,
                    "user_id": session.user_id,
                    "state_json": state_json,
                },
            )
            await db.commit()
    except Exception:
        logfire.exception("repository.save failed", session_id=session.session_id)


async def get_message_history(session_id: str) -> list[Any]:
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                text("SELECT messages FROM agent_message_history WHERE session_id = :sid"),
                {"sid": session_id},
            )
            row = result.fetchone()
            if row:
                return _deserialise_messages(row[0])
    except Exception:
        logfire.exception("repository.get_message_history failed", session_id=session_id)
    return []


async def save_message_history(session_id: str, messages: list[Any]) -> None:
    raw = _serialise_messages(messages)
    try:
        async with SessionLocal() as db:
            await db.execute(
                text(
                    "INSERT INTO agent_message_history (session_id, messages, updated_at) "
                    "VALUES (:sid, :msgs, NOW()) "
                    "ON CONFLICT (session_id) "
                    "DO UPDATE SET messages = :msgs, updated_at = NOW()"
                ),
                {"sid": session_id, "msgs": raw},
            )
            await db.commit()
    except Exception:
        logfire.exception("repository.save_message_history failed", session_id=session_id)


async def get_display_messages(session_id: str) -> list[dict[str, Any]]:
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                text("SELECT display_messages FROM agent_sessions WHERE session_id = :sid"),
                {"sid": session_id},
            )
            row = result.fetchone()
            if row:
                return json.loads(row[0] or "[]")
    except Exception:
        logfire.exception("repository.get_display_messages failed", session_id=session_id)
    return []


async def save_display_messages(session_id: str, messages: list[dict[str, Any]]) -> None:
    raw = json.dumps(messages)
    try:
        async with SessionLocal() as db:
            await db.execute(
                text(
                    "UPDATE agent_sessions "
                    "SET display_messages = :msgs, updated_at = NOW() "
                    "WHERE session_id = :sid"
                ),
                {"sid": session_id, "msgs": raw},
            )
            await db.commit()
    except Exception:
        logfire.exception("repository.save_display_messages failed", session_id=session_id)


async def list_sessions(user_id: str) -> list[dict[str, Any]]:
    """Return the 40 most-recent sessions for a user, newest first."""
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                text(
                    "SELECT session_id, stage, state_json, updated_at "
                    "FROM agent_sessions "
                    "WHERE user_id = :uid "
                    "ORDER BY updated_at DESC "
                    "LIMIT 40"
                ),
                {"uid": user_id},
            )
            rows = result.fetchall()
            sessions = []
            for sid, stage, state_raw, updated_at in rows:
                title = "New chat"
                try:
                    state_data = json.loads(state_raw or "{}")
                    partial = state_data.get("partial_dto") or {}
                    title = partial.get("name") or "New chat"
                except Exception:
                    pass
                sessions.append(
                    {
                        "session_id": sid,
                        "title": title,
                        "stage": stage,
                        "updated_at": (
                            updated_at.isoformat()
                            if hasattr(updated_at, "isoformat")
                            else str(updated_at)
                        ),
                    }
                )
            return sessions
    except Exception:
        logfire.exception("repository.list_sessions failed", user_id=user_id)
    return []


async def delete_session(session_id: str) -> None:
    try:
        async with SessionLocal() as db:
            await db.execute(
                text("DELETE FROM agent_sessions WHERE session_id = :sid"),
                {"sid": session_id},
            )
            await db.commit()
    except Exception:
        logfire.exception("repository.delete_session failed", session_id=session_id)
