"""PROGRAM_PREVIEW stage handler — confirm or edit before creating program."""

from __future__ import annotations

import re
import logfire

from packages.agents.program_config.api_client import create_program, friendly_api_error
from packages.agents.program_config.schemas import (
    AgentChatResponse,
    AgentStage,
    CreateProgramDto,
    SessionState,
)

_CONFIRM_WORDS = frozenset(
    {"yes", "y", "ok", "okay", "approve", "confirm", "go ahead", "proceed", "sure"}
)
_EDIT_WORDS = frozenset({"edit", "change", "modify", "update", "no", "nope"})


def is_confirm(message: str) -> bool:
    lower = message.lower().strip()
    if lower in _CONFIRM_WORDS:
        return True
    return any(
        (re.search(r'\b' + re.escape(w) + r'\b', lower) is not None) if ' ' not in w
        else (w in lower)
        for w in _CONFIRM_WORDS
    )


def is_edit(message: str) -> bool:
    lower = message.lower().strip()
    return lower in _EDIT_WORDS or any(lower.startswith(w) for w in _EDIT_WORDS)


def _fmt_date(iso: str | None) -> str:
    """Format ISO date or datetime to human-readable, e.g. '10 Jan 2026 09:00'."""
    if not iso:
        return "—"
    try:
        from datetime import datetime
        if "T" in iso:
            return datetime.fromisoformat(iso).strftime("%d %b %Y %H:%M")
        return datetime.fromisoformat(iso).strftime("%d %b %Y")
    except Exception:
        return iso


def _fmt_fee(amount: float | None) -> str:
    if amount is None:
        return "—"
    return f"₹{amount:,.0f}"


def format_program_preview(dto: CreateProgramDto) -> str:
    mode = dto.mode_of_operation.value if dto.mode_of_operation else "—"
    online_type = f" ({dto.online_type.value})" if dto.online_type else ""
    structure = "Single"
    if dto.has_multiple_sessions:
        structure = "Sessions"
    elif dto.is_grouped_program:
        structure = "Grouped Programs"

    prog_type = dto.sub_program_type or (
        "HDB" if (dto.is_grouped_program and dto.is_residence_required) else "CUSTOM"
    )
    is_hdb = prog_type == "HDB"

    lines = [
        "Here's the complete program configuration:\n",
        "┌─────────────────────────────────────────────────┐",
        "│  PROGRAM PREVIEW                                │",
        "├─────────────────────────────────────────────────┤",
        f"│  Name               : {dto.name or '—':<25}│",
        f"│  Type               : {prog_type:<25}│",
        f"│  Mode               : {(mode + online_type):<25}│",
        f"│  Structure          : {structure:<25}│",
        f"│  Starts             : {_fmt_date(dto.starts_at):<25}│",
        f"│  Ends               : {_fmt_date(dto.ends_at):<25}│",
        f"│  Reg. Opens         : {_fmt_date(dto.registration_starts_at):<25}│",
        f"│  Reg. Closes        : {_fmt_date(dto.registration_ends_at):<25}│",
        f"│  Max Seats          : {(str(dto.total_seats) if dto.limited_seats and dto.total_seats else ('Limited (count not set)' if dto.limited_seats else 'Unlimited')):<25}│",
        f"│  Waitlist           : {'Yes' if dto.waitlist_applicable else 'No':<25}│",
        f"│  Requires Approval  : {'Yes' if dto.requires_approval else 'No':<25}│",
    ]

    # Fee — HDB shows two tiers; other paid programs show a single fee
    if is_hdb:
        lines.append(f"│  HDB Fee            : {_fmt_fee(dto.base_price):<25}│")
        lines.append(f"│  MSD Fee            : {_fmt_fee(dto.program_fee):<25}│")
    elif dto.requires_payment and dto.program_fee is not None:
        lines.append(f"│  Fee                : {_fmt_fee(dto.program_fee):<25}│")
    else:
        lines.append(f"│  Fee                : {'Free':<25}│")

    if dto.is_residence_required and dto.total_bed_count:
        lines.append(f"│  Bed Count          : {dto.total_bed_count:<25}│")

    lines += [
        f"│  Email Sender       : {(dto.email_sender_name or '—'):<25}│",
        f"│  Venue              : {(dto.venue or '—'):<25}│",
        f"│  Status             : {'DRAFT':<25}│",
        "└─────────────────────────────────────────────────┘",
    ]

    # Sub-programs block
    if dto.is_grouped_program and dto.grouped_programs:
        lines.append(f"\nSub-programs ({len(dto.grouped_programs)}):")
        for i, g in enumerate(dto.grouped_programs, 1):
            date_range = f"{_fmt_date(g.starts_at)} → {_fmt_date(g.ends_at)}"
            checkin = ""
            if g.checkin_at:
                checkin = f"  Check-in: {_fmt_date(g.checkin_at)}"
                if g.checkout_at:
                    checkin += f" → {_fmt_date(g.checkout_at)}"
            lines.append(f"  {i}. {g.name:<12} {date_range}{checkin}")

    # Sessions block
    elif dto.has_multiple_sessions and dto.program_sessions:
        lines.append(f"\nSessions ({len(dto.program_sessions)}):")
        for i, s in enumerate(dto.program_sessions, 1):
            date_range = f"{_fmt_date(s.starts_at)} → {_fmt_date(s.ends_at)}"
            link = f"  {s.meeting_link}" if s.meeting_link else ""
            lines.append(f"  {i}. {s.name:<14} {date_range}{link}")

    lines.append("\nShall I create this program? (yes / edit)")
    return "\n".join(lines)


def format_preview_with_template(dto: CreateProgramDto, template_name: str | None) -> str:
    """Return the program preview with the selected template name injected."""
    preview = format_program_preview(dto)
    if not template_name:
        return preview
    lines = preview.split("\n")
    insert_at = len(lines) - 1
    while insert_at > 0 and not lines[insert_at].strip():
        insert_at -= 1
    lines.insert(insert_at, f"  Template             : {template_name:<25}")
    return "\n".join(lines)


async def handle_program_preview(session: SessionState, message: str) -> AgentChatResponse:
    from packages.agents.program_config.stages.collecting import run_extraction
    from packages.agents.program_config.stages.form import handle_form_preview_prompt
    from packages.agents.program_config.stages.collecting import model_busy_response

    if is_confirm(message):
        try:
            session.program_id = await create_program(session.partial_dto, session.user_id)
        except Exception as exc:
            logfire.exception("create_program failed")
            return AgentChatResponse(
                session_id=session.session_id,
                reply=f"Program creation failed — {friendly_api_error(exc)} Please try again.",
                stage=session.stage,
                success=False,
            )
        session.stage = AgentStage.PROGRAM_CREATED
        return await handle_form_preview_prompt(session)

    if is_edit(message):
        # Stay in PROGRAM_PREVIEW — next message hits the inline extraction path below,
        # bypassing template selection (template was already chosen).
        return AgentChatResponse(
            session_id=session.session_id,
            reply="Sure, what would you like to change?",
            stage=session.stage,
        )

    # Inline field update — extract and re-show updated preview
    _, error = await run_extraction(session, message)
    if error:
        return model_busy_response(session)

    return AgentChatResponse(
        session_id=session.session_id,
        reply=format_preview_with_template(session.partial_dto, session.template_name),
        stage=session.stage,
        dto_preview=session.partial_dto.model_dump(mode="json", exclude_none=True),
        requires_confirmation=True,
    )
