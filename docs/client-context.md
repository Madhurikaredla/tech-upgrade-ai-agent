# Discovery Context

The Infinitheism admin portal today requires admins to navigate four separate screens and fill over thirty fields manually to configure and publish a single program. This project replaces that fragmented flow with a single conversational agent: an admin describes what they want, the agent collects what it needs, shows a preview at each stage, and publishes on confirmation. The work is greenfield on top of an existing NestJS backend — the agent integrates with existing services rather than replacing them. The engagement scope is intentionally narrow: one module, one sprint, one agent, defined precisely before building begins.

---

Who is this for, what do they need, and what do we not yet know?

<details><summary>Graph: Who is this for, what do they need, and what do we not yet know?</summary>

```items
---
id: 00-cognition
title: Discovery Context cognition
default_open_depth: 1
default_color_by: kind
color_palette_source: .daksh/color-palette.json
width: 95vw
---

Users:
  - user-01 :: Infinitheism Admin | kind: User | role: Program Administrator | audience: end_customer | status: placeholder | summary: Configures and publishes programs for Infinitheism via the AI agent | spec: [§User Types](client-context.md#user-types)
  - user-02 :: Seeker | kind: User | role: Spiritual Participant | audience: end_customer | status: placeholder | summary: Registers for programs through forms built by the admin | spec: [§User Types](client-context.md#user-types)
  - user-03 :: Madhuri Karedla | kind: User | role: PTL | audience: delivery | status: validated | summary: Project Technical Lead accountable for agent implementation and NestJS integration | spec: [§User Types](client-context.md#user-types)

Goals:
  - goal-01 :: Admin configures program in under 5 min | kind: Goal | success_measure: Admin time from first message to published program under 5 minutes, measured in pilot sessions | summary: Any admin can configure and publish a complete program in under 5 minutes via a single chat session | spec: [§Product Summary](client-context.md#product-summary)
  - goal-02 :: Zero misconfigured programs reach seekers | kind: Goal | success_measure: Zero programs published with missing required fields or inconsistent configuration | summary: The agent validates all required fields and blocks publish until configuration is complete and consistent | spec: [§Product Summary](client-context.md#product-summary)
  - goal-03 :: Seeker frictionless registration | kind: Goal | success_measure: Seeker form completion rate higher than pre-agent baseline | summary: Seekers see a complete, pre-filled registration form and can submit in under 3 minutes | spec: [§User Types](client-context.md#user-types)
  - goal-04 :: Template question consistency | kind: Goal | success_measure: 100% of agent-configured programs use questions matching their type template | summary: The agent enforces template-based question sets so all programs of the same type have consistent forms | spec: [§Product Summary](client-context.md#product-summary)

Decisions:
  - dec-01 :: Conversational interface over enhanced form | kind: Decision | alternatives: (1) Improve the existing form UI with autofill and smart validation; (2) Add an AI sidebar assistant to the existing form wizard; (3) Full conversational replacement — this option chosen | reversal_trigger: Pilot shows fewer than half of admins complete the configuration end-to-end via chat without falling back to the form | summary: Admins configure programs via free-text chat rather than any variant of the multi-screen form | spec: [§Constraints](client-context.md#constraints)
  - dec-02 :: Preview-before-create at every stage | kind: Decision | alternatives: (1) Direct create with an undo operation; (2) Optimistic write to draft with explicit confirmation before publish only | reversal_trigger: Admins report the preview step adds friction without a measurable reduction in misconfiguration errors | summary: Nothing is written to the database until the admin sees and explicitly approves a full preview at the program stage and again at the form stage | spec: [§Product Summary](client-context.md#product-summary)
  - dec-03 :: Agent integrates via NestJS API, not direct DB | kind: Decision | alternatives: (1) Agent writes directly to the database, bypassing NestJS; (2) Agent wraps a new microservice with its own data layer | reversal_trigger: NestJS API contracts become incompatible with what the agent needs and renegotiation is not possible | summary: The agent calls existing NestJS endpoints for all program operations, keeping every business rule in the authoritative service layer | spec: [§Constraints](client-context.md#constraints)

Open Questions:
  - oq-01 :: Will admins adopt the chat interface? | kind: OpenQuestion | summary: Whether Infinitheism admins will prefer the conversational flow over the existing form wizard once both are available | spec: [§Open Questions](client-context.md#open-questions)
  - oq-02 :: Which seeker profile fields to pre-fill? | kind: OpenQuestion | summary: Which fields from a seeker's prior registrations should be pre-populated and in what priority order | spec: [§Open Questions](client-context.md#open-questions)
  - oq-03 :: How to handle custom program types without templates? | kind: OpenQuestion | summary: How the agent behaves when an admin configures a program type that has no existing question template | spec: [§Open Questions](client-context.md#open-questions)
  - oq-04 :: What admin onboarding is needed for chat adoption? | kind: OpenQuestion | summary: Whether admins need onboarding sessions, documentation, or in-chat tooltips to use the agent productively from day one | spec: [§Open Questions](client-context.md#open-questions)

Agent System:
  - component-01 :: Program Config Agent | kind: Component | boundary: In scope — conversational configuration, NestJS API integration, session state machine. Out of scope — seeker registration flow, direct database writes, payment handling. | summary: FastAPI + PydanticAI backend service that conducts the admin configuration conversation and calls NestJS APIs to create and publish programs | spec: [§Product Summary](client-context.md#product-summary)
  - sm-01 :: Program Config State Machine | kind: StateMachine | entity: Program Configuration Session | states: COLLECTING, TEMPLATE_SELECTION, PROGRAM_PREVIEW, PROGRAM_CREATED, FORM_PREVIEW, FORM_ATTACHED, READY_TO_PUBLISH, PUBLISHED | initial_state: COLLECTING | terminal_states: PUBLISHED | transitions: [§Product Summary](client-context.md#product-summary) | invariants_per_state: [§Product Summary](client-context.md#product-summary) | summary: Closed lifecycle of a single admin configuration session from first message to published program status | spec: [§Product Summary](client-context.md#product-summary)
  - component-03 :: Chat UI | kind: Component | boundary: In scope — admin conversation rendering, program and form preview display. Out of scope — backend API calls (delegated to FastAPI), seeker-facing registration UI. | summary: React 18 + TypeScript frontend that renders the admin-facing conversation and form previews | spec: [§Product Summary](client-context.md#product-summary)

Existing System:
  - component-02 :: NestJS Backend | kind: Component | boundary: In scope — all program CRUD, workflow assignment, form question attachment, publish operations. Out of scope — conversation management, pre-fill logic (owned by agent). | summary: Existing Infinitheism backend that owns all program DTOs, workflows, business rules, and the authoritative source of truth for program state | spec: [§Constraints](client-context.md#constraints)
  - component-04 :: Admin Form Wizard | kind: Component | boundary: In scope — manual field-by-field program creation via multi-screen UI. Out of scope — conversational configuration. | summary: The existing multi-screen manual program configuration UI that the agent complements; remains available as a fallback | spec: [§User Types](client-context.md#user-types)
  - component-05 :: Seeker Registration Service | kind: Component | boundary: In scope — seeker form submissions, registration status, seeker profile data. Out of scope — program configuration. | summary: Existing service handling seeker registrations — unchanged by this project; provides profile data for pre-fill | spec: [§User Types](client-context.md#user-types)
  - component-06 :: Program Type Registry | kind: Component | boundary: In scope — program type metadata, template definitions, workflow configs per type. Out of scope — program instance CRUD. | summary: Existing NestJS service providing program type metadata and question templates that the agent queries at session start | spec: [§Product Summary](client-context.md#product-summary)

Risks:
  - risk-01 :: Admin adoption failure | kind: Risk | likelihood: medium | impact: high | mitigation: Run pilot sessions with real admins before full rollout; measure chat completion rate vs. fallback to form | phase: design | summary: Admins may not adopt the conversational interface and fall back to the form wizard, leaving the agent unused in production | spec: [§Unvalidated Assumptions](client-context.md#unvalidated-assumptions)
  - risk-02 :: NestJS API contract change | kind: Risk | likelihood: low | impact: high | mitigation: Pin API contract versions; establish a change notification protocol with the NestJS team before development begins | phase: design | summary: Mid-development changes to NestJS API contracts could silently break the agent's integration layer | spec: [§Constraints](client-context.md#constraints)

Metrics:
  - metric-01 :: Admin time per program | kind: Metric | baseline: not measured | target: under 5 minutes | current: not measured | summary: Time from first admin message to program reaching published status | spec: [§Product Summary](client-context.md#product-summary)
  - metric-02 :: Misconfiguration rate | kind: Metric | baseline: not measured | target: zero | current: not measured | summary: Count of programs published with at least one missing or inconsistent required field | spec: [§Product Summary](client-context.md#product-summary)
  - metric-03 :: Seeker form completion rate | kind: Metric | baseline: not measured | target: higher than pre-agent baseline | current: not measured | summary: Percentage of seekers who begin and complete a registration form without abandonment | spec: [§User Types](client-context.md#user-types)
  - metric-04 :: Template question consistency | kind: Metric | baseline: not measured | target: 100% | current: not measured | summary: Percentage of agent-configured programs whose attached questions match their type template | spec: [§Product Summary](client-context.md#product-summary)

- assumption-01 :: Admin prefers chat over form | kind: Assumption | validation_plan: Pilot with 2–3 real admin sessions on staging; measure whether each admin completes the full configuration via chat or abandons mid-session to the form wizard | summary: Infinitheism admins will naturally adopt the conversational interface rather than reverting to the multi-screen form wizard | spec: [§Unvalidated Assumptions](client-context.md#unvalidated-assumptions)
- flow-01 :: Admin Program Configuration | kind: Flow | actor: Infinitheism Admin | trigger: Admin opens chat and types a program description | outcome: Program created and published with a form attached, seeker-ready in under 5 minutes | summary: 7-step conversational flow from program description to published status — describe, collect, preview, confirm, attach form, validate, publish | spec: [§Product Summary](client-context.md#product-summary)
- flow-02 :: Seeker Program Registration | kind: Flow | actor: Seeker | trigger: Seeker opens a published program listing | outcome: Registration submitted and confirmation received with next steps | summary: 5-step registration flow from program discovery to submission — find program, open form, fill pre-populated fields, submit, receive confirmation | spec: [§User Types](client-context.md#user-types)

user-01 -> flow-01 | relation: experiences
user-02 -> flow-02 | relation: experiences
user-03 -> component-01 | relation: owns
assumption-01 -> dec-01 | relation: enables
risk-01 -> goal-01 | relation: threatens
risk-02 -> component-01 | relation: threatens
oq-01 -> dec-01 | relation: threatens
oq-02 -> goal-03 | relation: threatens
oq-03 -> goal-04 | relation: threatens
oq-04 -> goal-01 | relation: threatens
dec-01 -> goal-01 | relation: serves
dec-02 -> goal-02 | relation: serves
dec-03 -> component-01 | relation: governs
component-01 -> flow-01 | relation: enables
component-01 -> sm-01 | relation: decomposes_into
component-02 -> component-01 | relation: enables
component-03 -> flow-01 | relation: enables
component-06 -> component-01 | relation: enables
flow-01 -> goal-01 | relation: serves
metric-01 -> goal-01 | relation: watches
metric-02 -> goal-02 | relation: watches
metric-03 -> goal-03 | relation: watches
metric-04 -> goal-04 | relation: watches
```

