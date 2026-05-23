"""Unit tests for program config rules — conditional logic, cleanup, validation."""

import pytest

from packages.agents.program_config.schemas import (
    CreateProgramDto,
    ModeOfOperation,
    OnlineType,
    ProgramSessionDto,
)
from packages.agents.program_config.rules import (
    apply_rules,
    get_missing_required_fields,
    validate_for_publish,
)


# ---------------------------------------------------------------------------
# apply_rules — forced values
# ---------------------------------------------------------------------------

class TestForcedValues:
    def test_travel_forced_false_when_online(self):
        dto = CreateProgramDto(
            mode_of_operation=ModeOfOperation.ONLINE,
            is_travel_involved=True,
        )
        result = apply_rules(dto)
        assert result.is_travel_involved is False

    def test_travel_preserved_when_offline(self):
        dto = CreateProgramDto(
            mode_of_operation=ModeOfOperation.OFFLINE,
            is_travel_involved=True,
        )
        result = apply_rules(dto)
        assert result.is_travel_involved is True

    def test_currency_always_inr(self):
        dto = CreateProgramDto(currency="USD")
        result = apply_rules(dto)
        assert result.currency == "INR"

    def test_gst_auto_computed_from_cgst_sgst(self):
        dto = CreateProgramDto(requires_payment=True, cgst=9.0, sgst=9.0)
        result = apply_rules(dto)
        assert result.gst_percentage == 18.0


# ---------------------------------------------------------------------------
# apply_rules — venue cleanup
# ---------------------------------------------------------------------------

class TestVenueCleanup:
    def test_venue_cleared_when_online(self):
        dto = CreateProgramDto(
            mode_of_operation=ModeOfOperation.ONLINE,
            venue="Some Hall",
            venue_name_in_emails="Hall Name",
            is_residence_required=True,
            total_bed_count=50,
        )
        result = apply_rules(dto)
        assert result.venue is None
        assert result.venue_name_in_emails is None
        assert result.is_residence_required is False
        assert result.total_bed_count is None

    def test_venue_kept_when_offline(self):
        dto = CreateProgramDto(
            mode_of_operation=ModeOfOperation.OFFLINE,
            venue="Retreat Centre",
        )
        result = apply_rules(dto)
        assert result.venue == "Retreat Centre"

    def test_bed_count_cleared_when_residence_not_required(self):
        dto = CreateProgramDto(
            mode_of_operation=ModeOfOperation.OFFLINE,
            is_residence_required=False,
            total_bed_count=100,
        )
        result = apply_rules(dto)
        assert result.total_bed_count is None


# ---------------------------------------------------------------------------
# apply_rules — payment cleanup
# ---------------------------------------------------------------------------

class TestPaymentCleanup:
    def test_payment_fields_cleared_when_not_required(self):
        dto = CreateProgramDto(
            requires_payment=False,
            program_fee=5000.0,
            cgst=9.0,
            sgst=9.0,
            invoice_sender_name="Infinitheism",
        )
        result = apply_rules(dto)
        assert result.program_fee is None
        assert result.cgst is None
        assert result.sgst is None
        assert result.invoice_sender_name is None

    def test_payment_fields_kept_when_required(self):
        dto = CreateProgramDto(
            requires_payment=True,
            program_fee=5000.0,
        )
        result = apply_rules(dto)
        assert result.program_fee == 5000.0


# ---------------------------------------------------------------------------
# apply_rules — seat cascade
# ---------------------------------------------------------------------------

class TestSeatCascade:
    def test_seats_cleared_when_no_limit(self):
        dto = CreateProgramDto(
            limited_seats=False,
            total_seats=100,
            waitlist_applicable=True,
            waitlist_trigger_count=80,
        )
        result = apply_rules(dto)
        assert result.total_seats is None
        assert result.waitlist_applicable is False
        assert result.waitlist_trigger_count is None

    def test_waitlist_trigger_cleared_when_waitlist_off(self):
        dto = CreateProgramDto(
            limited_seats=True,
            total_seats=100,
            waitlist_applicable=False,
            waitlist_trigger_count=80,
        )
        result = apply_rules(dto)
        assert result.waitlist_trigger_count is None


# ---------------------------------------------------------------------------
# apply_rules — sessions / grouped cleanup
# ---------------------------------------------------------------------------

