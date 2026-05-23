"""NestJS API calls for the program config agent.

Handles: program creation, form question attachment, program publishing.
All functions are async and raise on failure — callers translate to user messages.
"""

from __future__ import annotations

import json
from typing import Any

import logfire

from packages.client.nestjs_client import NestJSClient

from .db_lookup import get_type_and_workflow
from .schemas import CreateProgramDto, ProgramQuestionDto

# ---------------------------------------------------------------------------
# camelCase conversion
# ---------------------------------------------------------------------------

_CAMEL_RENAMES: dict[str, str] = {
    "isResidenceRequired": "requiresResidence",
}


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _venue_address_obj(raw: str) -> dict[str, str]:
    """Wrap a plain address string into the NestJS venueAddress object shape."""
    return {"type": "billing_address", "addressLine1": raw}


def _convert_nested_item(item: dict) -> dict:
    """Convert a single grouped_programs / program_sessions dict to camelCase.

    venue_address → emits both venue (string) and venueAddress (object).
    """
    out: dict[str, Any] = {}
    for k, v in item.items():
        camel_key = _CAMEL_RENAMES.get(_snake_to_camel(k), _snake_to_camel(k))
        if k == "venue_address" and isinstance(v, str):
            out["venue"] = v
            out["venueAddress"] = _venue_address_obj(v)
        elif hasattr(v, "value"):
            out[camel_key] = v.value.lower()
        else:
            out[camel_key] = v
    return out


def dto_to_api_payload(dto: CreateProgramDto, user_id: str = "") -> dict[str, Any]:
    """Convert internal DTO (snake_case) to NestJS API payload (camelCase).

    Enum values are serialised as lowercase strings.
    Nested lists (grouped_programs, program_sessions) are recursively converted.
    """
    data = dto.model_dump(exclude_none=True)
    camel: dict[str, Any] = {}

    for key, val in data.items():
        camel_key = _CAMEL_RENAMES.get(_snake_to_camel(key), _snake_to_camel(key))
        if key == "meta" and isinstance(val, dict):
            camel[camel_key] = json.dumps(val)
        elif key == "venue_address" and isinstance(val, str):
            camel[camel_key] = _venue_address_obj(val)
        elif hasattr(val, "value"):
            camel[camel_key] = val.value.lower()
        elif isinstance(val, list):
            camel[camel_key] = [
                _convert_nested_item(item) if isinstance(item, dict) else item
                for item in val
            ]
        else:
            camel[camel_key] = val

    uid = int(user_id) if user_id and user_id.isdigit() else 1
    camel.setdefault("createdBy", uid)
    camel.setdefault("updatedBy", uid)
    camel.setdefault("status", "draft")
    camel.setdefault("isActive", True)

    return camel


# ---------------------------------------------------------------------------
# Public API helpers
# ---------------------------------------------------------------------------


async def resolve_workflow(dto: CreateProgramDto) -> None:
    """Resolve typeId and workflowId from DB. Populates dto in-place."""
    if dto.type_id and dto.workflow_id:
        return
    type_id, workflow_id = await get_type_and_workflow(dto.sub_program_type)
    if type_id and not dto.type_id:
        dto.type_id = type_id
    if workflow_id and not dto.workflow_id:
        dto.workflow_id = workflow_id


async def create_program(dto: CreateProgramDto, user_id: str = "") -> int:
    """POST /program — returns the new program ID."""
    await resolve_workflow(dto)
    if not dto.type_id or not dto.workflow_id:
        raise ValueError(
            f"Cannot create program: typeId/workflowId missing for type '{dto.sub_program_type}'. "
            "Check the workflow_configuration table."
        )
    client = await NestJSClient.get_instance()
    payload = dto_to_api_payload(dto, user_id)
    logfire.info("program_config.create_program.payload", payload=payload)
    with logfire.span("program_config.create_program"):
        result = await client.post("/program", payload)
    logfire.info("program_config.create_program.response", result=result)

    if isinstance(result, (int, float)):
        return int(result)
    if isinstance(result, dict):
        data = result.get("data") if isinstance(result.get("data"), dict) else result
        # Grouped-program response: data.primaryProgram.id
        primary = data.get("primaryProgram")
        if isinstance(primary, dict) and primary.get("id"):
            return int(primary["id"])
        # Flat response: data.id / data.programId
        pid = data.get("id") or data.get("programId") or data.get("program_id")
        if pid:
            return int(pid)
    raise ValueError(f"Cannot extract program ID from NestJS response: {result!r}")


