"""FORM_PREVIEW / FORM_ATTACHED stage handlers — form question review and attachment."""

from __future__ import annotations

import re
import logfire

from packages.agents.program_config.api_client import (
    attach_questions,
    clone_template_to_program,
    create_program,
    fetch_template_questions,
    friendly_api_error,
)
from packages.agents.program_config.schemas import (
    AgentChatResponse,
    AgentStage,
    ProgramQuestionDto,
    SessionState,
)
from packages.agents.program_config.templates import get_template_questions

_CONFIRM_WORDS = frozenset(
    {
        "yes", "y", "ok", "okay", "approve", "confirm", "go ahead", "proceed", "sure",
        "continue", "looks good", "good", "done", "attach", "submit", "go",
    }
)
_EDIT_WORDS = frozenset({"edit", "change", "modify", "update", "no", "nope"})


def _is_confirm(message: str) -> bool:
    return message.lower().strip() in _CONFIRM_WORDS


def _is_edit(message: str) -> bool:
    lower = message.lower().strip()
    return lower in _EDIT_WORDS or any(lower.startswith(w) for w in _EDIT_WORDS)


def format_form_preview(questions: list[ProgramQuestionDto]) -> str:
    sections: dict[str, list[ProgramQuestionDto]] = {}
    for q in questions:
        sections.setdefault(q.form_section, []).append(q)

    lines = ["Here's the registration form I'll attach:\n"]
    counter = 1
    for section, qs in sections.items():
        lines.append(f"{section}")
        for q in sorted(qs, key=lambda x: x.display_order):
            req = "*" if q.is_required else ""
            opts = f"  [{', '.join(q.options)}]" if q.options else ""
            lines.append(f"  {counter}. {q.question_text}{req}{opts}")
            counter += 1
        lines.append("")

    total = len(questions)
    lines.append(
        f"Total: {total} question{'s' if total != 1 else ''} "
        f"across {len(sections)} section{'s' if len(sections) != 1 else ''}  (* = required)"
    )
    lines.append("\nType 'ok' to confirm or 'edit' to make changes.")
    return "\n".join(lines)


def _numbered_questions(questions: list[ProgramQuestionDto]) -> list[tuple[int, ProgramQuestionDto]]:
    """Return (1-based display number, question) pairs in the same order as format_form_preview."""
    sections: dict[str, list[ProgramQuestionDto]] = {}
    for q in questions:
        sections.setdefault(q.form_section, []).append(q)
    pairs: list[tuple[int, ProgramQuestionDto]] = []
    counter = 1
    for qs in sections.values():
        for q in sorted(qs, key=lambda x: x.display_order):
            pairs.append((counter, q))
            counter += 1
    return pairs


def apply_form_edit(
    questions: list[ProgramQuestionDto], instruction: str
) -> list[ProgramQuestionDto]:
    """Apply add/remove/update instructions to the question list.

    Handles three remove patterns:
    1. Pasted question text + "remove these" / "delete these" on the last line
    2. "remove questions 4, 5, 6" — remove by displayed number
    3. "remove <keyword>" — remove by text match
    """
    lower = instruction.lower().strip()
    updated = list(questions)

    # ── Pattern 1: body of question text + "remove these" on the last line ──────
    stripped_lines = [ln.strip() for ln in instruction.strip().splitlines() if ln.strip()]
    last_line = stripped_lines[-1].lower() if stripped_lines else ""
    if last_line in {"remove these", "delete these", "remove", "delete"} and len(stripped_lines) > 1:
        targets: list[str] = []
        for line in stripped_lines[:-1]:
            # Strip leading number+dot:  "5. Question text* [opts]" → "Question text"
            clean = re.sub(r"^\d+\.\s*", "", line)
            clean = re.sub(r"\*?\s*\[.*?\].*$", "", clean).strip()
            if clean:
                targets.append(clean.lower())
        if targets:
            return [
                q for q in updated
                if not any(t in q.question_text.lower() or q.question_text.lower() == t for t in targets)
            ]

    # ── Pattern 2: "remove questions 4, 5, 6" or "remove 4 5 6" ────────────────
    num_match = re.match(
        r"^(?:remove|delete)\s+(?:questions?\s+)?([\d\s,]+)$", lower
    )
    if num_match:
        nums = {int(n) for n in re.findall(r"\d+", num_match.group(1))}
        keep = {q for n, q in _numbered_questions(updated) if n not in nums}
        return [q for q in updated if q in keep]

    # ── Pattern 3: "remove <keyword text>" ─────────────────────────────────────
    if lower.startswith("remove") or lower.startswith("delete"):
        target = instruction.split(" ", 1)[1].strip().lower() if " " in instruction else ""
        if target:
            return [q for q in updated if target not in q.question_text.lower()]

    # ── Add ─────────────────────────────────────────────────────────────────────
    if lower.startswith("add"):
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
            pass
        return updated

    # ── Make required / optional ─────────────────────────────────────────────────
    if "required" in lower or "optional" in lower:
        make_required = "required" in lower
        words = lower.split()
        for q in updated:
            if any(w in q.question_text.lower() for w in words if len(w) > 3):
                q.is_required = make_required

    return updated


