"""Program configuration agent runner.

State machine:
  COLLECTING → PROGRAM_PREVIEW → PROGRAM_CREATED → FORM_PREVIEW
             → FORM_ATTACHED → READY_TO_PUBLISH → PUBLISHED

The runner drives all stage transitions. The AI agent is called only during
COLLECTING to extract fields and formulate clarification questions.
All other stages are deterministic: the runner checks keywords and calls
downstream APIs directly.
"""

from __future__ import annotations

import contextlib
import json
import time as _time
from typing import Any

import httpx
import logfire
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior

from packages.client.nestjs_client import NestJSClient
from packages.logging.context import get_request_id
from packages.logging.decorators import log_agent_run

from . import db_session, templates
from .agent import get_program_config_agent
from .db_lookup import get_type_and_workflow
from .models import (
    AgentChatRequest,
    AgentChatResponse,
    AgentStage,
    CreateProgramDto,
    ProgramConfigTurn,
    ProgramQuestionDto,
    SessionState,
)
from .prompts import EXTRACTION_PROMPT, HELP_MESSAGE
from . import rules


# ---------------------------------------------------------------------------
# Keyword matchers
# ---------------------------------------------------------------------------

_CONFIRM_WORDS = {"yes", "y", "ok", "okay", "approve", "confirm", "go ahead", "proceed", "sure"}
_EDIT_WORDS = {"edit", "change", "modify", "update", "no", "nope"}
_PUBLISH_WORDS = {"publish", "go live", "release", "launch", "make it live"}
_HELP_WORDS = {"help", "?", "/?", "/help", "what can you do", "how does this work", "guide"}


def _is_confirm(message: str) -> bool:
    return message.lower().strip() in _CONFIRM_WORDS


def _is_edit(message: str) -> bool:
    lower = message.lower().strip()
    return lower in _EDIT_WORDS or any(lower.startswith(w) for w in _EDIT_WORDS)


def _is_publish(message: str) -> bool:
    lower = message.lower().strip()
    return lower in _PUBLISH_WORDS or any(lower.startswith(w) for w in _PUBLISH_WORDS)


def _is_help(message: str) -> bool:
    return message.lower().strip() in _HELP_WORDS


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _format_program_preview(dto: CreateProgramDto) -> str:
    mode = dto.mode_of_operation.value if dto.mode_of_operation else "—"
    online_type = f" ({dto.online_type.value})" if dto.online_type else ""
    structure = "Single"
    if dto.has_multiple_sessions:
        structure = "Sessions"
    elif dto.is_grouped_program:
        structure = "Grouped Programs"

    lines = [
        "Here's the complete program configuration:\n",
        "┌─────────────────────────────────────────────────┐",
        "│  PROGRAM PREVIEW                                │",
        "├─────────────────────────────────────────────────┤",
        f"│  Name               : {dto.name or '—':<25}│",
        f"│  Type               : {(dto.sub_program_type or 'CUSTOM'):<25}│",
        f"│  Mode               : {(mode + online_type):<25}│",
        f"│  Structure          : {structure:<25}│",
        f"│  Starts             : {(dto.starts_at or '—'):<25}│",
        f"│  Ends               : {(dto.ends_at or '—'):<25}│",
        f"│  Reg. Opens         : {(dto.registration_starts_at or '—'):<25}│",
        f"│  Reg. Closes        : {(dto.registration_ends_at or '—'):<25}│",
        f"│  Max Seats          : {(str(dto.total_seats) if dto.limited_seats and dto.total_seats else 'Unlimited'):<25}│",
        f"│  Waitlist           : {'Yes' if dto.waitlist_applicable else 'No':<25}│",
        f"│  Requires Approval  : {'Yes' if dto.requires_approval else 'No':<25}│",
        f"│  Fee                : {'₹' + str(dto.program_fee) if dto.requires_payment and dto.program_fee else 'Free':<25}│",
        f"│  Email Sender       : {(dto.email_sender_name or '—'):<25}│",
        f"│  Venue              : {(dto.venue or '—'):<25}│",
        f"│  Status             : {'DRAFT':<25}│",
        "└─────────────────────────────────────────────────┘",
        "\nShall I create this program? (yes / edit)",
    ]
    return "\n".join(lines)


