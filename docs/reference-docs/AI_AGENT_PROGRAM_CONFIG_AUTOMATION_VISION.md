# AI Agent — Program Configuration Automation Vision

**Version:** v1.0 | **Date:** 2026-05-18

---

## 1. Purpose of This Document

This document captures:
- How an admin **currently** creates a program (manual multi-screen flow)
- What the **AI agent will automate** end-to-end via a single prompt
- The **predefined rules** the agent must enforce (derived from the CUSTOM program type spec)
- How **new form fields** can be added to the agent's knowledge base
- How the **custom template** pattern works and how the agent uses it

---

## 2. Current Admin Flow — What We Are Replacing

Today, creating and publishing a program requires an admin to navigate **four separate stages** across multiple UI screens:

### Stage A — Program Meta Creation

Admin opens the program creation form and manually fills all required fields across 12 sections:

```
Section 1  — Basic Info
             programName, programCode, description, launchDate, logoUrl, subProgramType

Section 2  — Mode & Structure
             modeOfProgram (ONLINE/OFFLINE/HYBRID)
             onlineType (MEETING/WEBINAR/LIVE_STREAM) — shown only if online or hybrid
             programStructure (Single / Sessions / Programs)

Section 3  — Registration Rules
             approvalRequired, allowsProxyRegistration, allowSaveAsDraft
             elderMinAge, childMaxAge, seekerCanShareExperience

Section 4  — Schedule & Dates
             startsAt, endsAt (daterange)
             blessEndsAt — shown only if approvalRequired = yes
             registrationStartsAt, registrationEndsAt
             defaultStartTime, defaultEndTime
             noOfSession — shown only if programStructure = Sessions
             hasCheckinCheckout → checkinAt, checkinEndsAt, checkoutAt, checkoutEndsAt

Section 5  — Venue & Location (offline / hybrid only)
             venue, venueNameInEmail, isResidenceRequired
             totalBedCount — shown only if isResidenceRequired = yes

Section 6  — Seats & Capacity
             hasSeatLimit → totalSeats
             waitlistApplicable → waitlistTriggerCount

Section 7  — Program Features
             requiresPayment (shows/hides Payment section)
             isTravelInvolved (auto-disabled + forced false when mode = ONLINE)

Section 8  — Payment & Billing (only if requiresPayment = yes)
             currency (INR, disabled), basePrice, programFee
             gstPercentage (auto-calc from cgst + sgst), cgst, sgst, igst, gstNumber
             tdsPercent, tdsApplicability
             invoiceSenderName, invoiceSenderPan, invoiceSenderCin, invoiceSenderAddress

Section 9  — Email & Communication
             emailSenderName, emailSenderAddress
             emailBccName, emailBccAddress, helplineNumber

Section 10 — Grouped Sub-Programs (only if programStructure = Programs)
             One or more GroupedProgramDto entries, each with:
             name, groupDisplayOrder, code, description, startsAt/endsAt
             modeOfOperation, venueAddress, checkin/checkout datetimes
             hasSeatLimit, totalSeats, waitlistApplicable, waitlistTriggerCount

Section 11 — Sessions (only if programStructure = Sessions)
             One or more CreateProgramSessionDto entries, each with:
             name, code, displayOrder, startsAt/endsAt, modeOfOperation
             meetingLink, meetingId, meetingPassword (online/hybrid only)
             venueAddress, checkin/checkout (offline/hybrid only)
             limitedSeats, totalSeats, waitlistApplicable, waitlistTriggerCount, description

Section 12 — Advanced
             meta (JSON textarea)
```

**Pain points:**
- 30+ fields across 12 sections, most with conditional dependencies
- Admin must know which fields matter for their program type
- No guardrails — an admin can submit with missing fees, wrong dates, or no form questions
- Zero validation until the publish button is pressed

---

### Stage B — Form Building (Template Selection + Customisation)

After creating program meta, admin navigates to the Form Builder separately:

```
1. Open Form Builder for the created program
2. Choose a template (HDB / MSD / TAT / CUSTOM)
3. Template pre-loads a default question set per section
4. Admin reviews sections: adds, removes, or reorders questions
5. Admin can add new custom questions (type, label, options, required flag)
6. Admin saves the form
```

**Pain points:**
- Separate screen from program meta — admin must context-switch
- Admin must know which template matches their program type
- Question selection is fully manual — no recommendations
- No check that the form is consistent with the program type's standard

---

### Stage C — Review & Publish

```
1. Admin revisits program listing
2. Verifies meta looks correct
3. Verifies form questions are attached
4. Manually checks dates, mode, fee
5. Clicks Publish → status → PUBLISHED
```

**Pain points:**
- Validation is post-hoc — problems are discovered only after seekers try to register
- No system check that form + meta are consistent with each other

---

## 3. What the Agent Automates