</details>

---

## Product Summary

The AI Platform — Program Configuration Agent enables Infinitheism admins to configure, preview, and publish programs through a single chat session. The agent handles the full sequence: extracting program details from free-text, assembling a complete `CreateProgramDto`, recommending form questions from per-type templates, showing an admin-facing preview at each stage, and calling the NestJS backend APIs to create and publish the program.

The seeker experience is a downstream benefit. By enforcing template-based question sets and pre-validating every required field before publish, the agent ensures seekers see complete, well-structured forms rather than whatever an admin happened to attach on a deadline. Seeker profile data from prior registrations is surfaced for pre-fill — seekers do not re-enter their name, city, or mobile number on every registration.

The agent does not replace the NestJS backend or the seeker registration service. All program DTOs, workflow rules, and API contracts remain in their authoritative service. The agent is a new conversational front-end layered on top of them.

### Admin Journey (7 steps)

```
1. Admin describes the program
       "5-day HDB, online, June 15, 100 seats, ₹5000 fee, internal"

2. Agent extracts what it can, asks only for what is missing
       "When does registration close? What name should appear on seeker emails?"

3. Admin answers → agent assembles full CreateProgramDto

4. Agent shows program preview → admin approves
       Program created in DB as DRAFT

5. Agent recommends form questions from the HDB template
       Shows questions across sections with binding keys

6. Admin reviews form preview → approves
       Questions attached to program

7. Agent runs final validation → admin publishes
       Status → PUBLISHED. Program live for seekers.
```

