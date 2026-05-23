"""DB-driven type announcement — shown once when admin confirms a program type.

Replaces the hardcoded TYPE ANNOUNCEMENT TEMPLATES that previously lived in prompts.py.
All logic here is deterministic Python; no LLM is involved.
"""

from __future__ import annotations

from packages.agents.program_config.rules import get_missing_required_fields
from packages.agents.program_config.schemas import (
    CreateProgramDto,
    ModeOfOperation,
    OnlineType,
)

# ---------------------------------------------------------------------------
# Field format hints shown next to each missing field in the announcement
# ---------------------------------------------------------------------------

_FORMAT_HINTS: dict[str, str] = {
    "program name":                                        "e.g. Inner Awakening 2026",
    "mode of program (ONLINE / OFFLINE / HYBRID)":        "Online / Offline / Hybrid",
    "online type (MEETING / WEBINAR / LIVE_STREAM)":       "Meeting / Webinar / Live Stream",
    "venue name / address":                                "e.g. Isha Yoga Center, Coimbatore",
    "program start date":                                  "e.g. 10 Jun 2026",
    "program end date":                                    "e.g. 15 Jun 2026",
    "HDB fee (₹ amount)":                                  "₹ amount for HDB tier, e.g. ₹15,000",
    "MSD fee (₹ amount)":                                  "₹ amount for MSD tier, e.g. ₹8,000",
    "program fee / MSD fee (₹ amount)":                    "₹ amount, e.g. ₹2,500 — or 'free'",
    "at least 1 session (each session requires a name)":   "title, date, meeting link",
    "at least 1 sub-program (each sub-program requires a name)": "name, dates, venue, check-in/out",
}

# ---------------------------------------------------------------------------
# DTO population from DB row
# ---------------------------------------------------------------------------

def apply_type_config_to_dto(dto: CreateProgramDto, config: dict) -> CreateProgramDto:
    """Merge non-null program_type_v1 fields into the DTO.

    Returns a new DTO instance. Enum fields are converted from DB strings.
    Only overwrites fields that have a real value in the DB row — nulls are skipped.
    """
    data = dto.model_dump()

    # mode_of_operation
    raw_mode = (config.get("mode_of_operation") or "").upper()
    if raw_mode and raw_mode not in ("NA", "NONE", ""):
        try:
            data["mode_of_operation"] = ModeOfOperation(raw_mode)
        except ValueError:
            pass

    # online_type — skip placeholder "NA"
    raw_otype = (config.get("online_type") or "").upper()
    if raw_otype and raw_otype not in ("NA", "NONE", "NULL", ""):
        try:
            data["online_type"] = OnlineType(raw_otype)
        except ValueError:
            pass

    # Boolean structural flags — apply only when DB has an explicit non-null value
    bool_map = {
        "has_multiple_sessions": "has_multiple_sessions",
        "is_grouped_program":    "is_grouped_program",
        "requires_residence":    "is_residence_required",
        "involves_travel":       "is_travel_involved",
        "has_checkin_checkout":  "has_checkin_checkout",
        "requires_payment":      "requires_payment",
        "requires_approval":     "requires_approval",
        "waitlist_applicable":   "waitlist_applicable",
        "limited_seats":         "limited_seats",
    }
    for db_col, dto_field in bool_map.items():
        val = config.get(db_col)
        if val is not None:
            data[dto_field] = bool(val)

    # no_of_session — only if DB has a positive integer
    raw_sessions = config.get("no_of_session")
    if raw_sessions is not None and int(raw_sessions) > 0:
        data["no_of_session"] = int(raw_sessions)

    # venue and email_sender_name — only if non-empty strings
    for db_col, dto_field in (("venue", "venue"), ("email_sender_name", "email_sender_name")):
        raw = config.get(db_col)
        if raw and str(raw).strip():
            data[dto_field] = str(raw).strip()

    return CreateProgramDto.model_validate(data)


# ---------------------------------------------------------------------------
# Announcement message builder
# ---------------------------------------------------------------------------

_TYPE_LABELS: dict[str, str] = {
    "HDB":    "HDB (Higher Deeper Beyond) — Residential Retreat",
    "TAT":    "TAT (Training / Technology) — Multi-Session Program",
    "ENT":    "ENT (Entrainment) — Single Event",
    "CUSTOM": "CUSTOM — Fully Flexible",
}


def build_type_announcement(
    admin_type: str,
    config: dict | None,
    dto_after_apply: CreateProgramDto,
) -> str:
    """Build the one-time type announcement message shown to the admin.

    For CUSTOM (or when DB config is unavailable) returns the comprehensive
    flexible spec. For HDB/TAT/ENT uses the actual DB row to show what is
    pre-configured and what the admin still needs to provide.
    """
    if admin_type == "CUSTOM" or config is None:
        return _build_custom_announcement()

    return _build_standard_announcement(admin_type, config, dto_after_apply)