The agent collapses all three stages into **one conversation**:

```
Admin types one prompt
        │
        ▼
Agent parses intent → extracts all resolvable fields
        │
        ▼
Agent identifies gaps → asks only the missing required questions
        │
        ▼
Admin answers (multi-turn, full context maintained)
        │
        ▼
Agent assembles CreateProgramDto
        │
        ▼
Agent shows PROGRAM PREVIEW → Admin confirms
        │
        ▼
Program created in DB (status: DRAFT)
        │
        ▼
Agent loads template questions for the program type
        │
        ▼
Agent shows FORM PREVIEW → Admin can add/remove questions
        │
        ▼
Form questions attached to program
        │
        ▼
Agent runs pre-publish validation
        │
        ▼
Admin types "publish" → status → PUBLISHED
```

**Admin experience:** One chat window. Two confirmations (program + form). Done in under 5 minutes.

---

## 4. Predefined Rules the Agent Must Enforce

These rules are derived directly from the CUSTOM program type spec. The agent must apply all of them when assembling or validating a `CreateProgramDto`.

### 4.1 Visibility Rules (Conditional Field Logic)

| Field(s) | Shown Only When |
|---|---|
| `onlineType` | `modeOfProgram` = ONLINE or HYBRID |
| `venue`, `venueNameInEmail`, `isResidenceRequired` | `modeOfProgram` = OFFLINE or HYBRID |
| `totalBedCount` | `isResidenceRequired` = yes AND mode = OFFLINE or HYBRID |
| `blessEndsAt` | `approvalRequired` = yes |
| `noOfSession` | `programStructure` = Sessions |
| `checkinAt`, `checkinEndsAt`, `checkoutAt`, `checkoutEndsAt` | `hasCheckinCheckout` = yes |
| `totalSeats`, `waitlistApplicable` | `hasSeatLimit` = yes |
| `waitlistTriggerCount` | `waitlistApplicable` = yes |
| Payment & Billing section (all fields) | `requiresPayment` = yes |
| Grouped Sub-Programs section | `programStructure` = Programs |
| Sessions section | `programStructure` = Sessions |

### 4.2 Forced / Disabled Rules

| Field | Rule |
|---|---|
| `isTravelInvolved` | **Forced to `false`** when `modeOfProgram` = ONLINE. Agent must set this field to false and must not ask admin about it. |
| `currency` | **Always `INR`**. Agent must not ask. |
| `gstPercentage` | **Auto-calculated** as `cgst + sgst`. Agent must derive this, not ask for it separately. |

### 4.3 Validation Rules

| Rule | Condition | Error |
|---|---|---|
| `programName` required | Always | Must be provided |
| `modeOfProgram` required | Always | Must be ONLINE / OFFLINE / HYBRID |
| `programStructure` required | Always | Must be Single / Sessions / Programs |
| At least 1 session | `programStructure` = Sessions | `NO_SESSIONS` |
| At least 1 sub-program | `programStructure` = Programs | `NO_SUB_PROGRAMS` |
| Session count must match | `noOfSession` declared vs. actual session entries | `SESSION_COUNT_MISMATCH` |
| Sub-program count must match | `noOfSubPrograms` declared vs. actual sub-program entries | `SUB_PROGRAM_COUNT_MISMATCH` |
| Dates must be logically ordered | `startsAt` < `endsAt`, `registrationStartsAt` < `registrationEndsAt` < `startsAt` | Date ordering error |
| Form must not be empty | At publish time | Program must have at least one question attached |
| Workflow must be assigned | At publish time | Workflow must match approval + payment configuration |

### 4.4 Parent-Child Sync Rules

When `programStructure` = Sessions or Programs, child entities inherit from the parent:

| Child Field | Inherits From |
|---|---|
| `modeOfOperation` | Parent `modeOfOperation` |
| Online details (meetingLink etc.) | Parent online config |
| Venue details | Parent venue config |
| Seat configuration | Parent seat config (can be overridden per child) |
| Code | Auto-generated as `<parentCode>_S1`, `<parentCode>_S2`, etc. |

### 4.5 Cleanup Rules (Fields Auto-Cleared)

When a conditional parent field is turned off, the agent must clear (null/false) its dependent children before submitting the DTO:

| Cleared When | Fields Cleared |
|---|---|
| `modeOfProgram` → ONLINE | `venue`, `venueNameInEmail`, `isResidenceRequired`, `totalBedCount` |
| `modeOfProgram` → ONLINE | `isTravelInvolved` → forced false |
| `requiresPayment` → no | All Payment & Billing fields |
| `hasSeatLimit` → no | `totalSeats`, `waitlistApplicable`, `waitlistTriggerCount` |
| `waitlistApplicable` → no | `waitlistTriggerCount` |
| `hasCheckinCheckout` → no | `checkinAt`, `checkinEndsAt`, `checkoutAt`, `checkoutEndsAt` |
| `isResidenceRequired` → no | `totalBedCount` |

