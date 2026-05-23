"""COLLECTING stage handler — extraction agent interaction."""

from __future__ import annotations

import asyncio
import contextlib
import json

import httpx
import logfire
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior

from packages.agents.program_config import repository
from packages.agents.program_config import rules
from packages.agents.program_config.agent import get_program_config_agent
from packages.agents.program_config.prompts import EXTRACTION_PROMPT
from packages.agents.program_config.schemas import (
    AgentChatResponse,
    AgentStage,
    CreateProgramDto,
    ProgramConfigTurn,
    SessionState,
)

_TRANSIENT_STATUSES = {429, 502, 503, 504}
_MAX_RETRIES = 2


def model_busy_response(session: SessionState) -> AgentChatResponse:
    return AgentChatResponse(
        session_id=session.session_id,
        reply="The AI model is temporarily busy — please send your message again in a moment.",
        stage=session.stage,
        success=False,
    )


async def run_extraction(
    session: SessionState, message: str
) -> tuple[ProgramConfigTurn | None, bool]:
    """Run the extraction agent and merge results into session.partial_dto.

    Returns (turn, had_error). On transient model errors returns (None, True).
    Retries up to _MAX_RETRIES times on transient HTTP errors before giving up.
    """
    agent = get_program_config_agent()
    missing = rules.get_missing_required_fields(session.partial_dto)

    # Build a plain-text conversation transcript from display_messages so the agent
    # has full context without using pydantic_ai message_history.
    #
    # We cannot pass message_history to agent.run() when targeting Gemini: structured
    # output uses tool-calling internally, producing 3 messages per run with no final
    # text response.  Replaying these creates consecutive "user" turns that Gemini
    # rejects with 400 "function response turn comes immediately after function call turn".
    #
    # Embedding the display transcript in the prompt gives equivalent context with zero
    # API format constraints.
    display = await repository.get_display_messages(session.session_id)
    recent = display[-8:] if len(display) > 8 else display  # last 4 exchanges
    if recent:
        lines = []
        for msg in recent:
            role = "Admin" if msg.get("role") == "user" else "Assistant"
            content = (msg.get("content") or "").strip()
            if content:
                lines.append(f"{role}: {content}")
        conversation_history = "\n".join(lines)
    else:
        conversation_history = "No prior conversation."

    prompt = EXTRACTION_PROMPT.format(
        partial_dto_json=session.partial_dto.model_dump_json(indent=2, exclude_none=True),
        missing_fields=", ".join(missing) if missing else "none — all required fields present",
        conversation_history=conversation_history,
        message=message,
    )

    result = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            result = await agent.run(prompt)
            break
        except ModelHTTPError as exc:
            logfire.warning(
                "agent.model_http_error",
                status=exc.status_code,
                model=exc.model_name,
                body=exc.body,
                attempt=attempt,
            )
            if exc.status_code in _TRANSIENT_STATUSES:
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(1.5 ** attempt)  # 1s, 1.5s
                    continue
                return None, True
            body = exc.body or {}
            if exc.status_code == 400 and (
                body.get("code") == "tool_use_failed"
                or "tool_use_failed" in str(body)
                or "function response turn" in str(body)
            ):
                return None, True
            if exc.status_code == 404 and (
                body.get("code") == "model_not_found" or "model_not_found" in str(body)
            ):
                raise RuntimeError(
                    f"Model '{exc.model_name}' not found on this provider. "
                    "Check GROQ_MODEL / DEFAULT_MODEL in your .env file."
                ) from exc
            raise
        except UnexpectedModelBehavior as exc:
            logfire.warning("agent.unexpected_model_behavior", detail=str(exc))
            return None, True
        except httpx.ConnectError as exc:
            if attempt < _MAX_RETRIES:
                logfire.warning("agent.connect_error — retrying", detail=str(exc), attempt=attempt)
                await asyncio.sleep(1.5 ** attempt)
                continue
            logfire.warning("agent.connect_error — giving up", detail=str(exc))
            return None, True

    if result is None:
        return None, True

    turn = result.output
    ef = turn.extracted_fields
    updates = ef.model_dump(exclude_none=True)

    if updates:
        logfire.info(
            "extraction.fields_extracted",
            session_id=session.session_id,
            keys=list(updates.keys()),
            all_required_collected=turn.all_required_collected,
        )
        merged = session.partial_dto.model_dump()

        for k, v in updates.items():
            if k == "sub_program_type" and v:
                from packages.agents.program_config.db_lookup import normalize_admin_type
                v = normalize_admin_type(str(v))
            if k == "meta" and v is not None:
                # v is MetaDto — convert to plain dict for merging
                meta_dict = v.model_dump(exclude_none=True) if hasattr(v, "model_dump") else dict(v)
                existing_meta: dict = {}
                if isinstance(merged.get("meta"), str):
                    with contextlib.suppress(Exception):
                        existing_meta = json.loads(merged["meta"])
                elif isinstance(merged.get("meta"), dict):
                    existing_meta = dict(merged["meta"])
                existing_meta.update(meta_dict)
                # CreateProgramDto.meta is str | None — must store as JSON string
                merged["meta"] = json.dumps(existing_meta)
            elif k == "grouped_programs":
                # ef.grouped_programs is already validated as list[GroupedProgramDto] by pydantic
                merged[k] = [g if isinstance(g, dict) else g.model_dump() for g in (v or [])]
            elif k == "program_sessions":
                merged[k] = [s if isinstance(s, dict) else s.model_dump() for s in (v or [])]
            else:
                merged[k] = v

        try:
            session.partial_dto = rules.apply_rules(CreateProgramDto.model_validate(merged))
        except Exception as merge_exc:
            logfire.warning("field merge failed — keeping previous DTO", error=str(merge_exc))
    else:
        logfire.info(
            "extraction.no_fields_extracted",
            session_id=session.session_id,
            all_required_collected=turn.all_required_collected,
        )

    await repository.save_message_history(session.session_id, result.all_messages())
    return turn, False


