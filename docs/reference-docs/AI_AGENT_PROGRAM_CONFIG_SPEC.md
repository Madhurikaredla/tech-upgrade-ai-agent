# AI Agent — Program Configuration & Registration

## Problem Statement

Infinitheism runs spiritual programs (HDB, MSD, TAT, etc.) that require admins to manually configure every detail — program metadata, form questions, session schedules, fees, workflows, capacity — across multiple screens and steps. This is time-consuming, error-prone, and requires deep knowledge of the system.

On the other side, seekers visit the platform, find a program, fill the registration form (which was built by the admin), and submit their registration.

### The Problem

**For Admins:**
Configuring a program today requires an admin to:
1. Fill a long program creation form (30+ fields: dates, mode, fees, capacity, GST, workflows, access type, etc.)
2. Separately go to the form builder and attach questions section by section
3. Manually assign a template or pick questions from a question library
4. Set up sessions if registration is session-level
5. Assign the right workflow for approval/waitlist logic
6. Publish the program only after all of the above is complete

This entire process is **manual, fragmented, and has no guardrails** — an admin can publish a misconfigured program (missing fee, wrong dates, no questions) that breaks the seeker experience.

**For Seekers:**
Once a program is published, a seeker lands on it and must fill a registration form. The form currently shows whatever questions the admin attached. If the admin missed a question, the seeker either can't complete registration or submits incomplete data. The seeker has **no intelligent guidance** — no pre-fill from their profile, no validation hints, no contextual help.

### Core Problem Statement

> **Admins lack an intelligent, conversational way to configure programs end-to-end — from basic details to form design — resulting in slow setup, misconfigured programs, and broken seeker registration experiences.**

| Pain | Who Feels It | Impact |
|------|-------------|--------|
| Multi-step manual program setup across fragmented UI | Admin | Slow, error-prone |
| No validation until publish — misconfiguration discovered late | Admin | Rework, delays |
| Manual question selection with no recommendations | Admin | Inconsistent forms across programs |
| Seeker sees incomplete or irrelevant form questions | Seeker | Drop-offs, failed registrations |
| No pre-fill from seeker's previous registrations | Seeker | Repetitive data entry |
| Admin has no visibility into "is this program ready to publish?" | Admin | Premature or delayed publishing |

---

## Solution Overview

An **AI Agent for Program Configuration** with two outcomes:

1. **Admin** — describes the program conversationally → agent collects all details via clarifying questions → assembles the full program config + form → shows preview → admin confirms → program is created and published
2. **Seeker** — opens the published program → sees a complete, well-structured form → fills and submits registration → flows into the correct workflow

---

## Conversational Flow

```
Admin types first message
        │
        ▼
Agent extracts what it can, asks for missing required fields
        │
        ▼
Admin answers (multi-turn, full chat context maintained throughout)
        │
        ▼
Agent assembles complete program config (CreateProgramDto)
        │
        ▼
Agent shows program preview to admin
        │
        ▼
Admin approves → Program created in DB (status: DRAFT)
        │
        ▼
Agent assembles form (questions, sections, order)
        │
        ▼
Agent shows form preview to admin
        │
        ▼
Admin approves → Form questions attached to program
        │
        ▼
Agent asks: "Ready to publish?"
        │
        ▼
Admin confirms → Program status set to PUBLISHED
        │
        ▼
Seeker opens program → sees form → fills → submits registration
```

---

## Step-by-Step Execution

### Step 1 — Admin Opens Agent Chat

Admin navigates to the AI agent chat panel and types their intent.

**Admin Input:**
```
"Create an HDB program for June 2026, 5 days, online via Zoom,
 max 100 seats, registration opens June 1, requires approval,
 fee ₹5000 + 18% GST, internal access only"
```

**Agent Action:**
- Parses intent using Azure OpenAI (`callOpenAIChatCompletion`)
- Extracts: programType=HDB, mode=ONLINE, onlineType=MEETING, startsAt, maxCapacity, requiresApproval, programFee, gstPercentage, accessType
- Identifies missing required fields: `registrationEndsAt`, `checkinAt`, `venueAddressId` (if offline), `emailSenderName`

**Agent Output:**
```
Got it! Here's what I have so far:

  Program Type  : HDB
  Mode          : Online (Zoom Meeting)
  Starts        : June 15, 2026
  Duration      : 5 days (ends June 20)
  Max Seats     : 100
  Requires Approval: Yes
  Fee           : ₹5,000 + 18% GST
  Access        : Internal

I need a few more details:
  1. When should registration close?
  2. What name should appear on emails sent to seekers?
  3. Should there be a waitlist if seats fill up?
```

---

### Step 2 — Admin Answers Clarifying Questions

**Admin Input:**
```
"Registration closes June 10. Emails from Infinitheism Team.
 Yes, enable waitlist."
```

**Agent Action:**
- Appends answers to running context (full chat history maintained in session)
- Re-evaluates: all required fields now resolved
- Assembles `CreateProgramDto`

**Agent Output:**
```
Perfect. Here's the complete program configuration:

┌─────────────────────────────────────────────────────┐
│  PROGRAM PREVIEW                                    │
├─────────────────────────────────────────────────────┤
│  Name               : HDB June 2026                │
│  Type               : HDB                          │
│  Mode               : Online — Zoom Meeting        │
│  Starts             : June 15, 2026                │
│  Ends               : June 20, 2026                │
│  Registration Open  : June 1 → June 10, 2026       │
│  Max Capacity       : 100 seats                    │
│  Waitlist           : Enabled                      │
│  Requires Approval  : Yes                          │
│  Fee                : ₹5,000 + 18% GST             │
│  Email Sender       : Infinitheism Team            │
│  Access             : Internal                     │
│  Status             : DRAFT                        │
└─────────────────────────────────────────────────────┘

Shall I create this program? (yes / edit)
```