---

## 5. How the Custom Template Pattern Works

Templates define the **default form question set** for each program type. This is the same pattern used by HDB, MSD, TAT, and CUSTOM types.

### 5.1 Template Data Model

```
ProgramTemplate
  ├── id
  ├── programTypeId          → links to program type (HDB / MSD / TAT / CUSTOM)
  ├── name
  └── TemplateQuestion[]
        ├── questionId       → points to a Question record
        ├── formSectionId    → which section this question belongs to
        ├── displayOrder     → order within section
        ├── isRequired       → required flag
        └── bindingKey       → DTO field it maps to (e.g. fullName, dob, city)
```

### 5.2 How the Agent Uses Templates

```
1. Admin confirms program type (e.g. HDB)
2. Agent calls getProgramTemplates(typeId=HDB)
3. Returns programTemplateId for that type
4. Agent loads TemplateQuestion[] for that template
5. Groups questions by FormSection
6. Presents grouped form preview to admin
7. Admin approves (or requests edits)
8. Agent calls addQuestionsFromTemplate(programId, templateId)
9. Inserts ProgramQuestion records with displayOrder, formSectionId, registrationLevel=PROGRAM
```

### 5.3 CUSTOM Type Template Default Question Set

When program type = CUSTOM and no standard template applies, the agent uses this default set:

| Section | Question | Required | Binding Key |
|---|---|---|---|
| Personal Details | Full Name | Yes | `fullName` |
| Personal Details | Date of Birth | Yes | `dob` |
| Personal Details | Gender | Yes | `gender` |
| Personal Details | Mobile Number | Yes | `mobileNumber` |
| Personal Details | Email Address | Yes | `emailAddress` |
| Personal Details | City | Yes | `city` |
| Program History | Last Program Attended | No | — |
| Preferences | Preferred Session | No | — |

Admin can add fields beyond this default set in the form preview step.

---

## 6. Adding New Form Fields to the Agent's Knowledge

The agent's understanding of available form fields is driven by the field spec. When the admin wants to add a custom question not in the template, the agent supports this through a structured add-field flow:

### 6.1 Admin Request Pattern

```
Admin: "Add a question asking if the seeker has attended before — dropdown Yes/No"
```

### 6.2 Agent Resolution

The agent maps this to a `CreateProgramQuestionDto`:

```json
{
  "questionText": "Have you attended this program before?",
  "questionType": "select",
  "options": ["Yes", "No"],
  "isRequired": false,
  "formSectionId": "<id of existing or new section>",
  "displayOrder": <next available order>,
  "registrationLevel": "PROGRAM"
}
```

### 6.3 Supported Question Types for New Fields

| Type | When to Use |
|---|---|
| `text` | Short open-ended text |
| `textarea` | Long open-ended text |
| `number` | Numeric answers |
| `radio` | Mutually exclusive choice (Yes/No, small option set) |
| `select` | Dropdown from fixed list |
| `creatableSelect` | Multi-tag input with free-form entry |
| `date` | Date only |
| `datetime` | Date + time |
| `email` | Email format input |
| `imageUpload` | File upload returning a URL |

### 6.4 Extending the Agent's Field Knowledge

To teach the agent about a new form field (e.g. a new section or a new question type added to the system):

1. Add the field entry to the relevant section in `AI_AGENT_custom-program-type-product-spec.md`
2. Add the field's conditional logic (if any) to the `Conditional Logic — Quick Reference` table
3. Add any validation rule to the `Validation Rules` table
4. Update the agent's system prompt to include the new field name, DTO key, type, and any `visibleWhen` / `disabledWhen` conditions
5. If the field is part of a standard template, add it to the `TemplateQuestion[]` records for that program type in the database

The agent reads its field knowledge from the system prompt at runtime — adding a field to the spec and mirroring it in the prompt is sufficient to make the agent aware of it.

---

## 7. Agent Prompt Structure

### 7.1 System Prompt (what the agent always knows)

```
You are the Infinitheism Program Configuration Agent.

Your job is to help admins create, form-build, and publish programs through conversation.

RULES YOU MUST ALWAYS FOLLOW:
1. Never write to the database without admin confirmation
2. Always show a preview (program config + form questions) before any create/update call
3. Apply all conditional field rules before assembling the DTO (visibility, disabled, cleanup)
4. Validate dates are logically ordered before showing the program preview
5. Block publish if: form is empty, workflow is unassigned, or required fields are missing
6. isTravelInvolved is always false when modeOfProgram = ONLINE — do not ask admin
7. currency is always INR — do not ask admin
8. gstPercentage = cgst + sgst — compute it, do not ask admin

FIELD RULES:
[Full field list with DTO keys, types, required flags, and conditional logic
 — mirrors the field spec in AI_AGENT_custom-program-type-product-spec.md]

TEMPLATES:
[Program type → template ID mapping]
[Template → default question set with sections, order, required flags, binding keys]
```