class TestStructureCleanup:
    def test_sessions_cleared_when_not_multiple_sessions(self):
        session = ProgramSessionDto(name="Morning Session")
        dto = CreateProgramDto(
            has_multiple_sessions=False,
            program_sessions=[session],
            no_of_session=1,
        )
        result = apply_rules(dto)
        assert result.program_sessions == []
        assert result.no_of_session is None

    def test_grouped_cleared_when_not_grouped(self):
        dto = CreateProgramDto(is_grouped_program=False)
        result = apply_rules(dto)
        assert result.grouped_programs == []


# ---------------------------------------------------------------------------
# get_missing_required_fields
# ---------------------------------------------------------------------------

class TestMissingRequiredFields:
    def test_name_missing(self):
        dto = CreateProgramDto(mode_of_operation=ModeOfOperation.ONLINE, online_type=OnlineType.MEETING)
        missing = get_missing_required_fields(dto)
        assert "program name" in missing

    def test_mode_missing(self):
        dto = CreateProgramDto(name="HDB June 2026")
        missing = get_missing_required_fields(dto)
        assert "mode of program (ONLINE / OFFLINE / HYBRID)" in missing

    def test_online_type_missing_when_online(self):
        dto = CreateProgramDto(name="HDB", mode_of_operation=ModeOfOperation.ONLINE)
        missing = get_missing_required_fields(dto)
        assert "online type (MEETING / WEBINAR / LIVE_STREAM)" in missing

    def test_online_type_not_required_when_offline(self):
        dto = CreateProgramDto(
            name="HDB",
            mode_of_operation=ModeOfOperation.OFFLINE,
            venue="Retreat Centre",
        )
        missing = get_missing_required_fields(dto)
        assert not any("online type" in m for m in missing)

    def test_venue_required_when_offline(self):
        dto = CreateProgramDto(name="HDB", mode_of_operation=ModeOfOperation.OFFLINE)
        missing = get_missing_required_fields(dto)
        assert "venue name / address" in missing

    def test_fee_required_when_payment_enabled(self):
        dto = CreateProgramDto(
            name="HDB",
            mode_of_operation=ModeOfOperation.ONLINE,
            online_type=OnlineType.MEETING,
            requires_payment=True,
        )
        missing = get_missing_required_fields(dto)
        assert "program fee / MSD fee (₹ amount)" in missing

    def test_all_required_present_online(self):
        dto = CreateProgramDto(
            name="HDB June 2026",
            mode_of_operation=ModeOfOperation.ONLINE,
            online_type=OnlineType.MEETING,
            starts_at="2026-06-15",
            ends_at="2026-06-20",
        )
        assert get_missing_required_fields(dto) == []

    def test_all_required_present_offline(self):
        dto = CreateProgramDto(
            name="HDB June 2026",
            mode_of_operation=ModeOfOperation.OFFLINE,
            venue="Infinitheism Centre",
            starts_at="2026-06-15",
            ends_at="2026-06-20",
        )
        assert get_missing_required_fields(dto) == []


# ---------------------------------------------------------------------------
# validate_for_publish — date ordering
# ---------------------------------------------------------------------------

class TestPublishValidation:
    def test_end_before_start_flagged(self):
        dto = CreateProgramDto(
            name="HDB",
            mode_of_operation=ModeOfOperation.ONLINE,
            online_type=OnlineType.MEETING,
            starts_at="2026-06-20",
            ends_at="2026-06-15",
        )
        errors = validate_for_publish(dto)
        assert any("end date must be after start date" in e for e in errors)

    def test_registration_end_after_program_start_flagged(self):
        dto = CreateProgramDto(
            name="HDB",
            mode_of_operation=ModeOfOperation.ONLINE,
            online_type=OnlineType.MEETING,
            starts_at="2026-06-15",
            registration_starts_at="2026-06-01",
            registration_ends_at="2026-06-20",  # after program start
        )
        errors = validate_for_publish(dto)
        assert any("registration must close before the program starts" in e for e in errors)

    def test_valid_dates_no_errors(self):
        dto = CreateProgramDto(
            name="HDB",
            mode_of_operation=ModeOfOperation.ONLINE,
            online_type=OnlineType.MEETING,
            starts_at="2026-06-15",
            ends_at="2026-06-20",
            registration_starts_at="2026-06-01",
            registration_ends_at="2026-06-10",
        )
        assert validate_for_publish(dto) == []
