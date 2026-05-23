# PROGRAM-CONFIG PRD

This PRD covers the PROGRAM-CONFIG module of the AI Platform, which implements the conversational program configuration agent for Infinitheism admins. It translates the client-onboarding context (`docs/client-context.md`) directly into product behavior — skipping BRD and roadmap stages because this is a small weight-class project. The agent replaces the existing multi-screen, 30+ field form wizard with a single chat session: the admin describes what they want, the agent collects what is missing, shows previews, and publishes on confirmation. Audience: admin-side developers, PTL (Madhuri Karedla), and any client sign-off reviewer.

---

What does PROGRAM-CONFIG do, and what is still undecided?

<details><summary>Graph: What does PROGRAM-CONFIG do, and what is still undecided?</summary>

```items
---
id: prd-cognition
title: PROGRAM-CONFIG PRD cognition
default_open_depth: 1
default_color_by: kind
color_palette_source: .daksh/color-palette.json
width: 95vw
---

Users:
  - user-01 :: Infinitheism Admin | kind: User | role: Program Administrator | audience: end_customer | status: placeholder | summary: Configures and publishes programs for Infinitheism via the AI agent | spec: [§User Types](client-context.md#user-types)
  - user-02 :: Seeker | kind: User | role: Spiritual Participant | audience: end_customer | status: placeholder | summary: Registers for programs through forms built by the admin | spec: [§User Types](client-context.md#user-types)
  - user-03 :: Madhuri Karedla / PTL | kind: User | role: PTL | audience: delivery | status: validated | summary: Project Technical Lead accountable for agent implementation and NestJS integration | spec: [§User Types](client-context.md#user-types)

Goals:
  - goal-01 :: Admin configures program in under 5 min | kind: Goal | success_measure: Admin time from first message to published program under 5 minutes, measured in pilot sessions | summary: Any admin can configure and publish a complete program in under 5 minutes via a single chat session | spec: [§Product Summary](client-context.md#product-summary)
  - goal-02 :: Zero misconfigured programs reach seekers | kind: Goal | success_measure: Zero programs published with missing required fields or inconsistent configuration | summary: The agent validates all required fields and blocks publish until configuration is complete and consistent | spec: [§Product Summary](client-context.md#product-summary)
  - goal-03 :: Seeker frictionless registration | kind: Goal | success_measure: Seeker form completion rate higher than pre-agent baseline | summary: Seekers see a complete, pre-filled registration form and can submit in under 3 minutes | spec: [§User Types](client-context.md#user-types)
  - goal-04 :: Template question consistency | kind: Goal | success_measure: 100% of agent-configured programs use questions matching their type template | summary: The agent enforces template-based question sets so all programs of the same type have consistent forms | spec: [§Product Summary](client-context.md#product-summary)

Admin Flows:
  - flow-03 :: Collect Program Fields | kind: Flow | actor: Admin | trigger: Admin sends first message describing a program | outcome: All required CreateProgramDto fields extracted or confirmed | summary: Multi-turn extraction loop where agent identifies missing fields and asks for them one group at a time | spec: [§User Stories](prd.md#user-stories)
  - flow-04 :: Template Selection | kind: Flow | actor: Admin | trigger: Agent reaches TEMPLATE_SELECTION state | outcome: Admin confirms which program type template to use for form questions | summary: Agent loads available templates for the program type and presents options to the admin | spec: [§User Stories](prd.md#user-stories)
  - flow-05 :: Program Preview and Confirm | kind: Flow | actor: Admin | trigger: All required fields collected | outcome: Admin approves and program is created as DRAFT in the database | summary: Agent assembles CreateProgramDto, shows a tabular preview, and waits for admin confirmation before calling POST /program | spec: [§User Stories](prd.md#user-stories)
  - flow-06 :: Form Attach | kind: Flow | actor: Admin | trigger: Program created as DRAFT | outcome: Template questions attached to program, grouped by form section | summary: Agent loads template questions, shows a section-by-section preview, and calls POST /program-question on admin confirmation | spec: [§User Stories](prd.md#user-stories)
  - flow-07 :: Validate and Publish | kind: Flow | actor: Admin | trigger: Admin says publish | outcome: Program status set to PUBLISHED | summary: Agent runs pre-publish validation (dates valid, form not empty, workflow assigned), then calls PUT /program/:id/status with accessType uppercase | spec: [§Business Rules](prd.md#business-rules)

Seeker Flows:
  - flow-08 :: Seeker Pre-fill | kind: Flow | actor: Seeker | trigger: Seeker opens a published program registration form | outcome: Personal fields pre-populated from prior registration history | summary: System reads seeker's previous registration data and pre-fills matching fields so the seeker only fills program-specific questions | spec: [§User Stories](prd.md#user-stories)
  - flow-09 :: Registration Submit | kind: Flow | actor: Seeker | trigger: Seeker completes and submits the pre-filled form | outcome: Registration record created with initial status | summary: Seeker form submitted; registration created in PENDING_APPROVAL or equivalent initial state per program workflow | spec: [§User Stories](prd.md#user-stories)
  - flow-10 :: Registration Confirmation | kind: Flow | actor: Seeker | trigger: Registration submitted | outcome: Seeker sees confirmation with registration ID and next steps | summary: Seeker receives immediate confirmation with their registration ID, status, and what happens next (email/WhatsApp notification on approval) | spec: [§User Stories](prd.md#user-stories)

Decisions:
  - dec-01 :: Conversational interface over enhanced form | kind: Decision | alternatives: (1) Improve the existing form UI with autofill and smart validation; (2) Add an AI sidebar assistant to the existing form wizard; (3) Full conversational replacement — this option chosen | reversal_trigger: Pilot shows fewer than half of admins complete the configuration end-to-end via chat without falling back to the form | summary: Admins configure programs via free-text chat rather than any variant of the multi-screen form | spec: [§Decisions](prd.md#decisions)
  - dec-02 :: Preview-before-create at every stage | kind: Decision | alternatives: (1) Direct create with an undo operation; (2) Optimistic write to draft with explicit confirmation before publish only | reversal_trigger: Admins report the preview step adds friction without a measurable reduction in misconfiguration errors | summary: Nothing is written to the database until the admin sees and explicitly approves a full preview at the program stage and again at the form stage | spec: [§Decisions](prd.md#decisions)
  - dec-03 :: Agent integrates via NestJS API, not direct DB | kind: Decision | alternatives: (1) Agent writes directly to the database, bypassing NestJS; (2) Agent wraps a new microservice with its own data layer | reversal_trigger: NestJS API contracts become incompatible with what the agent needs and renegotiation is not possible | summary: The agent calls existing NestJS endpoints for all program operations, keeping every business rule in the authoritative service layer | spec: [§Decisions](prd.md#decisions)
  - dec-04 :: Template-based question recommendation | kind: Decision | alternatives: (1) Present the full question library for manual selection; (2) AI-recommend questions from the full library without templates | reversal_trigger: Admins consistently report the template is missing questions they need and manual overrides exceed 50% of sessions | summary: Agent recommends form questions from a per-program-type template rather than letting admins select from the full question library | spec: [§Decisions](prd.md#decisions)

Open Questions:
  - oq-01 :: Will admins adopt the chat interface? | kind: OpenQuestion | summary: Whether Infinitheism admins will prefer the conversational flow over the existing form wizard once both are available | spec: [§Open Questions](prd.md#open-questions)
  - oq-02 :: Which seeker profile fields to pre-fill? | kind: OpenQuestion | summary: Which fields from a seeker's prior registrations should be pre-populated and in what priority order | spec: [§Open Questions](prd.md#open-questions)
  - oq-03 :: How to handle custom program types without templates? | kind: OpenQuestion | summary: How the agent behaves when an admin configures a program type that has no existing question template | spec: [§Open Questions](prd.md#open-questions)
  - oq-04 :: What admin onboarding is needed for chat adoption? | kind: OpenQuestion | summary: Whether admins need onboarding sessions, documentation, or in-chat tooltips to use the agent productively from day one | spec: [§Open Questions](prd.md#open-questions)

Constraints:
  - constraint-01 :: NestJS API is the only write path | kind: Constraint | summary: The agent must call NestJS backend endpoints for all create/update/publish operations — direct DB access is forbidden | spec: [§Scope](prd.md#scope)
  - constraint-02 :: accessType must be uppercase enum | kind: Constraint | summary: The publish API requires accessType as PUBLIC, INTERNAL, or RESTRICTED in uppercase — lowercase causes a 400 from the NestJS backend | spec: [§Business Rules](prd.md#business-rules)
  - constraint-03 :: Seeker registration flow is unchanged | kind: Constraint | summary: The agent's scope ends at program PUBLISHED status — seeker registration, approval workflows, and waitlist management are out of scope | spec: [§Scope](prd.md#scope)
  - constraint-04 :: gstPercentage is auto-calculated (agent never asks for it) | kind: Constraint | summary: gstPercentage is always computed as cgst + sgst — the agent never prompts the admin to enter gstPercentage directly | spec: [§Business Rules](prd.md#business-rules)

- risk-01 :: Admin adoption failure | kind: Risk | likelihood: medium | impact: high | mitigation: Run pilot sessions with real admins before full rollout; measure chat completion rate vs. fallback to form | phase: design | summary: Admins may not adopt the conversational interface and fall back to the form wizard, leaving the agent unused in production | spec: [§Risks](prd.md#risks)
- risk-02 :: NestJS API contract change | kind: Risk | likelihood: low | impact: high | mitigation: Pin API contract versions; establish a change notification protocol with the NestJS team before development begins | phase: design | summary: Mid-development changes to NestJS API contracts could silently break the agent's integration layer | spec: [§Risks](prd.md#risks)
- milestone-01 :: PROGRAM-CONFIG shipped | kind: Milestone | due: end of sprint | definition_of_done: All user stories AC-PC-001 through AC-PC-009 pass in staging; at least one real admin pilot session completed successfully | summary: Admin can configure and publish any HDB, MSD, TAT, or custom program via chat, and seekers see pre-filled registration forms | spec: [§Acceptance Criteria](prd.md#acceptance-criteria)

user-01 -> flow-03 | relation: experiences
user-02 -> flow-08 | relation: experiences
user-03 -> milestone-01 | relation: owns
flow-03 -> flow-04 | relation: enables
flow-04 -> flow-05 | relation: enables
flow-05 -> flow-06 | relation: enables
flow-06 -> flow-07 | relation: enables
flow-07 -> goal-02 | relation: serves
flow-03 -> goal-01 | relation: serves
flow-08 -> goal-03 | relation: serves
dec-04 -> goal-04 | relation: serves
dec-01 -> goal-01 | relation: serves
dec-02 -> goal-02 | relation: serves
constraint-01 -> component-01 | relation: governs
constraint-02 -> flow-07 | relation: governs
constraint-03 -> flow-07 | relation: governs
oq-01 -> dec-01 | relation: threatens
oq-02 -> goal-03 | relation: threatens
oq-03 -> dec-04 | relation: threatens
oq-04 -> goal-01 | relation: threatens
risk-01 -> goal-01 | relation: threatens
risk-02 -> component-01 | relation: threatens
milestone-01 -> goal-01 | relation: serves
milestone-01 -> goal-02 | relation: serves
milestone-01 -> goal-03 | relation: serves
```