async def handle_collecting(session: SessionState, message: str) -> AgentChatResponse:
    from packages.agents.program_config.db_lookup import (
        get_program_type_config,
        normalize_admin_type,
    )
    from packages.agents.program_config.stages.type_announcement import (
        apply_type_config_to_dto,
        build_type_announcement,
    )

    # Defensive: re-apply rules on load to repair stale DB state (e.g. if a prior
    # save failed silently and the session was re-loaded with default values).
    session.partial_dto = rules.apply_rules(session.partial_dto)

    # Capture sub_program_type BEFORE this turn's extraction to detect first-time confirmation
    prev_sub_type = session.partial_dto.sub_program_type

    turn, error = await run_extraction(session, message)
    if error:
        return model_busy_response(session)

    # ── TYPE ANNOUNCEMENT INTERCEPTION ──────────────────────────────────────
    # Fires exactly once per session: when sub_program_type transitions None → value
    # and the session has not yet had an announcement (program_type_key is None).
    current_sub_type = session.partial_dto.sub_program_type
    type_just_confirmed = (
        prev_sub_type is None
        and current_sub_type is not None
        and session.program_type_key is None
    )

    if type_just_confirmed:
        admin_type = normalize_admin_type(current_sub_type)
        session.program_type_key = admin_type  # mark as announced — won't fire again

        with logfire.span(
            "program_config.type_announcement",
            session_id=session.session_id,
            admin_type=admin_type,
        ):
            config = await get_program_type_config(admin_type)

        if config is not None:
            session.partial_dto = apply_type_config_to_dto(session.partial_dto, config)
            session.partial_dto = rules.apply_rules(session.partial_dto)

        announcement = build_type_announcement(admin_type, config, session.partial_dto)
        logfire.info(
            "type_announcement.sent",
            session_id=session.session_id,
            admin_type=admin_type,
            had_db_config=(config is not None),
        )
        return AgentChatResponse(
            session_id=session.session_id,
            reply=announcement,
            stage=session.stage,
        )
    # ────────────────────────────────────────────────────────────────────────

    missing_after = rules.get_missing_required_fields(session.partial_dto)
    if not missing_after:
        from packages.agents.program_config.stages.template import handle_template_selection_prompt
        return await handle_template_selection_prompt(session)

    # Agent said "I have everything" but the DTO still has gaps — surface real missing fields.
    if turn and turn.all_required_collected:
        missing_str = ", ".join(missing_after)
        return AgentChatResponse(
            session_id=session.session_id,
            reply=(
                f"Almost there! I still need the following to complete the setup: "
                f"{missing_str}. Could you provide these?"
            ),
            stage=session.stage,
        )

    reply = turn.reply  # type: ignore[union-attr]

    if missing_after:
        # Always override the question portion with one built from the actual
        # post-extraction missing list.  The LLM's question was generated against
        # the pre-extraction missing_fields and may ask for fields the admin just
        # provided — a direct BR-PC-006 violation.  Keeping the acknowledgment
        # text (before the first "?") and replacing the question is safer.
        if "?" in reply:
            q_pos = reply.rfind("?")
            # Walk back to the nearest paragraph or sentence break before the "?"
            cut = max(reply.rfind("\n\n", 0, q_pos), reply.rfind("\n", 0, q_pos))
            if cut > len(reply) // 4:
                reply = reply[:cut].rstrip()
        next_fields = missing_after[:3]
        fields_str = ", ".join(f"**{f}**" for f in next_fields)
        reply = reply.rstrip() + f"\n\nCould you share: {fields_str}?"

    return AgentChatResponse(
        session_id=session.session_id,
        reply=reply,
        stage=session.stage,
    )