def _format_form_preview(questions: list[ProgramQuestionDto]) -> str:
    sections: dict[str, list[ProgramQuestionDto]] = {}
    for q in questions:
        sections.setdefault(q.form_section, []).append(q)

    lines = ["Here's the registration form I'll attach:\n"]
    for section, qs in sections.items():
        lines.append(f"  {section.upper()}")
        for q in sorted(qs, key=lambda x: x.display_order):
            req = "required" if q.is_required else "optional"
            bind = f" → {q.binding_key}" if q.binding_key else ""
            lines.append(f"    ✓ {q.question_text:<30} ({req}{bind})")
        lines.append("")

    total = len(questions)
    lines.append(f"  Total: {total} question{'s' if total != 1 else ''} across {len(sections)} section{'s' if len(sections) != 1 else ''}")
    lines.append("\nWant to add or remove any questions? (ok / edit)")
    return "\n".join(lines)


def _format_publish_ready(session: SessionState) -> str:
    dto = session.partial_dto
    return (
        f"Program is fully configured and ready to publish.\n\n"
        f"  Program ID   : {session.program_id}\n"
        f"  Name         : {dto.name}\n"
        f"  Mode         : {dto.mode_of_operation.value if dto.mode_of_operation else '—'}\n"
        f"  Form         : {len(session.template_questions)} questions attached\n\n"
        f"Type 'publish' to make this program live for seekers, or 'keep as draft' to save it."
    )


def _format_published(session: SessionState) -> str:
    dto = session.partial_dto
    return (
        f"✓ {dto.name} is now PUBLISHED.\n\n"
        f"  Program ID   : {session.program_id}\n"
        f"  Registration : {dto.registration_starts_at or 'Open'} → {dto.registration_ends_at or 'Open'}\n"
        f"  Seats        : {dto.total_seats or 'Unlimited'}\n\n"
        f"Seekers can now find and register for this program."
    )


# ---------------------------------------------------------------------------
# Downstream API helpers
# ---------------------------------------------------------------------------


def _friendly_api_error(exc: Exception) -> str:
    """Return a user-facing error message that never leaks raw API response bodies."""
    msg = str(exc)
    if "NestJS" in msg or "httpx" in msg or "traceback" in msg.lower() or "{" in msg:
        return "An unexpected error occurred on the server. Please try again or contact support."
    if "typeId" in msg or "workflowId" in msg or "workflow_configuration" in msg:
        return "Program type configuration is missing. Please contact an administrator."
    if len(msg) > 200:
        return "An unexpected error occurred on the server. Please try again or contact support."
    return msg


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


# NestJS uses a different camelCase name for this field than what snake_to_camel produces
_CAMEL_RENAMES: dict[str, str] = {
    "isResidenceRequired": "requiresResidence",
}


def _dto_to_api_payload(dto: CreateProgramDto, user_id: str = "") -> dict[str, Any]:
    """Convert internal DTO (snake_case) to NestJS API payload (camelCase).

    Enum values are serialised as their string value.
    Nested lists (grouped_programs, program_sessions) are recursively converted.
    Required NestJS fields typeId, workflowId, createdBy, updatedBy are injected.
    """
    data = dto.model_dump(exclude_none=True)
    camel: dict[str, Any] = {}

    for key, val in data.items():
        camel_key = _CAMEL_RENAMES.get(_snake_to_camel(key), _snake_to_camel(key))
        # Enum → lowercase string value (NestJS expects online/offline/hybrid/draft/…)
        if key == "meta" and isinstance(val, dict):
            camel[camel_key] = json.dumps(val)
        elif hasattr(val, "value"):
            camel[camel_key] = val.value.lower()
        elif isinstance(val, list):
            camel[camel_key] = [
                {_CAMEL_RENAMES.get(_snake_to_camel(k), _snake_to_camel(k)): (v.value.lower() if hasattr(v, "value") else v) for k, v in item.items()}
                if isinstance(item, dict) else item
                for item in val
            ]
        else:
            camel[camel_key] = val

    # Inject required NestJS FK fields
    uid = int(user_id) if user_id and user_id.isdigit() else 1
    camel.setdefault("createdBy", uid)
    camel.setdefault("updatedBy", uid)
    camel.setdefault("status", "draft")
    camel.setdefault("isActive", True)

    return camel