</details>

---

## Scope

**In scope:**

- Conversational program configuration for Infinitheism admins (HDB, MSD, TAT, CUSTOM program types)
- Multi-turn field extraction with targeted clarifying questions
- Program preview before any database write
- Template-based form question recommendation and form attachment
- Pre-publish validation and one-step publish via NestJS API
- Seeker pre-fill from prior registration history

**Out of scope:**

- Seeker registration, approval workflows, and waitlist management (these remain in the existing NestJS/frontend stack)
- Direct database writes from the agent (all writes go through NestJS APIs)
- Payment processing and GST calculation (the agent captures fee metadata; payment processing lives in NestJS)
- Program analytics, reporting, or post-publish editing

The explicit scope boundary is: **the agent's responsibility ends when `PUT /program/:id/status` returns a PUBLISHED status**. Everything after that — seeker discovery, registration, approval, notification — is outside this module.

---

## Decisions

The decisions below are binding for this sprint. The reversal trigger for each defines when this decision should be revisited.

**dec-01 — Conversational interface over enhanced form**
Admins configure programs via free-text chat rather than any variant of the multi-screen form. This is a project-level decision inherited from the client-onboarding context. Reversal trigger: pilot shows fewer than half of admins complete configuration end-to-end via chat without falling back to the form wizard.