def _build_standard_announcement(
    admin_type: str,
    config: dict,
    dto: CreateProgramDto,
) -> str:
    label = _TYPE_LABELS.get(admin_type, admin_type)
    preconfigured = _describe_preconfigured(dto)
    missing = get_missing_required_fields(dto)

    lines: list[str] = [f"Got it — this is a **{label}** program.\n"]

    if preconfigured:
        lines.append("The following settings are **pre-configured** for this program type:\n")
        for item in preconfigured:
            lines.append(f"  ✅ {item}")
        lines.append("")

    if missing:
        lines.append("Here is everything I still need from you — share as many as you like in one reply:\n")
        for i, field in enumerate(missing, start=1):
            hint = _FORMAT_HINTS.get(field, "")
            hint_text = f" *({hint})*" if hint else ""
            lines.append(f"{i}. **{field}**{hint_text}")
        lines.append("")
        lines.append("Go ahead and share whatever you have — I'll ask for anything still missing.")
    else:
        lines.append("All required fields are already set — let me put together a preview for you.")

    return "\n".join(lines)


def _describe_preconfigured(dto: CreateProgramDto) -> list[str]:
    """Return human-readable lines for fields already set on the DTO from DB config."""
    lines: list[str] = []
    d = dto.model_dump()

    mode = d.get("mode_of_operation")
    if mode:
        val = mode.value if hasattr(mode, "value") else str(mode)
        otype = d.get("online_type")
        otype_str = f" ({otype.value if hasattr(otype, 'value') else otype})" if otype else ""
        lines.append(f"Mode: {val}{otype_str}")

    struct_map = [
        ("is_grouped_program",    "Structure: Grouped sub-programs"),
        ("has_multiple_sessions", "Structure: Multiple sessions"),
    ]
    for field, label in struct_map:
        if d.get(field) is True:
            lines.append(label)
            break
    else:
        if mode and not d.get("is_grouped_program") and not d.get("has_multiple_sessions"):
            lines.append("Structure: Single event")

    bool_labels = [
        ("is_residence_required", "Residential accommodation required"),
        ("is_travel_involved",    "Travel involved"),
        ("has_checkin_checkout",  "Check-in / check-out"),
        ("requires_payment",      "Payment required"),
        ("requires_approval",     "Approval required"),
        ("waitlist_applicable",   "Waitlist enabled"),
        ("limited_seats",         "Seat limit applies"),
    ]
    for field, label in bool_labels:
        if d.get(field) is True:
            lines.append(label)

    sessions = d.get("no_of_session")
    if sessions and int(sessions) > 0:
        lines.append(f"Default number of sessions: {sessions}")

    venue = d.get("venue")
    if venue:
        lines.append(f"Venue: {venue}")

    email_name = d.get("email_sender_name")
    if email_name:
        lines.append(f"Email sender name: {email_name}")

    return lines


def _build_custom_announcement() -> str:
    return """\
Got it — this is a **CUSTOM** program. You have full control over every setting.

Here's what I need from you — share as many details as you like in one reply:

**Required:**
1. **Program name** *(e.g. Special Retreat 2026)*
2. **Structure** *(choose one)*
   - **Single** — one standalone event, no sub-programs or sessions
   - **Multiple Sessions** — a set of repeating sessions (e.g. 12-week online course)
   - **Grouped Sub-Programs** — separate sub-events under one umbrella (e.g. HDB + MSD)
3. **Mode** *(Online / Offline / Hybrid)*
   - Online → I'll ask for online type (Meeting / Webinar / Live Stream) + link / ID / password
   - Offline → I'll ask for venue address
   - Hybrid → both

**Based on your structure + mode choices, I'll also collect:**
- If Online or Hybrid: **online type** + meeting / webinar / stream link details
- If Offline or Hybrid: **venue address** *(e.g. Isha Yoga Center, Coimbatore)*
- If Single event: **start date & time** and **end date & time**
- If Multiple Sessions: **number of sessions** + per-session title, dates, and link
- If Grouped Sub-Programs: **number of sub-programs** + per sub-program name, dates, venue, check-in/out

**Optional — share any of these now and I'll skip asking later:**
- Program fee *(₹ amount — or 'free')*
- Seat limit *(e.g. 100, or 'no limit')*
- Waitlist *(yes / no)*
- Requires approval *(yes / no)*
- Residential accommodation required *(yes / no)*
- Travel involved *(yes / no)*
- Check-in / check-out *(yes / no)*
- Registration open date *(e.g. 1 May 2026)*
- Registration close date *(e.g. 5 Jun 2026)*
- Email sender name *(shown on confirmation emails)*

Go ahead and share whatever you have — I'll ask for anything still missing."""
