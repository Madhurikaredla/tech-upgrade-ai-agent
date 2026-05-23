"""Unit tests for program config models and template question sets."""

import pytest

from packages.agents.program_config.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentStage,
    CreateProgramDto,
    ModeOfOperation,
    OnlineType,
    ProgramQuestionDto,
    SessionState,
)
from packages.agents.program_config.templates import TEMPLATES, get_template_questions


class TestCreateProgramDto:
    def test_defaults(self):
        dto = CreateProgramDto()
        assert dto.currency == "INR"
        assert dto.is_travel_involved is False
        assert dto.requires_payment is False
        assert dto.limited_seats is False
        assert dto.program_sessions == []
        assert dto.grouped_programs == []

    def test_mode_of_operation_enum(self):
        dto = CreateProgramDto(mode_of_operation="ONLINE")
        assert dto.mode_of_operation == ModeOfOperation.ONLINE

    def test_serialise_exclude_none(self):
        dto = CreateProgramDto(name="Test", mode_of_operation=ModeOfOperation.ONLINE)
        data = dto.model_dump(exclude_none=True)
        assert "name" in data
        assert "venue" not in data
        assert "program_fee" not in data


class TestSessionState:
    def test_default_stage_is_collecting(self):
        state = SessionState()
        assert state.stage == AgentStage.COLLECTING

    def test_session_id_auto_generated(self):
        s1 = SessionState()
        s2 = SessionState()
        assert s1.session_id != s2.session_id

    def test_partial_dto_is_fresh_per_session(self):
        s1 = SessionState()
        s2 = SessionState()
        s1.partial_dto.name = "changed"
        assert s2.partial_dto.name is None


class TestAgentChatRequest:
    def test_message_required(self):
        with pytest.raises(Exception):
            AgentChatRequest(user_id="u1")  # missing message

    def test_session_id_auto_generated(self):
        r1 = AgentChatRequest(message="hello", user_id="u1")
        r2 = AgentChatRequest(message="hello", user_id="u1")
        assert r1.session_id != r2.session_id

    def test_explicit_session_id_preserved(self):
        req = AgentChatRequest(session_id="my-session", message="hello", user_id="u1")
        assert req.session_id == "my-session"


class TestAgentChatResponse:
    def test_success_default_true(self):
        resp = AgentChatResponse(
            session_id="s1",
            reply="hi",
            stage=AgentStage.COLLECTING,
        )
        assert resp.success is True

    def test_error_response(self):
        resp = AgentChatResponse(
            session_id="s1",
            reply="error",
            stage=AgentStage.COLLECTING,
            success=False,
        )
        assert resp.success is False


class TestTemplates:
    def test_all_template_types_registered(self):
        for key in ("HDB", "MSD", "TAT", "CUSTOM"):
            assert key in TEMPLATES

    def test_all_templates_have_personal_questions(self):
        required_bindings = {"fullName", "dob", "gender", "mobileNumber", "emailAddress", "city"}
        for key, questions in TEMPLATES.items():
            bindings = {q.binding_key for q in questions if q.binding_key}
            assert required_bindings.issubset(bindings), f"{key} template missing personal questions"

    def test_hdb_has_extra_sections(self):
        sections = {q.form_section for q in TEMPLATES["HDB"]}
        assert "Program History" in sections
        assert "Preferences" in sections

    def test_get_template_questions_returns_copy(self):
        q1 = get_template_questions("HDB")
        q2 = get_template_questions("HDB")
        q1[0].question_text = "MUTATED"
        assert q2[0].question_text != "MUTATED"

    def test_unknown_type_falls_back_to_personal_questions(self):
        questions = get_template_questions("UNKNOWN_TYPE")
        assert len(questions) > 0
        binding_keys = {q.binding_key for q in questions if q.binding_key}
        assert "fullName" in binding_keys

    def test_none_type_falls_back_to_custom(self):
        questions = get_template_questions(None)
        assert len(questions) > 0

    def test_case_insensitive_lookup(self):
        lower = get_template_questions("hdb")
        upper = get_template_questions("HDB")
        assert len(lower) == len(upper)