### 7.2 Extraction Prompt (per admin message)

```
Parse this admin message and extract program configuration fields.
Return a JSON object with every field you can confidently extract.
For fields you cannot extract, return null.
Do not guess or infer fields the admin did not mention.

Admin message: "{admin_input}"

Known fields:
[Full list of DTO field names with expected types]
```

### 7.3 Clarification Prompt

```
Given the partial program config below, identify all required fields
that are still null. Return a short, numbered list of questions to ask
the admin. Ask only what is genuinely required — do not ask about
optional fields or fields with valid defaults.

Current config: {partial_dto_json}
Required fields: [list]
```

### 7.4 Preview Prompt

```
Format the following CreateProgramDto as a human-readable program preview.
Use a table or structured layout. Include only fields that have non-null values.
Group by section. End with: "Shall I create this program? (yes / edit)"

DTO: {assembled_dto_json}
```

---

## 8. Agent State Machine

The agent tracks a `stage` field in the session context to manage conversation flow:

```
COLLECTING
    │ all required fields resolved
    ▼
PROGRAM_PREVIEW
    │ admin says "yes"
    ▼
PROGRAM_CREATED (status: DRAFT)
    │
    ▼
FORM_PREVIEW
    │ admin says "ok" or "approve"
    ▼
FORM_ATTACHED
    │
    ▼
VALIDATION
    │ all checks pass
    ▼
READY_TO_PUBLISH
    │ admin says "publish"
    ▼
PUBLISHED
```

If admin says "edit" at any preview stage, the agent returns to `COLLECTING` with the current DTO as context.

---

## 9. API Contract

```
POST /v1/program-config-agent/chat

Request:
{
  "sessionId": "uuid",
  "message": "string",
  "confirm": true | false | null
}

Response:
{
  "success": true,
  "data": {
    "reply": "string",
    "stage": "COLLECTING | PROGRAM_PREVIEW | FORM_PREVIEW | READY_TO_PUBLISH | PUBLISHED",
    "dtoPreview": CreateProgramDto | null,
    "formPreview": ProgramQuestionDto[] | null,
    "requiresConfirmation": true | false,
    "programId": number | null
  }
}
```

---

## 10. Implementation Phases

### Phase 1 — Program Meta Automation

- Agent parses admin prompt and extracts `CreateProgramDto` fields
- Multi-turn clarification for missing required fields
- Program preview → admin confirms → program created (DRAFT)
- Enforces all conditional field rules and cleanup rules

**Done when:** Admin can describe a program in plain language and get a DRAFT program created in under 3 turns.

---

### Phase 2 — Form Building via Templates

- Agent fetches template for the program type
- Presents grouped form preview
- Admin can add/remove questions via conversation
- Form questions attached via `addQuestionsFromTemplate`

**Done when:** Form is attached without admin opening the form builder UI.

---

### Phase 3 — Pre-Publish Validation & Publish

- Agent runs full validation: dates, form not empty, workflow assigned
- Admin types "publish" → `updateStatus(PUBLISHED)`

**Done when:** Agent blocks publishing of misconfigured programs and publishes correct ones in one turn.

---

### Phase 4 — New Field Support

- New form fields added to spec and mirrored in agent system prompt
- No code change needed — field knowledge is prompt-driven
- DB changes needed only if a new question type is added to the question library

---

## 11. Success Criteria

| Outcome | Measure |
|---|---|
| Admin time from first message to PUBLISHED program | Under 5 minutes |
| Misconfigured programs reaching seekers | Zero |
| Admin screens visited during program creation | Zero (chat only) |
| Question consistency for same program type | 100% (template enforced) |
| Programs published with form attached | 100% (agent blocks publish without form) |
| New form field onboarding effort | Update spec + system prompt only |

---

## 12. Relationship to Existing Documents

| Document | Role |
|---|---|
| `AI_AGENT_PROGRAM_CONFIG_VISION.md` | High-level vision: the two journeys (admin + seeker) |
| `AI_AGENT_PROGRAM_CONFIG_SPEC.md` | Technical flow: step-by-step execution and API spec |
| `AI_AGENT_custom-program-type-product-spec.md` | Field authority: all fields, types, conditions, validation rules |
| `AI_AGENT_PROGRAM_CONFIG_API_USAGE.md` | API endpoints the agent calls in the downstream NestJS service |
| **This document** | Automation vision: rules, template pattern, prompt structure, state machine, extensibility |

The CUSTOM program type spec (`AI_AGENT_custom-program-type-product-spec.md`) is the **single source of truth** for all field rules. When in doubt, that document governs. This document explains how the agent uses those rules.