async def _resolve_workflow(dto: CreateProgramDto) -> None:
    """Resolve typeId and workflowId directly from the DB (no NestJS round-trip).

    Queries workflow_configuration by sub_program_type, caches results in-process.
    Populates dto.type_id and dto.workflow_id in-place if not already set.
    """
    if dto.type_id and dto.workflow_id:
        return  # already resolved

    type_id, workflow_id = await get_type_and_workflow(dto.sub_program_type)
    if type_id and not dto.type_id:
        dto.type_id = type_id
    if workflow_id and not dto.workflow_id:
        dto.workflow_id = workflow_id


async def _create_program(dto: CreateProgramDto, user_id: str = "") -> int:
    """POST /program → returns the new program ID."""
    await _resolve_workflow(dto)
    if not dto.type_id or not dto.workflow_id:
        raise ValueError(
            f"Cannot create program: typeId/workflowId missing for type '{dto.sub_program_type}'. "
            "Check the workflow_configuration table."
        )
    client = await NestJSClient.get_instance()
    payload = _dto_to_api_payload(dto, user_id)
    logfire.info("program_config.create_program.payload", payload=payload)
    with logfire.span("program_config.create_program"):
        result = await client.post("/program", payload)
    logfire.info("program_config.create_program.response", result=result)

    # NestJS may return the ID under different keys / envelope shapes
    if isinstance(result, (int, float)):
        return int(result)
    if isinstance(result, dict):
        # Unwrap {"statusCode": 201, "data": {"id": ...}} envelopes
        candidate = result.get("data") if isinstance(result.get("data"), dict) else result
        pid = candidate.get("id") or candidate.get("programId") or candidate.get("program_id")
        if pid:
            return int(pid)
    raise ValueError(f"Cannot extract program ID from NestJS response: {result!r}")


async def _attach_questions(program_id: int, questions: list[ProgramQuestionDto]) -> None:
    """POST /program-question — adds template questions grouped by form_section."""
    client = await NestJSClient.get_instance()

    # Group questions by form_section to build the sections array
    sections_map: dict[str, list[ProgramQuestionDto]] = {}
    for q in questions:
        sections_map.setdefault(q.form_section, []).append(q)

    sections = []
    for section_order, (section_name, qs) in enumerate(sections_map.items(), start=1):
        custom_questions = []
        for q in sorted(qs, key=lambda x: x.display_order):
            cq: dict[str, Any] = {
                "question": {
                    "label": q.question_text,
                    "type": q.question_type.upper(),
                    **({"bindingKey": q.binding_key} if q.binding_key else {}),
                    "config": {"isRequired": q.is_required},
                },
                "displayOrder": q.display_order,
            }
            if q.options:
                cq["options"] = [{"name": opt, "type": "OPTION"} for opt in q.options]
            custom_questions.append(cq)

        sections.append({
            "sectionName": section_name,
            "sectionDisplayOrder": section_order,
            "questions": [],
            "customQuestions": custom_questions,
        })

    payload: dict[str, Any] = {
        "programId": program_id,
        "registrationLevel": "PROGRAM",
        "sections": sections,
    }
    with logfire.span("program_config.attach_questions", program_id=program_id):
        await client.post("/program-question", payload)


async def _publish_program(program_id: int, user_id: str = "") -> None:
    """PUT /program/{id}/status → publishes the program."""
    client = await NestJSClient.get_instance()
    uid = int(user_id) if user_id and user_id.isdigit() else 1
    payload: dict[str, Any] = {
        "status": "published",
        "updatedBy": uid,
        "accessType": "public",
    }
    with logfire.span("program_config.publish_program", program_id=program_id):
        await client.put(f"/program/{program_id}/status", payload)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

@log_agent_run("program_config")
async def run_chat(request: AgentChatRequest) -> AgentChatResponse:
    session = await db_session.get_or_create(request.session_id, request.user_id)
    message = request.message.strip()

    with logfire.span(
        "program_config.chat",
        session_id=session.session_id,
        stage=session.stage.value,
        request_id=get_request_id(),
    ):
        response = await _dispatch(session, message)

    await db_session.save(session)
    await _append_display_messages(request.session_id, message, response)
    return response