### Seeker Journey (5 steps)

```
1. Seeker finds the published program on the listing
2. Seeker opens the registration form — personal details pre-filled
3. Seeker fills program-specific questions and submits
4. Registration created (PENDING_APPROVAL if program requires approval)
5. Admin approves → seeker notified via email or WhatsApp
```

### Program Config State Machine

The agent's session lifecycle is a closed state machine. Every state transition requires an explicit admin confirmation.

```
COLLECTING → TEMPLATE_SELECTION → PROGRAM_PREVIEW → PROGRAM_CREATED
                                                   → FORM_PREVIEW → FORM_ATTACHED
                                                                  → READY_TO_PUBLISH → PUBLISHED
```

---

## User Types

**Admin** — Infinitheism staff who configure and publish programs for seekers. Primary frictions: multi-screen, 30+ field manual program setup with no guardrails; no validation until publish; manual question selection with no recommendations. Configures HDB, MSD, TAT, and custom program types. Needs speed (programs are announced close to their dates) and confidence (cannot publish a broken program). *Status: placeholder — no formal user interviews conducted.*

**Seeker** — Sincere spiritual participant who registers for programs on the Infinitheism platform. Primary frictions: no pre-fill from prior registrations, incomplete forms due to admin mistakes, no visibility into registration status after submit. Not directly involved in the agent workflow — they benefit from it downstream through more complete forms and fewer errors. *Status: placeholder — no formal user interviews conducted.*

