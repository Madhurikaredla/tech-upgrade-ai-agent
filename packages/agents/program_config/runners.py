"""Program configuration agent runner — thin orchestrator.

State machine:
  COLLECTING → PROGRAM_PREVIEW → PROGRAM_CREATED → FORM_PREVIEW
             → FORM_ATTACHED → READY_TO_PUBLISH → PUBLISHED

The AI agent is invoked only during COLLECTING.
All other stages are deterministic keyword + API calls via stage handlers.
"""

from __future__ import annotations

import time as _time

import logfire

from packages.logging.context import get_request_id
from packages.logging.decorators import log_agent_run

from . import repository
from .prompts import HELP_MESSAGE
from .schemas import AgentChatRequest, AgentChatResponse, AgentStage, SessionState
from .stages.collecting import handle_collecting
from .stages.form import handle_form_preview, handle_form_preview_prompt
from .stages.preview import handle_program_preview
from .stages.publishing import handle_publish, handle_publish_prompt, handle_republish
from .stages.template import handle_template_selection

_HELP_WORDS = frozenset(
    {"help", "?", "/?", "/help", "what can you do", "how does this work", "guide"}
)


def _is_help(message: str) -> bool:
    return message.lower().strip() in _HELP_WORDS


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


@log_agent_run("program_config")
async def run_chat(request: AgentChatRequest) -> AgentChatResponse:
    session = await repository.get_or_create(request.session_id, request.user_id)
    message = request.message.strip()

    with logfire.span(
        "program_config.chat",
        session_id=session.session_id,
        stage=session.stage.value,
        request_id=get_request_id(),
    ):
        response = await _dispatch(session, message)

    await repository.save(session)
    await _append_display_messages(request.session_id, message, response)
    return response


async def _append_display_messages(
    session_id: str, user_msg: str, response: AgentChatResponse
) -> None:
    now = f"{__import__('datetime').datetime.utcnow().isoformat()}Z"
    t = int(_time.time() * 1000)
    msgs = await repository.get_display_messages(session_id)
    msgs.append({"id": f"u_{t}", "role": "user", "content": user_msg, "ts": now})
    assistant_msg: dict = {
        "id": f"a_{t + 1}",
        "role": "assistant",
        "content": response.reply,
        "stage": response.stage.value if hasattr(response.stage, "value") else str(response.stage),
        "ts": now,
    }
    if response.dto_preview is not None:
        assistant_msg["dto_preview"] = response.dto_preview
    msgs.append(assistant_msg)
    await repository.save_display_messages(session_id, msgs)


async def _dispatch(session: SessionState, message: str) -> AgentChatResponse:
    if _is_help(message):
        return AgentChatResponse(
            session_id=session.session_id,
            reply=HELP_MESSAGE,
            stage=session.stage,
        )

    stage = session.stage

    if stage == AgentStage.COLLECTING:
        return await handle_collecting(session, message)

    if stage == AgentStage.TEMPLATE_SELECTION:
        return await handle_template_selection(session, message)

    if stage == AgentStage.PROGRAM_PREVIEW:
        return await handle_program_preview(session, message)

    if stage == AgentStage.PROGRAM_CREATED:
        return await handle_form_preview_prompt(session)

    if stage == AgentStage.FORM_PREVIEW:
        return await handle_form_preview(session, message)

    if stage == AgentStage.FORM_ATTACHED:
        return handle_publish_prompt(session)

    if stage == AgentStage.READY_TO_PUBLISH:
        return await handle_publish(session, message)

    # PUBLISHED stage — allow visibility changes; anything else shows status
    return await handle_republish(session, message)
