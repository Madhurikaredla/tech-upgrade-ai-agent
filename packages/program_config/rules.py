from .models import CreateProgramDto, ModeOfOperation


def apply_rules(dto: CreateProgramDto) -> CreateProgramDto:
    """Apply all CUSTOM program type conditional rules, auto-computations, and field cleanup.

    Rules sourced from AI_AGENT_custom-program-type-product-spec.md.
    Must be called every time the partial DTO is updated.
    """
    data = dto.model_copy(deep=True)

    # --- FORCED VALUES ---
    # isTravelInvolved is always false when ONLINE
    if data.mode_of_operation == ModeOfOperation.ONLINE:
        data.is_travel_involved = False

    # currency is always INR
    data.currency = "INR"

    # --- AUTO-COMPUTATION ---
    # gst_percentage = cgst + sgst (never ask admin)
    if data.cgst is not None and data.sgst is not None:
        data.gst_percentage = data.cgst + data.sgst

    # --- STRUCTURE MUTUAL EXCLUSION ---
    # is_grouped_program and has_multiple_sessions cannot both be true
    if data.is_grouped_program and data.has_multiple_sessions:
        data.has_multiple_sessions = False

    # --- CLEANUP: venue fields when ONLINE ---
    if data.mode_of_operation == ModeOfOperation.ONLINE:
        data.venue = None
        data.venue_name_in_emails = None
        data.is_residence_required = False
        data.total_bed_count = None

    # --- CLEANUP: payment fields when requires_payment = false ---
    if not data.requires_payment:
        data.base_price = None
        data.program_fee = None
        data.gst_percentage = None
        data.cgst = None
        data.sgst = None
        data.igst = None
        data.gst_number = None
        data.tds_percent = None
        data.tds_applicability = None
        data.invoice_sender_name = None
        data.invoice_sender_pan = None
        data.invoice_sender_cin = None
        data.invoice_sender_address = None

    # --- CLEANUP: seat-cascade ---
    if not data.limited_seats:
        data.total_seats = None
        data.waitlist_applicable = False
        data.waitlist_trigger_count = None

    if not data.waitlist_applicable:
        data.waitlist_trigger_count = None

    # --- CLEANUP: checkin fields ---
    if not data.has_checkin_checkout:
        data.checkin_at = None
        data.checkin_ends_at = None
        data.checkout_at = None
        data.checkout_ends_at = None

    # --- CLEANUP: residence bed count ---
    if not data.is_residence_required:
        data.total_bed_count = None

    # --- CLEANUP: blessEndsAt ---
    if not data.requires_approval:
        data.bless_ends_at = None

    # --- CLEANUP: sessions / grouped lists ---
    if not data.has_multiple_sessions:
        data.program_sessions = []
        data.no_of_session = None

    if not data.is_grouped_program:
        data.grouped_programs = []

    return data


def get_missing_required_fields(dto: CreateProgramDto) -> list[str]:
    """Return human-readable labels of required fields still missing from the DTO."""
    missing: list[str] = []

    if not dto.name:
        missing.append("program name")

    if not dto.mode_of_operation:
        missing.append("mode of program (ONLINE / OFFLINE / HYBRID)")

    if dto.mode_of_operation in (ModeOfOperation.ONLINE, ModeOfOperation.HYBRID):
        if not dto.online_type:
            missing.append("online type (MEETING / WEBINAR / LIVE_STREAM)")

    if dto.mode_of_operation in (ModeOfOperation.OFFLINE, ModeOfOperation.HYBRID):
        if not dto.venue:
            missing.append("venue name / address")

    # ENT requires explicit start and end dates (not derived from sub-programs)
    if not dto.is_grouped_program and not dto.has_multiple_sessions:
        if not dto.starts_at:
            missing.append("program start date")
        if not dto.ends_at:
            missing.append("program end date")

    if dto.requires_payment:
        if dto.program_fee is None:
            missing.append("program fee / MSD fee (₹ amount)")
        # HDB has two fee tiers; base_price is the HDB-session fee
        if dto.is_grouped_program and dto.base_price is None:
            missing.append("HDB fee (₹ amount)")

    if dto.has_multiple_sessions:
        if not dto.program_sessions:
            missing.append("at least 1 session (each session requires a name)")
        elif dto.no_of_session is not None and dto.no_of_session != len(dto.program_sessions):
            missing.append(
                f"session count mismatch — declared {dto.no_of_session} "
                f"but {len(dto.program_sessions)} added"
            )

    if dto.is_grouped_program and not dto.grouped_programs:
        missing.append("at least 1 sub-program (each sub-program requires a name)")

    return missing


def validate_for_publish(dto: CreateProgramDto) -> list[str]:
    """Return all validation errors that must be resolved before publishing."""
    errors = get_missing_required_fields(dto)

    if dto.starts_at and dto.ends_at and dto.starts_at >= dto.ends_at:
        errors.append("program end date must be after start date")

    if (
        dto.registration_starts_at
        and dto.registration_ends_at
        and dto.registration_starts_at >= dto.registration_ends_at
    ):
        errors.append("registration end must be after registration start")

    if (
        dto.registration_ends_at
        and dto.starts_at
        and dto.registration_ends_at > dto.starts_at
    ):
        errors.append("registration must close before the program starts")

    return errors