**[PTL]** — Madhuri Karedla (madhuri.karedla@divami.com, Divami delivery team). Accountable for agent implementation and NestJS API integration. *Status: validated.*

---

## Constraints

| Constraint | Source |
|---|---|
| Stack fixed: FastAPI + PydanticAI + SQLAlchemy (backend); React 18 + TypeScript + shadcn/ui (frontend) | Project CLAUDE.md — non-negotiable |
| NestJS backend APIs are the source of truth — agent calls them, never writes to the DB directly | Architecture decision (dec-03) |
| Seeker registration flow is unchanged — agent scope ends at program publish | Vision doc scope boundary |
| All program validation rules, workflow assignments, and DTOs live in the NestJS backend | Architecture decision (dec-03) |
| Timeline: 1-day sprint | [PTL] decision |
| No Jira integration configured | PTL decision during init |

---

## Unvalidated Assumptions

These assumptions are baked into the design but have not been validated with real users or data. If any proves false, the project scope or approach will need revisiting.

**A1 — Admin will use chat naturally** *(explicitly flagged as unvalidated)*

We assume Infinitheism admins will prefer a conversational interface over the existing multi-screen form wizard. This has not been tested with actual users. If admins revert to the form wizard, the agent has no adoption path regardless of its technical correctness.

*Validation plan:* Pilot with 2–3 real admin sessions on a staging environment. Measure whether each admin completes the full configuration flow via chat or abandons to the form wizard mid-session.

**A2 — Existing NestJS API contracts are stable for the development window**

We assume the NestJS backend's API surface will not change significantly during the agent development sprint. This has not been confirmed with the NestJS team. A breaking change to any endpoint the agent calls would require unplanned rework.

*Validation plan:* Confirm a code freeze or change-notification protocol with the NestJS team before development begins.

**A3 — Program type templates cover the programs Infinitheism runs in practice**

We assume the HDB, MSD, TAT, and custom program type templates defined in the agent's codebase match what Infinitheism actually needs. If the admin configures a program type with no template, the agent's question recommendation is undefined.

*Validation plan:* Review the full list of active program types with an Infinitheism admin before building template selection logic.

---

## Open Questions

| # | Question | Blocks | Status |
|---|---|---|---|
| OQ-01 | Will admins naturally adopt the chat interface, or will they fall back to the form wizard? | Decision dec-01 (conversational interface) — if false, the design approach needs rethinking | Open |
| OQ-02 | Which seeker profile fields from prior registrations should be pre-filled, and in what priority order? | Goal goal-03 (seeker frictionless registration) | Open |
| OQ-03 | How does the agent handle program types not covered by the existing templates? | Goal goal-04 (template question consistency) | Open |
| OQ-04 | What level of admin onboarding (documentation, tooltips, demo) is needed for productive first use? | Goal goal-01 (admin < 5 min) — onboarding overhead affects time-to-value | Open |

---

## Approval

*Weight class: small — 1 approval required per gate.*

Approved by:
Role:
Date:
