"""All Pydantic models for the program_config agent.

Covers:
- Domain DTOs (CreateProgramDto, GroupedProgramDto, ProgramSessionDto)
- Agent output type (ProgramConfigTurn)
- Session state (SessionState)
- API contracts (AgentChatRequest, AgentChatResponse)
- Form models (ProgramQuestionDto)
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModeOfOperation(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    HYBRID = "HYBRID"


class OnlineType(str, Enum):
    MEETING = "MEETING"
    WEBINAR = "WEBINAR"
    LIVE_STREAM = "LIVE_STREAM"


class AgentStage(str, Enum):
    COLLECTING = "COLLECTING"
    TEMPLATE_SELECTION = "TEMPLATE_SELECTION"
    PROGRAM_PREVIEW = "PROGRAM_PREVIEW"
    PROGRAM_CREATED = "PROGRAM_CREATED"
    FORM_PREVIEW = "FORM_PREVIEW"
    FORM_ATTACHED = "FORM_ATTACHED"
    READY_TO_PUBLISH = "READY_TO_PUBLISH"
    PUBLISHED = "PUBLISHED"


class GroupedProgramDto(BaseModel):
    name: str
    group_display_order: int = 1
    code: str | None = None
    description: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    mode_of_operation: ModeOfOperation | None = None
    venue_address: str | None = None
    checkin_at: str | None = None
    checkin_ends_at: str | None = None
    checkout_at: str | None = None
    checkout_ends_at: str | None = None
    limited_seats: bool = False
    total_seats: int | None = None
    waitlist_applicable: bool = False
    waitlist_trigger_count: int | None = None


class ProgramSessionDto(BaseModel):
    name: str
    code: str | None = None
    display_order: int = 1
    starts_at: str | None = None
    ends_at: str | None = None
    mode_of_operation: ModeOfOperation | None = None
    meeting_link: str | None = None
    meeting_id: str | None = None
    meeting_password: str | None = None
    venue_address: str | None = None
    checkin_at: str | None = None
    checkout_at: str | None = None
    limited_seats: bool = False
    total_seats: int | None = None
    waitlist_applicable: bool = False
    waitlist_trigger_count: int | None = None
    description: str | None = None


class CreateProgramDto(BaseModel):
    # NestJS FK fields — resolved from workflow_configuration table
    type_id: int | None = None
    workflow_id: int | None = None

    # Section 1 — Basic Info
    name: str | None = None
    code: str | None = None
    description: str | None = None
    launch_date: str | None = None
    logo_url: str | None = None
    banner_image_url: str | None = None
    sub_program_type: str | None = None

    # Section 2 — Mode & Structure
    mode_of_operation: ModeOfOperation | None = None
    online_type: OnlineType | None = None
    is_grouped_program: bool = False
    has_multiple_sessions: bool = False
    no_of_session: int | None = None

    # Section 3 — Registration Rules
    requires_approval: bool = False
    allows_proxy_registration: bool = False
    allow_save_as_draft: bool = False
    allows_minors: bool = False
    elder_min_age: int | None = None
    child_max_age: int | None = None
    seeker_can_share_experience: bool = False

    # Section 4 — Schedule & Dates
    starts_at: str | None = None
    ends_at: str | None = None
    bless_ends_at: str | None = None
    registration_starts_at: str | None = None
    registration_ends_at: str | None = None
    default_start_time: str | None = None
    default_end_time: str | None = None
    has_checkin_checkout: bool = False
    checkin_at: str | None = None
    checkin_ends_at: str | None = None
    checkout_at: str | None = None
    checkout_ends_at: str | None = None

    # Section 5 — Venue & Location (offline / hybrid only)
    venue: str | None = None
    venue_name_in_emails: str | None = None
    is_residence_required: bool = False
    total_bed_count: int | None = None

    # Section 6 — Seats & Capacity
    limited_seats: bool = False
    total_seats: int | None = None
    waitlist_applicable: bool = False
    waitlist_trigger_count: int | None = None

    # Section 7 — Program Features
    requires_payment: bool = False
    is_travel_involved: bool = False  # auto-forced false when ONLINE

    # Section 8 — Payment & Billing (visible only when requires_payment = true)
    currency: str = "INR"  # always INR, never ask admin
    base_price: float | None = None
    program_fee: float | None = None
    gst_percentage: float | None = None  # auto-computed: cgst + sgst
    cgst: float | None = None
    sgst: float | None = None
    igst: float | None = None
    gst_number: str | None = None
    tds_percent: float | None = None
    tds_applicability: str | None = None
    invoice_sender_name: str | None = None
    invoice_sender_pan: str | None = None
    invoice_sender_cin: str | None = None
    invoice_sender_address: str | None = None

    # Section 9 — Email & Communication
    email_sender_name: str | None = None
    email_sender_address: str | None = None
    email_bcc_name: str | None = None
    email_bcc_address: str | None = None
    helpline_number: str | None = None

    # Section 10 — Grouped Sub-Programs
    grouped_programs: list[GroupedProgramDto] = Field(default_factory=list)

    # Section 11 — Sessions
    program_sessions: list[ProgramSessionDto] = Field(default_factory=list)

    # Section 12 — Advanced
    meta: str | None = None


class PriceEntry(BaseModel):
    HDB: float | None = None
    MSD: float | None = None


class MetaDto(BaseModel):
    """Typed meta payload — replaces dict[str, Any] so Gemini can reliably populate it."""

    price: PriceEntry | None = None
    programStructure: str | None = None  # "Single" | "Multiple" | "Grouped"
    noOfSubPrograms: int | None = None
    sameVenueForAll: bool | None = None
    sameOnlineDetailsForAll: bool | None = None
    hasGoodies: str | None = None  # "YES"


class ProgramQuestionDto(BaseModel):
    question_text: str
    question_type: str
    is_required: bool = False
    form_section: str = "General"
    display_order: int = 1
    binding_key: str | None = None
    options: list[str] = Field(default_factory=list)


class ExtractedFields(BaseModel):
    """Typed extraction output — only fields explicitly extracted by the agent.

    All fields default to None so that unmentioned fields are cleanly excluded
    from the DTO merge (model_dump(exclude_none=True)).
    """

    # Basic info
    name: str | None = None
    code: str | None = None
    description: str | None = None
    logo_url: str | None = None
    banner_image_url: str | None = None
    sub_program_type: str | None = None

    # Mode & structure
    mode_of_operation: ModeOfOperation | None = None
    online_type: OnlineType | None = None
    is_grouped_program: bool | None = None
    has_multiple_sessions: bool | None = None
    no_of_session: int | None = None

    # Registration rules
    requires_approval: bool | None = None
    allows_proxy_registration: bool | None = None
    allow_save_as_draft: bool | None = None
    allows_minors: bool | None = None
    elder_min_age: int | None = None
    child_max_age: int | None = None

    # Dates
    starts_at: str | None = None
    ends_at: str | None = None
    registration_starts_at: str | None = None
    registration_ends_at: str | None = None
    has_checkin_checkout: bool | None = None
    checkin_at: str | None = None
    checkin_ends_at: str | None = None
    checkout_at: str | None = None
    checkout_ends_at: str | None = None

    # Venue
    venue: str | None = None
    venue_name_in_emails: str | None = None
    is_residence_required: bool | None = None
    is_travel_involved: bool | None = None
    total_bed_count: int | None = None

    # Seats
    limited_seats: bool | None = None
    total_seats: int | None = None
    waitlist_applicable: bool | None = None
    waitlist_trigger_count: int | None = None

    # Payment
    requires_payment: bool | None = None
    base_price: float | None = None
    program_fee: float | None = None
    cgst: float | None = None
    sgst: float | None = None
    igst: float | None = None
    gst_number: str | None = None
    tds_percent: float | None = None
    invoice_sender_name: str | None = None

    # Email
    email_sender_name: str | None = None

    # Sub-programs and sessions (None = not extracted this turn)
    grouped_programs: list[GroupedProgramDto] | None = None
    program_sessions: list[ProgramSessionDto] | None = None

    # Meta object (merged, not replaced) — typed so Gemini populates it reliably
    meta: MetaDto | None = None


class ProgramConfigTurn(BaseModel):
    """Structured output the extraction agent returns each conversation step."""

    reply: str
    extracted_fields: ExtractedFields = Field(default_factory=ExtractedFields)
    all_required_collected: bool = False


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    stage: AgentStage = AgentStage.COLLECTING
    partial_dto: CreateProgramDto = Field(default_factory=CreateProgramDto)
    program_id: int | None = None
    template_questions: list[ProgramQuestionDto] = Field(default_factory=list)
    program_type_key: str | None = None  # canonical admin type: HDB / TAT / ENT / CUSTOM
    # Template selection
    template_id: int | None = None           # backend template ID chosen by admin
    template_name: str | None = None         # display name of selected template
    available_templates: list[Any] = Field(default_factory=list)  # fetched from backend


class AgentChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = Field(..., min_length=1, max_length=10_000)
    user_id: str = Field(..., min_length=1)


class AgentChatResponse(BaseModel):
    session_id: str
    reply: str
    stage: AgentStage
    dto_preview: dict[str, Any] | None = None
    form_preview: list[ProgramQuestionDto] | None = None
    requires_confirmation: bool = False
    program_id: int | None = None
    success: bool = True
