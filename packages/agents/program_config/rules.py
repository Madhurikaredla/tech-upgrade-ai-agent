from .schemas import CreateProgramDto, ModeOfOperation


def apply_rules(dto: CreateProgramDto) -> CreateProgramDto:
    """Apply all conditional rules, auto-computations, and field cleanup.

    Must be called every time the partial DTO is updated.
    Rules sourced from AI_AGENT_custom-program-type-product-spec.md.
    """
    data = dto.model_copy(deep=True)

    data.currency = "INR"

    # --- AUTO-DERIVE structural flags from populated lists (must run first) ---
    # If the agent extracted sub-programs/sessions but forgot the parent flag,
    # infer it so downstream HDB detection and cleanup work correctly.
    if data.grouped_programs:
        data.is_grouped_program = True
    if data.program_sessions:
        data.has_multiple_sessions = True

    # --- AUTO-DETECT HDB type ---
    # Lenient: is_grouped_program + is_residence_required is enough to identify HDB.
    # The agent reliably sets these two but may forget the others.
    if not data.sub_program_type and data.is_grouped_program and data.is_residence_required:
        data.sub_program_type = "HDB"

    # --- HDB: force all structural flags and mode by code, not just by prompt ---
    if data.sub_program_type == "HDB":
        data.requires_payment = True
        data.is_grouped_program = True
        data.is_residence_required = True
        data.has_checkin_checkout = True
        data.requires_approval = True
        data.is_travel_involved = True
        if not data.mode_of_operation:
            data.mode_of_operation = ModeOfOperation.OFFLINE

    # --- AUTO-DERIVE parent dates from sub-program / session dates ---
    # Only fills in dates that aren't already set; ISO strings sort lexicographically.
    if data.is_grouped_program and data.grouped_programs:
        sub_starts = [g.starts_at for g in data.grouped_programs if g.starts_at]
        sub_ends = [g.ends_at for g in data.grouped_programs if g.ends_at]
        if sub_starts and not data.starts_at:
            data.starts_at = min(sub_starts)
        if sub_ends and not data.ends_at:
            data.ends_at = max(sub_ends)
    if data.has_multiple_sessions and data.program_sessions:
        sess_starts = [s.starts_at for s in data.program_sessions if s.starts_at]
        sess_ends = [s.ends_at for s in data.program_sessions if s.ends_at]
        if sess_starts and not data.starts_at:
            data.starts_at = min(sess_starts)
        if sess_ends and not data.ends_at:
            data.ends_at = max(sess_ends)

    # --- AUTO-COMPUTATION ---
    if data.cgst is not None and data.sgst is not None:
        data.gst_percentage = data.cgst + data.sgst

    # --- FORCED VALUES ---
    if data.mode_of_operation == ModeOfOperation.ONLINE:
        data.is_travel_involved = False

    # --- STRUCTURE MUTUAL EXCLUSION ---
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

    # --- AUTO-FIX display orders — NestJS reserves order=1 for the primary program;
    # sub-programs must start from 2. Sessions use 1-based ordering (no reservation).
    for i, g in enumerate(data.grouped_programs, start=2):
        g.group_display_order = i
    for i, s in enumerate(data.program_sessions, start=1):
        s.display_order = i

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

    if not dto.is_grouped_program and not dto.has_multiple_sessions:
        if not dto.starts_at:
            missing.append("program start date")
        if not dto.ends_at:
            missing.append("program end date")

    # HDB always needs both fees regardless of requires_payment flag
    if dto.sub_program_type == "HDB":
        if dto.base_price is None:
            missing.append("HDB fee (₹ amount)")
        if dto.program_fee is None:
            missing.append("MSD fee (₹ amount)")
    elif dto.requires_payment:
        if dto.program_fee is None:
            missing.append("program fee / MSD fee (₹ amount)")
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

    if not dto.registration_starts_at:
        missing.append("registration open date & time (e.g. 21 May 2026, 9:00 AM)")
    if not dto.registration_ends_at:
        missing.append("registration close date & time (e.g. 25 Sep 2026, 9:00 AM)")

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

    return errors
