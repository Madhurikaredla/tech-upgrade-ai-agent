"""Default template question sets per program type.

These mirror the standard question libraries used by HDB, MSD, TAT, and CUSTOM
program types. When the admin approves the form during the agent flow, these
questions are attached to the created program via addQuestionsFromTemplate.

New template types can be added by extending the TEMPLATES dict — no code
changes needed in the agent or runner.
"""

from .schemas import ProgramQuestionDto

_PERSONAL_QUESTIONS: list[ProgramQuestionDto] = [
    ProgramQuestionDto(
        question_text="Full Name",
        question_type="text",
        is_required=True,
        form_section="Personal Details",
        display_order=1,
        binding_key="fullName",
    ),
    ProgramQuestionDto(
        question_text="Date of Birth",
        question_type="date",
        is_required=True,
        form_section="Personal Details",
        display_order=2,
        binding_key="dob",
    ),
    ProgramQuestionDto(
        question_text="Gender",
        question_type="radio",
        is_required=True,
        form_section="Personal Details",
        display_order=3,
        binding_key="gender",
        options=["Male", "Female", "Other"],
    ),
    ProgramQuestionDto(
        question_text="Mobile Number",
        question_type="text",
        is_required=True,
        form_section="Personal Details",
        display_order=4,
        binding_key="mobileNumber",
    ),
    ProgramQuestionDto(
        question_text="Email Address",
        question_type="email",
        is_required=True,
        form_section="Personal Details",
        display_order=5,
        binding_key="emailAddress",
    ),
    ProgramQuestionDto(
        question_text="City",
        question_type="text",
        is_required=True,
        form_section="Personal Details",
        display_order=6,
        binding_key="city",
    ),
]

_HDB_QUESTIONS: list[ProgramQuestionDto] = [
    *_PERSONAL_QUESTIONS,
    ProgramQuestionDto(
        question_text="Last HDB Attended",
        question_type="text",
        is_required=False,
        form_section="Program History",
        display_order=1,
    ),
    ProgramQuestionDto(
        question_text="HDB Association Since",
        question_type="date",
        is_required=False,
        form_section="Program History",
        display_order=2,
    ),
    ProgramQuestionDto(
        question_text="Other Infinitheism Contact",
        question_type="text",
        is_required=False,
        form_section="Program History",
        display_order=3,
    ),
    ProgramQuestionDto(
        question_text="First Song Preference",
        question_type="text",
        is_required=False,
        form_section="Preferences",
        display_order=1,
    ),
    ProgramQuestionDto(
        question_text="Second Song Preference",
        question_type="text",
        is_required=False,
        form_section="Preferences",
        display_order=2,
    ),
    ProgramQuestionDto(
        question_text="Preferred Roommate",
        question_type="text",
        is_required=False,
        form_section="Preferences",
        display_order=3,
    ),
]

_MSD_QUESTIONS: list[ProgramQuestionDto] = [
    *_PERSONAL_QUESTIONS,
    ProgramQuestionDto(
        question_text="Last MSD Attended",
        question_type="text",
        is_required=False,
        form_section="Program History",
        display_order=1,
    ),
    ProgramQuestionDto(
        question_text="Dietary Preference",
        question_type="select",
        is_required=False,
        form_section="Preferences",
        display_order=1,
        options=["Vegetarian", "Non-Vegetarian", "Vegan"],
    ),
]

_TAT_QUESTIONS: list[ProgramQuestionDto] = [
    *_PERSONAL_QUESTIONS,
    ProgramQuestionDto(
        question_text="Preferred Language",
        question_type="select",
        is_required=False,
        form_section="Preferences",
        display_order=1,
        options=["English", "Tamil", "Telugu", "Hindi"],
    ),
    ProgramQuestionDto(
        question_text="Prior Meditation Experience",
        question_type="radio",
        is_required=False,
        form_section="Program History",
        display_order=1,
        options=["Yes", "No"],
    ),
]

TEMPLATES: dict[str, list[ProgramQuestionDto]] = {
    "HDB": _HDB_QUESTIONS,
    "MSD": _MSD_QUESTIONS,
    "TAT": _TAT_QUESTIONS,
    "ENT": list(_PERSONAL_QUESTIONS),
    "CUSTOM": list(_PERSONAL_QUESTIONS),
}


def get_template_questions(sub_program_type: str | None) -> list[ProgramQuestionDto]:
    """Return a fresh copy of the template question list for the given program type."""
    key = (sub_program_type or "CUSTOM").upper()
    source = TEMPLATES.get(key, list(_PERSONAL_QUESTIONS))
    return [q.model_copy() for q in source]