async def _append_display_messages(
    session_id: str, user_msg: str, response: AgentChatResponse
) -> None:
    """Persist the latest user + assistant turn for the UI history panel."""
    now = f"{__import__('datetime').datetime.utcnow().isoformat()}Z"
    t = int(_time.time() * 1000)
    msgs = await db_session.get_display_messages(session_id)
    msgs.append({"id": f"u_{t}", "role": "user", "content": user_msg, "ts": now})
    msgs.append({
        "id": f"a_{t + 1}",
        "role": "assistant",
        "content": response.reply,
        "stage": response.stage.value if hasattr(response.stage, "value") else str(response.stage),
        "ts": now,
    })
    await db_session.save_display_messages(session_id, msgs)


async def _dispatch(session: SessionState, message: str) -> AgentChatResponse:
    if _is_help(message):
        return AgentChatResponse(
            session_id=session.session_id,
            reply=HELP_MESSAGE,
            stage=session.stage,
        )

    stage = session.stage

    if stage == AgentStage.COLLECTING:
        return await _handle_collecting(session, message)

    if stage == AgentStage.PROGRAM_PREVIEW:
        return await _handle_program_preview(session, message)

    if stage == AgentStage.PROGRAM_CREATED:
        return await _handle_form_preview_prompt(session)

    if stage == AgentStage.FORM_PREVIEW:
        return await _handle_form_preview(session, message)

    if stage == AgentStage.FORM_ATTACHED:
        return _handle_publish_prompt(session)

    if stage == AgentStage.READY_TO_PUBLISH:
        return await _handle_publish(session, message)

    # PUBLISHED — terminal state
    return AgentChatResponse(
        session_id=session.session_id,
        reply=(
            f"Program {session.program_id} is already published. "
            "Start a new session to create another program."
        ),
        stage=AgentStage.PUBLISHED,
        program_id=session.program_id,
    )


# ---------------------------------------------------------------------------
# Stage handlers
# ---------------------------------------------------------------------------

async def _run_extraction(
    session: SessionState, message: str
) -> tuple[ProgramConfigTurn | None, bool]:
    """Run the extraction agent, merge results into session.partial_dto.

    Returns (turn, had_error).  On transient model errors returns (None, True)
    so callers can show a retry message without crashing.
    """
    agent = get_program_config_agent()
    history = await db_session.get_message_history(session.session_id)
    missing = rules.get_missing_required_fields(session.partial_dto)

    prompt = EXTRACTION_PROMPT.format(
        partial_dto_json=session.partial_dto.model_dump_json(indent=2, exclude_none=True),
        missing_fields=", ".join(missing) if missing else "none — all required fields present",
        message=message,
    )

    # Keep only the last 6 messages (~3 turns) to stay within free-tier TPM limits.
    # The partial_dto in the prompt already carries all extracted state, so older
    # turns don't improve extraction quality.
    trimmed_history = (history[-6:] if len(history) > 6 else history) or None

    try:
        result = await agent.run(prompt, message_history=trimmed_history)
    except ModelHTTPError as exc:
        logfire.warning("agent.model_http_error", status=exc.status_code, model=exc.model_name, body=exc.body)
        if exc.status_code in {413, 429, 502, 503, 504}:
            return None, True
        # Groq returns 400 tool_use_failed when the model generates a malformed tool call.
        # Treat it as a transient error so the user can retry with the same message.
        body = exc.body or {}
        if exc.status_code == 400 and (body.get("code") == "tool_use_failed" or "tool_use_failed" in str(body)):
            return None, True
        if exc.status_code == 404 and (body.get("code") == "model_not_found" or "model_not_found" in str(body)):
            raise RuntimeError(
                f"Model '{exc.model_name}' not found on this provider. "
                "Check GROQ_MODEL / DEFAULT_MODEL in your .env file."
            ) from exc
        raise
    except UnexpectedModelBehavior as exc:
        logfire.warning("agent.unexpected_model_behavior", detail=str(exc))
        return None, True
    except httpx.ConnectError as exc:
        logfire.warning("agent.connect_error", detail=str(exc))
        return None, True

    turn = result.output
    if turn.extracted_fields:
        merged = session.partial_dto.model_dump()
        for k, v in turn.extracted_fields.items():
            if v is None:
                continue
            # Deep-merge meta dict so new keys don't wipe previously collected ones
            if k == "meta" and isinstance(v, dict):
                existing_meta: dict = {}
                if isinstance(merged.get("meta"), str):
                    with contextlib.suppress(Exception):
                        existing_meta = json.loads(merged["meta"])
                elif isinstance(merged.get("meta"), dict):
                    existing_meta = dict(merged["meta"])
                existing_meta.update(v)
                merged["meta"] = existing_meta
            else:
                merged[k] = v
        try:
            session.partial_dto = rules.apply_rules(CreateProgramDto.model_validate(merged))
        except Exception:
            logfire.warning("field merge failed — keeping previous DTO")

    await db_session.save_message_history(session.session_id, result.all_messages())
    return turn, False


