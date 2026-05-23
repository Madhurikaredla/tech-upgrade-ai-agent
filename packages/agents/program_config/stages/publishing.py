"""READY_TO_PUBLISH / PUBLISHED stage handlers."""

from __future__ import annotations

import logfire

from packages.agents.program_config.api_client import friendly_api_error, publish_program
from packages.agents.program_config.rules import validate_for_publish
from packages.agents.program_config.schemas import (
    AgentChatResponse,
    AgentStage,
    SessionState,
)

_DRAFT_WORDS = frozenset({"keep as draft", "draft", "later", "not now"})


def _contains_publish(message: str) -> bool:
    lower = message.lower().strip()
    publish_words = {"publish", "go live", "release", "launch", "make it live"}
    return lower in publish_words or any(lower.startswith(w) for w in publish_words) or "publish" in lower


def _form_summary(session: SessionState) -> str:
    if session.template_id is not None:
        return f"Template '{session.template_name or session.template_id}' cloned"
    n = len(session.template_questions)
    return f"{n} question{'s' if n != 1 else ''} attached"


def format_publish_ready(session: SessionState) -> str:
    dto = session.partial_dto
    return (
        f"Program is fully configured and ready to publish.\n\n"
        f"  Program ID   : {session.program_id}\n"
        f"  Name         : {dto.name}\n"
        f"  Mode         : {dto.mode_of_operation.value if dto.mode_of_operation else '—'}\n"
        f"  Form         : {_form_summary(session)}\n\n"
        f"Type 'publish' to go live, or 'keep as draft' to save without publishing."
    )


def _fmt_date(iso: str | None) -> str:
    if not iso:
        return "Open"
    try:
        from datetime import datetime
        if "T" in iso:
            return datetime.fromisoformat(iso).strftime("%d %b %Y %H:%M")
        return datetime.fromisoformat(iso).strftime("%d %b %Y")
    except Exception:
        return iso


def format_published(session: SessionState) -> str:
    dto = session.partial_dto
    reg_open = _fmt_date(dto.registration_starts_at)
    reg_close = _fmt_date(dto.registration_ends_at)
    return (
        f"✓ {dto.name} is now PUBLISHED.\n\n"
        f"  Program ID   : {session.program_id}\n"
        f"  Registration : {reg_open} → {reg_close}\n"
        f"  Seats        : {dto.total_seats or 'Unlimited'}\n\n"
        f"Seekers can now find and register for this program."
    )


def handle_publish_prompt(session: SessionState) -> AgentChatResponse:
    session.stage = AgentStage.READY_TO_PUBLISH
    return AgentChatResponse(
        session_id=session.session_id,
        reply=format_publish_ready(session),
        stage=session.stage,
        program_id=session.program_id,
        requires_confirmation=True,
    )


async def _do_publish(session: SessionState, stage: AgentStage) -> AgentChatResponse:
    try:
        await publish_program(
            session.program_id,  # type: ignore[arg-type]
            session.user_id,
            "PUBLIC",
        )
    except Exception as exc:
        logfire.exception("publish_program failed")
        return AgentChatResponse(
            session_id=session.session_id,
            reply=f"Publishing failed — {friendly_api_error(exc)} Please try again.",
            stage=stage,
            success=False,
        )
    session.stage = AgentStage.PUBLISHED
    return AgentChatResponse(
        session_id=session.session_id,
        reply=format_published(session),
        stage=AgentStage.PUBLISHED,
        program_id=session.program_id,
    )


async def handle_publish(session: SessionState, message: str) -> AgentChatResponse:
    lower = message.lower().strip()

    if lower in _DRAFT_WORDS:
        return AgentChatResponse(
            session_id=session.session_id,
            reply=f"Saved as DRAFT (ID: {session.program_id}). Come back anytime to publish.",
            stage=session.stage,
            program_id=session.program_id,
        )

    if not _contains_publish(message):
        return AgentChatResponse(
            session_id=session.session_id,
            reply="Type 'publish' to go live, or 'keep as draft' to save for later.",
            stage=session.stage,
            program_id=session.program_id,
            requires_confirmation=True,
        )

    errors = validate_for_publish(session.partial_dto)
    if errors:
        return AgentChatResponse(
            session_id=session.session_id,
            reply="Cannot publish — please fix these issues first:\n" + "\n".join(f"  • {e}" for e in errors),
            stage=session.stage,
            program_id=session.program_id,
        )

    return await _do_publish(session, session.stage)


async def handle_republish(session: SessionState, message: str) -> AgentChatResponse:
    if not _contains_publish(message):
        return AgentChatResponse(
            session_id=session.session_id,
            reply=(
                f"Program {session.program_id} is already published.\n"
                "To create another program, start a new session."
            ),
            stage=AgentStage.PUBLISHED,
            program_id=session.program_id,
        )

    return await _do_publish(session, AgentStage.PUBLISHED)