async def handle_form_preview_prompt(session: SessionState) -> AgentChatResponse:
    """Called immediately after program is created — load template and show form."""
    if session.program_id is None:
        try:
            session.program_id = await create_program(session.partial_dto, session.user_id)
        except Exception as exc:
            logfire.exception("create_program (recovery) failed")
            session.stage = AgentStage.PROGRAM_PREVIEW
            return AgentChatResponse(
                session_id=session.session_id,
                reply=f"Program creation failed — {friendly_api_error(exc)} Please try again.",
                stage=session.stage,
                success=False,
            )

    session.stage = AgentStage.FORM_PREVIEW

    if session.template_id is not None:
        # Fetch real questions from the selected backend template so the admin can
        # review (and optionally edit) before confirming.
        template_name = session.template_name or f"Template #{session.template_id}"
        try:
            questions = await fetch_template_questions(session.template_id)
        except Exception:
            logfire.warning(
                "fetch_template_questions failed — falling back to brief confirm",
                template_id=session.template_id,
            )
            questions = []

        if questions:
            session.template_questions = questions
            reply = (
                f"Program created (ID: {session.program_id}).\n\n"
                f"Template: **{template_name}**\n\n"
                + format_form_preview(questions)
            )
            return AgentChatResponse(
                session_id=session.session_id,
                reply=reply,
                stage=session.stage,
                program_id=session.program_id,
                form_preview=questions,
                requires_confirmation=True,
            )

        # Fetch failed — fall back to brief message; clone will still run on confirm
        reply = (
            f"Program created (ID: {session.program_id}).\n\n"
            f"Registration form template: **{template_name}**\n"
            f"All questions from this template will be attached automatically.\n\n"
            f"Type 'ok' to confirm, or 'use default' to switch to the built-in question set instead."
        )
        return AgentChatResponse(
            session_id=session.session_id,
            reply=reply,
            stage=session.stage,
            program_id=session.program_id,
            requires_confirmation=True,
        )

    # No backend template — use hardcoded question set
    questions = get_template_questions(session.partial_dto.sub_program_type)
    session.template_questions = questions
    reply = f"Program created (ID: {session.program_id}).\n\n" + format_form_preview(questions)
    return AgentChatResponse(
        session_id=session.session_id,
        reply=reply,
        stage=session.stage,
        program_id=session.program_id,
        form_preview=questions,
        requires_confirmation=True,
    )


async def handle_form_preview(session: SessionState, message: str) -> AgentChatResponse:
    from packages.agents.program_config.stages.publishing import handle_publish_prompt

    lower = message.lower().strip()

    # "use default" — discard template, switch to built-in hardcoded question set
    if lower in {"use default", "default", "skip template"}:
        session.template_id = None
        session.template_name = None
        questions = get_template_questions(session.partial_dto.sub_program_type)
        session.template_questions = questions
        return AgentChatResponse(
            session_id=session.session_id,
            reply="Switched to built-in questions.\n\n" + format_form_preview(questions),
            stage=session.stage,
            form_preview=questions,
            requires_confirmation=True,
        )

    if _is_confirm(message):
        if session.template_id is not None:
            # Admin confirmed without edits — fast server-side clone, no question upload needed
            try:
                await clone_template_to_program(session.program_id, session.template_id)  # type: ignore[arg-type]
            except Exception as exc:
                logfire.exception("clone_template_to_program failed")
                return AgentChatResponse(
                    session_id=session.session_id,
                    reply=f"Could not attach the registration form — {friendly_api_error(exc)} Please try again.",
                    stage=session.stage,
                    success=False,
                )
        else:
            # Admin edited questions (template_id cleared on first edit) — upload modified set
            try:
                await attach_questions(session.program_id, session.template_questions, session.user_id)  # type: ignore[arg-type]
            except Exception as exc:
                logfire.exception("attach_questions failed")
                return AgentChatResponse(
                    session_id=session.session_id,
                    reply=f"Could not attach the registration form — {friendly_api_error(exc)} Please try again.",
                    stage=session.stage,
                    success=False,
                )
        session.stage = AgentStage.FORM_ATTACHED
        return handle_publish_prompt(session)

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
            form_preview=session.template_questions or None,
        )

    # Inline edit — works on both real template questions and built-in questions.
    # On the first edit of a template, clear template_id so confirm uses attach_questions
    # (server-side clone can't apply partial edits).
    lower_stripped = lower.strip()
    _looks_like_edit = (
        lower_stripped.startswith(("remove", "delete", "add", "make", "change"))
        or "remove these" in lower_stripped
        or "delete these" in lower_stripped
    )
    if session.template_questions and _looks_like_edit:
        updated = apply_form_edit(session.template_questions, message)
        if updated == session.template_questions:
            return AgentChatResponse(
                session_id=session.session_id,
                reply=(
                    "I couldn't apply that edit. Try:\n"
                    "  • Paste the question text and end with 'remove these'\n"
                    "  • 'Remove questions 4, 5, 6'\n"
                    "  • 'Remove <keyword>'\n"
                    "  • 'Add a question: <text> (text, required)'\n"
                    "  • 'Make <question keyword> optional'"
                ),
                stage=session.stage,
                form_preview=session.template_questions,
            )
        if session.template_id is not None:
            session.template_id = None
            session.template_name = None
        session.template_questions = updated
        return AgentChatResponse(
            session_id=session.session_id,
            reply="Updated. Here's the revised form:\n\n" + format_form_preview(updated),
            stage=session.stage,
            form_preview=updated,
            requires_confirmation=True,
        )

    preview_reply = (
        "Here's the current form. Type **ok** to confirm, describe a change to edit, "
        "or **use default** to switch to the built-in question set.\n\n"
        + format_form_preview(session.template_questions)
        if session.template_questions
        else 'Type "ok" to confirm, "edit" to make changes, or "use default" to switch to built-in questions.'
    )
    return AgentChatResponse(
        session_id=session.session_id,
        reply=preview_reply,
        stage=session.stage,
        form_preview=session.template_questions or None,
        requires_confirmation=True,
    )