def _model_busy_response(session: SessionState) -> AgentChatResponse:
    return AgentChatResponse(
        session_id=session.session_id,
        reply="The AI model is temporarily busy — please send your message again in a moment.",
        stage=session.stage,
        success=False,
    )


async def _handle_collecting(session: SessionState, message: str) -> AgentChatResponse:
    turn, error = await _run_extraction(session, message)
    if error:
        return _model_busy_response(session)

    missing_after = rules.get_missing_required_fields(session.partial_dto)
    if not missing_after:
        session.stage = AgentStage.PROGRAM_PREVIEW
        return AgentChatResponse(
            session_id=session.session_id,
            reply=_format_program_preview(session.partial_dto),
            stage=session.stage,
            dto_preview=session.partial_dto.model_dump(exclude_none=True),
            requires_confirmation=True,
        )

    return AgentChatResponse(
        session_id=session.session_id,
        reply=turn.reply,  # type: ignore[union-attr]
        stage=session.stage,
    )


async def _handle_program_preview(session: SessionState, message: str) -> AgentChatResponse:
    if _is_confirm(message):
        try:
            session.program_id = await _create_program(session.partial_dto, session.user_id)
        except Exception as exc:
            logfire.exception("create_program failed")
            return AgentChatResponse(
                session_id=session.session_id,
                reply=f"Program creation failed — {_friendly_api_error(exc)} Please try again.",
                stage=session.stage,
                success=False,
            )
        session.stage = AgentStage.PROGRAM_CREATED
        return await _handle_form_preview_prompt(session)

    if _is_edit(message):
        session.stage = AgentStage.COLLECTING
        return AgentChatResponse(
            session_id=session.session_id,
            reply="Sure, what would you like to change?",
            stage=session.stage,
        )

    # Inline field update (e.g. "reg opens today", "change venue to Chennai")
    # Extract the new value and re-show the updated preview without leaving this stage.
    _, error = await _run_extraction(session, message)
    if error:
        return _model_busy_response(session)

    return AgentChatResponse(
        session_id=session.session_id,
        reply=_format_program_preview(session.partial_dto),
        stage=session.stage,
        dto_preview=session.partial_dto.model_dump(exclude_none=True),
        requires_confirmation=True,
    )


async def _handle_form_preview_prompt(session: SessionState) -> AgentChatResponse:
    """Called immediately after program is created — load template and show form."""
    if session.program_id is None:
        # Recovery: PROGRAM_CREATED stage but NestJS call was never completed
        try:
            session.program_id = await _create_program(session.partial_dto, session.user_id)
        except Exception as exc:
            logfire.exception("create_program (recovery) failed")
            session.stage = AgentStage.PROGRAM_PREVIEW
            return AgentChatResponse(
                session_id=session.session_id,
                reply=f"Program creation failed — {_friendly_api_error(exc)} Please try again.",
                stage=session.stage,
                success=False,
            )

    questions = templates.get_template_questions(session.partial_dto.sub_program_type)
    session.template_questions = questions
    session.stage = AgentStage.FORM_PREVIEW
    reply = (
        f"Program created (ID: {session.program_id}).\n\n"
        + _format_form_preview(questions)
    )
    return AgentChatResponse(
        session_id=session.session_id,
        reply=reply,
        stage=session.stage,
        program_id=session.program_id,
        form_preview=questions,
        requires_confirmation=True,
    )


