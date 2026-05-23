"""DB-backed session and message history store for the program config agent.

Replaces the in-memory session_store.py so that sessions survive restarts and
can be shared across worker processes.

Tables: agent_sessions, agent_message_history (see packages/db/session_tables.sql).
"""

from __future__ import annotations

import json
from typing import Any

import logfire
from pydantic import TypeAdapter
from sqlalchemy import text

from packages.db.database import SessionLocal

from .models import AgentStage, CreateProgramDto, ProgramQuestionDto, SessionState

# ---------------------------------------------------------------------------
# pydantic-ai message serialisation
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
    if not raw or raw == "[]":
        return []
    if not _HAS_TA:
        return []
    try:
        return _messages_ta.validate_json(raw)
    except Exception:
        logfire.warning("message_history.deserialise_failed — returning empty")
        return []


# ---------------------------------------------------------------------------
# Public API — mirrors session_store.py but all functions are async
# ---------------------------------------------------------------------------

async def get_or_create(session_id: str, user_id: str = "") -> SessionState:
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                text(
                    "SELECT user_id, stage, partial_dto, program_id, template_questions "
                    "FROM agent_sessions WHERE session_id = :sid"
                ),
                {"sid": session_id},
            )
            row = result.fetchone()

            if row:
                uid, stage, partial_json, program_id, questions_json = row
                return SessionState(
                    session_id=session_id,
                    user_id=uid or user_id,
                    stage=AgentStage(stage),
                    partial_dto=CreateProgramDto.model_validate_json(partial_json or "{}"),
                    program_id=program_id,
                    template_questions=[
                        ProgramQuestionDto.model_validate(q)
                        for q in json.loads(questions_json or "[]")
                    ],
                )

            # New session — insert row
            await db.execute(
                text(
                    "INSERT INTO agent_sessions "
                    "(session_id, user_id, stage, partial_dto, template_questions) "
                    "VALUES (:sid, :uid, 'COLLECTING', '{}', '[]') "
                    "ON CONFLICT (session_id) DO NOTHING"
                ),
                {"sid": session_id, "uid": user_id},
            )
            await db.commit()
    except Exception:
        logfire.exception("db_session.get_or_create failed — using in-memory fallback")

    return SessionState(session_id=session_id, user_id=user_id)


async def save(session: SessionState) -> None:
    partial_json = session.partial_dto.model_dump_json(exclude_none=True)
    questions_json = json.dumps([q.model_dump() for q in session.template_questions])
    try:
        async with SessionLocal() as db:
            await db.execute(
                text(
                    "UPDATE agent_sessions "
                    "SET stage = :stage, "
                    "    partial_dto = :partial_dto, "
                    "    program_id = :program_id, "
                    "    template_questions = :template_qs, "
                    "    user_id = :user_id, "
                    "    updated_at = NOW() "
                    "WHERE session_id = :sid"
                ),
                {
                    "sid": session.session_id,
                    "stage": session.stage.value,
                    "partial_dto": partial_json,
                    "program_id": session.program_id,
                    "template_qs": questions_json,
                    "user_id": session.user_id,
                },
            )
            await db.commit()
    except Exception:
        logfire.exception("db_session.save failed", session_id=session.session_id)


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
        logfire.exception("db_session.get_message_history failed", session_id=session_id)
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
        logfire.exception("db_session.save_message_history failed", session_id=session_id)


# ---------------------------------------------------------------------------
# Display messages — human-readable chat turns for the history panel
# ---------------------------------------------------------------------------

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
        logfire.exception("db_session.get_display_messages failed", session_id=session_id)
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
        logfire.exception("db_session.save_display_messages failed", session_id=session_id)


async def list_sessions(user_id: str) -> list[dict[str, Any]]:
    """Return the 40 most-recent sessions for a user, newest first."""
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                text(
                    "SELECT session_id, stage, partial_dto, updated_at "
                    "FROM agent_sessions "
                    "WHERE user_id = :uid "
                    "ORDER BY updated_at DESC "
                    "LIMIT 40"
                ),
                {"uid": user_id},
            )
            rows = result.fetchall()
            sessions = []
            for sid, stage, partial_json, updated_at in rows:
                title = "New chat"
                try:
                    partial = json.loads(partial_json or "{}")
                    title = partial.get("name") or "New chat"
                except Exception:
                    pass
                sessions.append({
                    "session_id": sid,
                    "title": title,
                    "stage": stage,
                    "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
                })
            return sessions
    except Exception:
        logfire.exception("db_session.list_sessions failed", user_id=user_id)
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
        logfire.exception("db_session.delete_session failed", session_id=session_id)