async def fetch_existing_section_ids(program_id: int) -> dict[str, int]:
    """GET /program/{programId} → map of sectionKey → sectionId for already-attached sections."""
    client = await NestJSClient.get_instance()
    with logfire.span("program_config.fetch_existing_sections", program_id=program_id):
        result = await client.get(f"/program/{program_id}")

    if not isinstance(result, dict):
        return {}
    data = result.get("data") if isinstance(result.get("data"), dict) else result
    section_map: dict[str, int] = {}
    for q_map in (data.get("programQuestionMaps") or []):
        if not isinstance(q_map, dict):
            continue
        section = q_map.get("programQuestionFormSection")
        if isinstance(section, dict):
            key = section.get("key")
            sid = section.get("id")
            if key and sid:
                section_map[str(key)] = int(sid)
    return section_map


async def attach_questions(
    program_id: int, questions: list[ProgramQuestionDto], user_id: str = ""
) -> None:
    """POST /program/form — attaches custom questions to a program form.

    Uses the same endpoint as the infinipath-web FormBuilderEdit:
      endPoints.saveProgramForm = "program/form"
    with a full sections payload (no cloneFromTemplate flag).

    When a section key already exists on the program (e.g. from a prior clone),
    passes formSectionId so NestJS updates rather than trying to create a duplicate.
    """
    client = await NestJSClient.get_instance()
    uid = int(user_id) if user_id and user_id.isdigit() else 1

    try:
        existing_ids = await fetch_existing_section_ids(program_id)
    except Exception:
        logfire.warning(
            "program_config.fetch_existing_sections failed — proceeding without IDs",
            program_id=program_id,
        )
        existing_ids = {}

    sections_map: dict[str, list[ProgramQuestionDto]] = {}
    for q in questions:
        sections_map.setdefault(q.form_section, []).append(q)

    sections = []
    for section_order, (section_name, qs) in enumerate(sections_map.items(), start=1):
        flat_questions = []
        for q in sorted(qs, key=lambda x: x.display_order):
            fq: dict[str, Any] = {
                "label": q.question_text,
                "type": q.question_type.lower(),
                "config": {"isRequired": q.is_required},
                "displayOrder": q.display_order,
                "answerType": "string",
            }
            if q.binding_key:
                fq["bindingKey"] = q.binding_key
            if q.options:
                fq["optionConfig"] = [
                    {"value": opt, "name": opt, "type": "string", "order": idx}
                    for idx, opt in enumerate(q.options)
                ]
            flat_questions.append(fq)

        section_key = "FS_" + section_name.upper().replace(" ", "_").replace("-", "_")
        section_payload: dict[str, Any] = {
            "displayOrder": section_order,
            "questions": flat_questions,
            "subSections": [],
        }
        existing_id = existing_ids.get(section_key)
        if existing_id:
            section_payload["formSectionId"] = existing_id
        else:
            section_payload["sectionName"] = section_name
            section_payload["sectionKey"] = section_key
        sections.append(section_payload)

    payload: dict[str, Any] = {
        "programId": program_id,
        "sections": sections,
        "createdBy": uid,
    }
    with logfire.span("program_config.attach_questions", program_id=program_id):
        await client.post("/program/form", payload)


async def fetch_templates_by_type(type_id: int) -> list[dict[str, Any]]:
    """GET /v1/program-templates/program-type/:typeId — returns published templates."""
    client = await NestJSClient.get_instance()
    with logfire.span("program_config.fetch_templates", type_id=type_id):
        result = await client.get(f"/v1/program-templates/program-type/{type_id}")
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        data = result.get("data") or result.get("templates") or result.get("rows") or []
        return data if isinstance(data, list) else []
    return []