**dec-02 — Preview-before-create at every stage**
Nothing is written to the database until the admin sees and explicitly approves a full preview — once at the program stage and again at the form stage. The agent never calls POST /program or POST /program-question optimistically. Reversal trigger: admins report the preview step adds friction without a measurable reduction in misconfiguration errors.

**dec-03 — Agent integrates via NestJS API, not direct DB**
The agent calls existing NestJS endpoints for all program operations. This keeps every business rule in the authoritative service layer and avoids duplicating NestJS validation logic. Reversal trigger: NestJS API contracts become incompatible with what the agent needs and renegotiation is not possible.

**dec-04 — Template-based question recommendation**
The agent recommends form questions from a per-program-type template rather than letting admins select questions manually from the full library. This enforces consistency across programs of the same type. Reversal trigger: admins consistently report the template is missing questions they need and manual overrides exceed 50% of sessions.

---

## User Stories

All stories trace to the client vision document (`docs/client-context.md`) — this project skips BRD and roadmap stages per small weight-class rules.

**US-PC-001** — As an admin, I want to describe a program in plain language so that the agent collects all required details via targeted clarifying questions, without me filling any form.

**US-PC-002** — As an admin, I want to see a complete program preview before anything is written to the database so that I can verify every field before committing.

**US-PC-003** — As an admin, I want to edit specific fields in the preview without restarting the session so that I don't lose my prior answers.