---

### Step 3 — Admin Confirms Program → Program Created

**Admin Input:**
```
"yes"
```

**Agent Action:**
- Calls `program.service.create(dto)`
- Program record inserted into DB with `status: DRAFT`
- Returns `programId`

**Agent Output:**
```
Program created successfully.
  Program ID : 4821
  Status     : DRAFT

Now let's set up the registration form.
I'll suggest questions based on the HDB template.
Shall I load the standard HDB question set? (yes / customise)
```

---

### Step 4 — Agent Recommends Form Questions

**Admin Input:**
```
"yes"
```

**Agent Action:**
- Calls `getProgramTemplates(typeId=HDB)` → fetches `programTemplateId`
- Loads `TemplateQuestion[]` for that template
- Groups by `FormSection`
- Identifies optional vs required questions

**Agent Output:**
```
Here's the form I'll attach to HDB June 2026:

  SECTION 1 — Personal Details
    ✓ Full Name          (required, binds → fullName)
    ✓ Date of Birth      (required, binds → dob)
    ✓ Gender             (required, binds → gender)
    ✓ Mobile Number      (required, binds → mobileNumber)
    ✓ Email Address      (required, binds → emailAddress)
    ✓ City               (required, binds → city)

  SECTION 2 — Program History
    ✓ Last HDB Attended         (optional)
    ✓ HDB Association Since     (optional)
    ✓ Other Infinitheism Contact (optional)

  SECTION 3 — Preferences
    ✓ First Song Preference     (optional)
    ✓ Second Song Preference    (optional)
    ✓ Preferred Roommate        (optional)

  Total: 12 questions across 3 sections

Want to add, remove, or reorder any questions? (ok / edit)
```

---

### Step 5 — Admin Confirms Form → Questions Attached

**Admin Input:**
```
"ok"
```

**Agent Action:**
- Calls `addQuestionsFromTemplate(programId=4821, templateId)`
- Inserts `ProgramQuestion` records with `displayOrder`, `formSectionId`, `registrationLevel=PROGRAM`
- Validates all required questions are present

**Agent Output:**
```
Form attached successfully.
  12 questions added across 3 sections.

Program HDB June 2026 is fully configured.

Ready to publish? Once published, seekers with internal
access can view and register for this program. (publish / keep as draft)
```

---

### Step 6 — Admin Publishes

**Admin Input:**
```
"publish"
```

**Agent Action:**
- Calls `program.service.updateStatus(4821, { status: PUBLISHED })`
- Runs final validation: dates valid, form not empty, workflow assigned

**Agent Output:**
```
HDB June 2026 is now PUBLISHED.

  Program ID   : 4821
  Access       : Internal seekers
  Registration : Opens June 1, 2026
  Seats        : 100 available

Seekers can now find and register for this program.
```

---

### Step 7 — Seeker Registers

**Seeker Action:**
- Opens program listing → finds "HDB June 2026"
- Clicks Register → sees the form built in Steps 4-5
- Fields pre-filled from their previous registrations (name, DOB, mobile, city)
- Fills remaining answers → submits

**System Action:**
- Calls `registration.service.create(CreateRegistrationDto)`
- Validates all answers via `RegistrationAnswerValidationService`
- Since `requiresApproval=true` → status set to `PENDING_APPROVAL`
- Workflow triggers approval notification to admin

**Seeker Sees:**
```
Registration submitted successfully.
Your registration is pending approval.
You will receive a confirmation on madhuri@example.com
once approved.

  Registration ID : HDB26-001
  Program         : HDB June 2026
  Status          : Pending Approval
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Admin time: describe → published program | Under 5 minutes |
| Misconfigured programs reaching seekers | Zero (agent validates before publish) |
| Seeker form completion rate | Improved (consistent, well-structured forms) |
| Form question coverage consistency | Same question set for same program type |

---

## Technical Execution Plan

### Phase 1 — Module Scaffold

- Create `src/program-config-agent/` module
- Wire Azure OpenAI client (reuse from `ai-communication`)
- Implement session/context store (Redis-backed chat history)
- Define `AgentChatDto`, `AgentResponseDto`

### Phase 2 — Tools

| Tool | Calls |
|------|-------|
| `getProgramTypes` | `program-type` repository |
| `getProgramTemplates` | `program-template` repository |
| `getWorkflows` | `workflow-configuration` repository |
| `validateProgramConfig` | `program-validation.service` |
| `createProgram` | `program.service.create()` |
| `addQuestionsFromTemplate` | `program-question` service |
| `publishProgram` | `program.service.updateStatus()` |

### Phase 3 — Prompts

- System prompt: defines agent role, rules, output format
- Extraction prompt: parse natural language → program fields
- Clarification prompt: identify missing required fields → ask targeted questions
- Preview prompt: format assembled DTO into human-readable summary
- Form recommendation prompt: suggest questions based on program type

### Phase 4 — API

```
POST /v1/program-config-agent/chat
Body  : { sessionId: string, message: string, confirm?: boolean }
Response: {
  success: true,
  data: {
    reply: string,
    dtoPreview?: CreateProgramDto | ProgramQuestionDto[],
    requiresConfirmation: boolean,
    stage: 'COLLECTING' | 'PROGRAM_PREVIEW' | 'FORM_PREVIEW' | 'PUBLISHED',
    programId?: number
  }
}
```

### Phase 5 — Seeker Side (no change needed)

Existing `registration.service.create()` and form rendering work unchanged — the agent simply ensures the program and questions are correctly configured before publish.