async def fetch_template_questions(template_id: int) -> list[ProgramQuestionDto]:
    """GET /v1/program-templates/:templateId — returns sections and questions for a template.

    Converts the NestJS section/question structure back to ProgramQuestionDto so the
    admin can see and edit the real template questions before confirming.
    """
    client = await NestJSClient.get_instance()
    with logfire.span("program_config.fetch_template_questions", template_id=template_id):
        result = await client.get(f"/v1/program-templates/{template_id}")

    if isinstance(result, dict):
        data = result.get("data") or result
    else:
        data = {}

    sections: list[Any] = (
        data.get("sections")
        or data.get("formSections")
        or data.get("templateSections")
        or []
    )

    questions: list[ProgramQuestionDto] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_name = (
            section.get("sectionName")
            or section.get("name")
            or "General"
        )
        for q in section.get("questions") or []:
            if not isinstance(q, dict):
                continue
            config = q.get("config") or {}
            option_config = q.get("optionConfig") or []
            options = [
                str(opt.get("value") or opt.get("name") or "")
                for opt in option_config
                if isinstance(opt, dict)
            ]
            questions.append(
                ProgramQuestionDto(
                    question_text=q.get("label") or q.get("questionText") or "",
                    question_type=q.get("type") or "text",
                    is_required=bool(config.get("isRequired", False)),
                    form_section=section_name,
                    display_order=int(q.get("displayOrder") or 1),
                    binding_key=q.get("bindingKey") or None,
                    options=[o for o in options if o],
                )
            )

    return questions


async def clone_template_to_program(program_id: int, template_id: int) -> None:
    """POST /program/form — clones all template sections/questions to a program.

    Uses the same endpoint as the infinipath-web FormBuilderEdit:
      endPoints.saveProgramForm = "program/form"
    with payload { programId, programTemplateId, cloneFromTemplate: true }.
    """
    client = await NestJSClient.get_instance()
    payload: dict[str, Any] = {
        "programId": program_id,
        "programTemplateId": template_id,
        "cloneFromTemplate": True,
    }
    with logfire.span("program_config.clone_template", program_id=program_id, template_id=template_id):
        await client.post("/program/form", payload)


async def publish_program(
    program_id: int,
    user_id: str = "",
    access_type: str = "PUBLIC",
    allowed_user_ids: list[int] | None = None,
) -> None:
    """PUT /program/{id}/status — publishes the program with the given access type.

    access_type must be one of: PUBLIC | INTERNAL | RESTRICTED (case-insensitive).
    Both INTERNAL and RESTRICTED require allowedUserIds to specify who can access.
    """
    client = await NestJSClient.get_instance()
    uid = int(user_id) if user_id and user_id.isdigit() else 1
    normalized = access_type.upper()
    payload: dict[str, Any] = {
        "status": "published",
        "updatedBy": uid,
        "accessType": normalized,
    }
    if normalized in ("INTERNAL", "RESTRICTED") and allowed_user_ids:
        payload["allowedUserIds"] = allowed_user_ids
    with logfire.span(
        "program_config.publish_program",
        program_id=program_id,
        access_type=normalized,
        allowed_user_ids=allowed_user_ids or [],
    ):
        await client.put(f"/program/{program_id}/status", payload)


def friendly_api_error(exc: Exception) -> str:
    """Return a user-facing error message that never leaks raw API response bodies."""
    msg = str(exc)
    if "NestJS" in msg or "httpx" in msg or "traceback" in msg.lower() or "{" in msg:
        return "An unexpected error occurred on the server. Please try again or contact support."
    if "typeId" in msg or "workflowId" in msg or "workflow_configuration" in msg:
        return "Program type configuration is missing. Please contact an administrator."
    if len(msg) > 200:
        return "An unexpected error occurred on the server. Please try again or contact support."
    return msg
