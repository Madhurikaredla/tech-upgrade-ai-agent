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
    # NestJS FK fields — resolved from /workflow/program-type/:key
    type_id: int | None = None
    workflow_id: int | None = None

    # Section 1 — Basic Info
    name: str | None = None
    code: str | None = None
    description: str | None = None
    launch_date: str | None = None
    logo_url: str | None = None
    sub_program_type: str | None = None

    # Section 2 — Mode & Structure
    mode_of_operation: ModeOfOperation | None = None
    online_type: OnlineType | None = None
    # programStructure maps to these two booleans; both false = Single
    is_grouped_program: bool = False
    has_multiple_sessions: bool = False
    no_of_session: int | None = None

    # Section 3 — Registration Rules
    requires_approval: bool = False
    allows_proxy_registration: bool = False
    allow_save_as_draft: bool = False
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

    # Section 10 — Grouped Sub-Programs (visible when is_grouped_program = true)
    grouped_programs: list[GroupedProgramDto] = Field(default_factory=list)

    # Section 11 — Sessions (visible when has_multiple_sessions = true)
    program_sessions: list[ProgramSessionDto] = Field(default_factory=list)

    # Section 12 — Advanced
    meta: str | None = None


class ProgramQuestionDto(BaseModel):
    question_text: str
    question_type: str
    is_required: bool = False
    form_section: str = "General"
    display_order: int = 1
    binding_key: str | None = None
    options: list[str] = Field(default_factory=list)


class ProgramConfigTurn(BaseModel):
    """Structured turn the extraction agent returns each conversation step."""

    reply: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    all_required_collected: bool = False


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    stage: AgentStage = AgentStage.COLLECTING
    partial_dto: CreateProgramDto = Field(default_factory=CreateProgramDto)
    program_id: int | None = None
    template_questions: list[ProgramQuestionDto] = Field(default_factory=list)


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
