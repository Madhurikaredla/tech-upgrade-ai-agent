"""TEMPLATE_SELECTION stage handler.

Fetches available templates from the backend for the selected program type,
presents them to the admin, and stores the chosen template_id in session
before transitioning to PROGRAM_PREVIEW.
"""

from __future__ import annotations

import logfire

from packages.agents.program_config.api_client import fetch_templates_by_type, friendly_api_error
from packages.agents.program_config.schemas import AgentChatResponse, AgentStage, SessionState


def _format_template_list(templates: list[dict]) -> str:
    lines = ["Please select a registration form template:\n"]
    for i, t in enumerate(templates, 1):
        name = t.get("name") or t.get("title") or f"Template {i}"
        desc = t.get("description") or ""
        desc_part = f" — {desc}" if desc else ""
        lines.append(f"  {i}. {name}{desc_part}")
    lines.append(f"  {len(templates) + 1}. Use default template")
    lines.append("\nType the number to select.")
    return "\n".join(lines)


def _parse_selection(message: str, count: int) -> int | None:
    """Return 0-based index, -1 for default, or None if input is invalid."""
    stripped = message.strip().lower()
    try:
        n = int(stripped)
        if 1 <= n <= count:
            return n - 1
        if n == count + 1:
            return -1
    except ValueError:
        pass
    if stripped in {"default", "skip", "no template", "none", "0"}:
        return -1
    return None


async def handle_template_selection_prompt(session: SessionState) -> AgentChatResponse:
    """Fetch templates for the program type and offer selection to admin.

    If no templates exist, skips directly to PROGRAM_PREVIEW.
    """
    from packages.agents.program_config.db_lookup import get_program_type_config, normalize_admin_type
    from packages.agents.program_config.stages.preview import format_program_preview

    admin_type = normalize_admin_type(session.partial_dto.sub_program_type)
    type_id: int | None = None

    try:
        config = await get_program_type_config(admin_type)
        if config:
            type_id = config.get("id")
    except Exception as exc:
        logfire.warning("template_selection.type_lookup_failed", error=str(exc))

    templates: list[dict] = []
    if type_id:
        try:
            templates = await fetch_templates_by_type(type_id)
        except Exception as exc:
            logfire.warning(
                "template_selection.fetch_failed",
                error=friendly_api_error(exc),
                type_id=type_id,
            )

    if not templates:
        # No templates — go straight to program preview
        logfire.info("template_selection.skipped_no_templates", admin_type=admin_type)
        session.stage = AgentStage.PROGRAM_PREVIEW
        return AgentChatResponse(
            session_id=session.session_id,
            reply=format_program_preview(session.partial_dto),
            stage=session.stage,
            dto_preview=session.partial_dto.model_dump(mode="json", exclude_none=True),
            requires_confirmation=True,
        )

    session.available_templates = templates
    session.stage = AgentStage.TEMPLATE_SELECTION
    logfire.info(
        "template_selection.presented",
        session_id=session.session_id,
        count=len(templates),
        admin_type=admin_type,
    )
    return AgentChatResponse(
        session_id=session.session_id,
        reply=_format_template_list(templates),
        stage=session.stage,
    )


async def handle_template_selection(session: SessionState, message: str) -> AgentChatResponse:
    """Process admin's numeric template choice and move to PROGRAM_PREVIEW."""
    templates = session.available_templates
    idx = _parse_selection(message, len(templates))

    if idx is None:
        return AgentChatResponse(
            session_id=session.session_id,
            reply=(
                f"Please type a number between 1 and {len(templates) + 1}.\n\n"
                + _format_template_list(templates)
            ),
            stage=session.stage,
        )

    if idx == -1:
        session.template_id = None
        session.template_name = None
        logfire.info("template_selection.default_chosen", session_id=session.session_id)
    else:
        t = templates[idx]
        session.template_id = t.get("id")
        session.template_name = t.get("name") or t.get("title") or f"Template {idx + 1}"
        logfire.info(
            "template_selection.chosen",
            session_id=session.session_id,
            template_id=session.template_id,
            template_name=session.template_name,
        )

    session.stage = AgentStage.PROGRAM_PREVIEW
    from packages.agents.program_config.stages.preview import format_preview_with_template
    preview = format_preview_with_template(session.partial_dto, session.template_name)

    return AgentChatResponse(
        session_id=session.session_id,
        reply=preview,
        stage=session.stage,
        dto_preview=session.partial_dto.model_dump(mode="json", exclude_none=True),
        requires_confirmation=True,
    )