**US-PC-004** — As an admin, I want the agent to recommend form questions from my program type's template so that I don't have to select questions manually from a library.

**US-PC-005** — As an admin, I want to review the recommended form questions and optionally add, remove, or reorder them before they are attached so that the form matches my program's needs.

**US-PC-006** — As an admin, I want the agent to block publish if the configuration is incomplete or the form is empty so that seekers never see a broken program.

**US-PC-007** — As an admin, I want to publish the program in a single confirmation step so that it becomes live for seekers immediately.

**US-PC-008** — As a seeker, I want my name, mobile, city, and email pre-filled from my previous registration so that I only fill program-specific questions.

**US-PC-009** — As an admin, I want the agent to remember everything I've said in the current session so that I never have to repeat information.

---

## Business Rules

These rules are invariants — the agent must enforce them without exception. Rules marked **[NestJS-enforced]** are also validated by the NestJS backend; the agent must enforce them independently to prevent wasted API calls and confusing error messages.

**BR-PC-001** — The agent extracts program type from natural language. Supported types: HDB, MSD, TAT, CUSTOM. If the admin uses a name not in this list, the agent asks for clarification before proceeding.

**BR-PC-002** — `isTravelInvolved` is forced to `false` when `modeOfOperation = ONLINE`. Admin cannot override this. The agent sets the value silently and notes it in the preview.

**BR-PC-003** — `gstPercentage` is always computed as `cgst + sgst`. The agent never asks the admin for `gstPercentage` directly. If `requiresPayment = false`, all GST fields default to 0.

**BR-PC-004** — Program code must be unique. The agent validates via `GET /program/check-code?code=:code` before confirming the preview. If the code is not unique, the agent notifies the admin and suggests an alternative.

**BR-PC-005** — `accessType` sent to NestJS must be uppercase: `PUBLIC`, `INTERNAL`, or `RESTRICTED`. Lowercase values cause a 400 response. This was a prior production bug; the agent must coerce any admin input to uppercase before calling the API. [NestJS-enforced]

**BR-PC-006** — The agent only asks for fields that are missing or unconfirmed. It never re-asks for a field the admin has already provided in the current session, even across many turns.

**BR-PC-007** — Conditional fields are asked only when relevant:
- `onlineType` is asked only if `modeOfOperation = ONLINE` or `HYBRID`
- Venue fields (`venue`, `city`, `address`) are asked only if `modeOfOperation = OFFLINE` or `HYBRID`
- Payment fields (`fee`, `cgst`, `sgst`, `paymentDeadline`) are asked only if `requiresPayment = true`
- `blessEndsAt` is asked only if `approvalRequired = true`

**BR-PC-008** — A program cannot be published if the attached form has zero questions. The agent blocks the publish step, explains which check failed, and prompts the admin to attach a form before retrying.

**BR-PC-009** — Template questions are grouped by `FormSection`. Section order and question `displayOrder` within sections must be preserved from the template. Admins may add, remove, or reorder questions but not change section membership.

**BR-PC-010** — The agent must validate all required fields before calling `POST /program`. Minimum required: `name`, `modeOfOperation`, `programStructure`, `typeId`. Missing any of these blocks the PROGRAM_PREVIEW transition.

---

## Acceptance Criteria

Each AC is written in Given/When/Then format and traces to a user story.

**AC-PC-001** (for US-PC-001):
Given an admin sends "Create an HDB, 5 days, online, June 15, 100 seats", when the agent processes the message, then it extracts `type=HDB`, `mode=ONLINE`, `startsAt`, `duration`, and `seats` and asks only for the fields still missing (registration close date, email sender name).