async def _handle_form_preview(session: SessionState, message: str) -> AgentChatResponse:
    if _is_confirm(message):
        try:
            await _attach_questions(session.program_id, session.template_questions)  # type: ignore[arg-type]
        except Exception as exc:
            logfire.exception("attach_questions failed")
            return AgentChatResponse(
                session_id=session.session_id,
                reply=f"Could not attach the registration form — {_friendly_api_error(exc)} Please try again.",
                stage=session.stage,
                success=False,
            )

        session.stage = AgentStage.FORM_ATTACHED
        return _handle_publish_prompt(session)

    if _is_edit(message):
        return AgentChatResponse(
            session_id=session.session_id,
            reply=(
                "Tell me what you'd like to change. For example:\n"
                "  • 'Add a question: preferred roommate (text, optional)'\n"
                "  • 'Remove the Date of Birth question'\n"
                "  • 'Make Mobile Number optional'\n"
            ),
            stage=session.stage,
            form_preview=session.template_questions,
        )

    # Treat any other message as a form edit instruction — apply simple changes
    updated = _apply_form_edit(session.template_questions, message)
    session.template_questions = updated
    return AgentChatResponse(
        session_id=session.session_id,
        reply="Updated. Here's the revised form:\n\n" + _format_form_preview(updated),
        stage=session.stage,
        form_preview=updated,
        requires_confirmation=True,
    )


def _apply_form_edit(
    questions: list[ProgramQuestionDto], instruction: str
) -> list[ProgramQuestionDto]:
    """Apply simple add/remove/update instructions to the question list."""
    lower = instruction.lower()
    updated = list(questions)

    if lower.startswith("remove") or lower.startswith("delete"):
        # Extract the question text after 'remove' / 'delete'
        target = instruction.split(" ", 1)[1].strip().lower() if " " in instruction else ""
        updated = [q for q in updated if target not in q.question_text.lower()]

    elif lower.startswith("add"):
        # Minimal add: parse 'Add a question: <text> (<type>, <required|optional>)'
        try:
            rest = instruction.split(":", 1)[1].strip() if ":" in instruction else instruction
            parts = rest.split("(")
            text = parts[0].strip()
            meta = parts[1].rstrip(")").split(",") if len(parts) > 1 else []
            q_type = meta[0].strip() if meta else "text"
            is_req = len(meta) > 1 and "required" in meta[1].lower()
            next_order = max((q.display_order for q in updated), default=0) + 1
            updated.append(
                ProgramQuestionDto(
                    question_text=text,
                    question_type=q_type,
                    is_required=is_req,
                    form_section="General",
                    display_order=next_order,
                )
            )
        except Exception:
            pass  # If parsing fails, return unchanged

    elif "required" in lower or "optional" in lower:
        # Make a question required/optional: 'Make <name> required/optional'
        make_required = "required" in lower
        words = lower.split()
        for q in updated:
            if any(w in q.question_text.lower() for w in words if len(w) > 3):
                q.is_required = make_required

    return updated


def _handle_publish_prompt(session: SessionState) -> AgentChatResponse:
    session.stage = AgentStage.READY_TO_PUBLISH
    return AgentChatResponse(
        session_id=session.session_id,
        reply=_format_publish_ready(session),
        stage=session.stage,
        program_id=session.program_id,
        requires_confirmation=True,
    )


async def _handle_publish(session: SessionState, message: str) -> AgentChatResponse:
    if message.lower().strip() in {"keep as draft", "draft", "later", "not now"}:
        return AgentChatResponse(
            session_id=session.session_id,
            reply=f"Saved as DRAFT (ID: {session.program_id}). Come back anytime to publish.",
            stage=session.stage,
            program_id=session.program_id,
        )

    if not _is_publish(message):
        return AgentChatResponse(
            session_id=session.session_id,
            reply='Type "publish" to go live or "keep as draft" to save for later.',
            stage=session.stage,
            program_id=session.program_id,
            requires_confirmation=True,
        )

    # Pre-publish validation
    errors = rules.validate_for_publish(session.partial_dto)
    if errors:
        bullet_list = "\n".join(f"  • {e}" for e in errors)
        return AgentChatResponse(
            session_id=session.session_id,
            reply=f"Cannot publish — please fix these issues first:\n{bullet_list}",
            stage=session.stage,
            program_id=session.program_id,
        )

    try:
        await _publish_program(session.program_id, session.user_id)  # type: ignore[arg-type]
    except Exception as exc:
        logfire.exception("publish_program failed")
        return AgentChatResponse(
            session_id=session.session_id,
            reply=f"Publishing failed — {_friendly_api_error(exc)} Please try again.",
            stage=session.stage,
            success=False,
        )

    session.stage = AgentStage.PUBLISHED
    return AgentChatResponse(
        session_id=session.session_id,
        reply=_format_published(session),
        stage=AgentStage.PUBLISHED,
        program_id=session.program_id,
    )