**AC-PC-002** (for US-PC-002):
Given all required fields are collected, when the agent transitions to PROGRAM_PREVIEW, then it renders a tabular preview of all fields before calling any write API.

**AC-PC-003** (for US-PC-003):
Given the admin says "change the fee to 3000" during preview, when the agent processes the edit request, then it updates only the fee field, re-validates, and re-shows the full preview without losing other field values.

**AC-PC-004** (for US-PC-004):
Given the program is created as DRAFT, when the agent transitions to TEMPLATE_SELECTION, then it calls `GET /v1/program-templates/program-type/:typeId` and presents the available question set grouped by section.

**AC-PC-005** (for US-PC-005):
Given the agent shows the template question set, when the admin says "remove the roommate preference question", then the agent removes that question from the pending set and re-shows the updated list before calling `POST /program-question`.

**AC-PC-006** (for US-PC-006):
Given the admin says "publish" but the form has zero questions, when the agent runs pre-publish validation, then it blocks the publish, explains which check failed, and prompts the admin to attach a form first.

**AC-PC-007** (for US-PC-007):
Given the program has a form attached and all validation checks pass, when the admin says "publish", then the agent calls `PUT /program/:id/status` with `{"status":"PUBLISHED","accessType":"PUBLIC"|"INTERNAL"|"RESTRICTED"}` (uppercase) and confirms the program is live.

**AC-PC-008** (for US-PC-008):
Given a seeker with prior registrations opens a published program, when the registration form renders, then their name, mobile number, city, and email are pre-populated from their most recent registration.

**AC-PC-009** (for US-PC-009):
Given an admin has already said "the fee is 5000 and it requires approval" in message 3, when the agent reaches message 8, then it does not re-ask for fee or approval status.

---

## Data Contract

**Request (consumed by this module):**
```json
{
  "session_id": "string (UUID4, client-generated)",
  "message": "string (admin's plain-language chat message)",
  "user_id": "integer"
}
```

**Response (produced by this module):**
```json
{
  "session_id": "string",
  "reply": "string (agent's response text, rendered in the chat UI)",
  "stage": "COLLECTING | TEMPLATE_SELECTION | PROGRAM_PREVIEW | PROGRAM_CREATED | FORM_PREVIEW | FORM_ATTACHED | READY_TO_PUBLISH | PUBLISHED",
  "requires_confirmation": "boolean",
  "preview_data": "object | null"
}
```

**NestJS APIs consumed:**

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/program` | Create program (camelCase payload, `CreateProgramDto`) |
| POST | `/program-question` | Attach questions to a program |
| POST | `/program/clone-from-template` | Clone template `{programId, programTemplateId}` |
| PUT | `/program/:id/status` | Publish: `{status:"PUBLISHED", updatedBy:int, accessType:"PUBLIC"\|"INTERNAL"\|"RESTRICTED"}` |
| GET | `/v1/program-templates/program-type/:typeId` | List templates by type |
| GET | `/program/check-code?code=:code&excludeId=:id` | Check program code uniqueness |

---

## Risks

**risk-01 — Admin adoption failure**
*Likelihood: medium | Impact: high*
Admins may not adopt the conversational interface and fall back to the form wizard, leaving the agent unused in production. Mitigation: run pilot sessions with 2–3 real admins before full rollout; measure chat completion rate versus fallback rate.

**risk-02 — NestJS API contract change**
*Likelihood: low | Impact: high*
Mid-development changes to NestJS API contracts could silently break the agent's integration layer. Mitigation: pin API contract versions; establish a change-notification protocol with the NestJS team before development begins.

---

## Open Questions

| # | Question | Blocks | Status |
|---|---|---|---|
| OQ-01 | Will admins naturally adopt the chat interface, or will they fall back to the form wizard? | dec-01 (conversational interface) — if false, the design approach needs rethinking | Open |
| OQ-02 | Which seeker profile fields from prior registrations should be pre-filled, and in what priority order? | goal-03 (seeker frictionless registration) | Open |
| OQ-03 | How does the agent handle program types not covered by the existing templates? | dec-04 (template-based recommendation) | Open |
| OQ-04 | What level of admin onboarding (documentation, tooltips, demo) is needed for productive first use? | goal-01 (admin < 5 min) — onboarding overhead affects time-to-value | Open |

---

## Approval

*Weight class: small — 1 approval required per gate.*

Approved by:
Role:
Date:
