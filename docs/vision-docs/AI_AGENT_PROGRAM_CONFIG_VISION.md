# Vision Document — AI Agent for Program Configuration & Registration

---

## 1. Vision Statement

> **Enable any admin to configure, form-build, and publish a complete program through a single conversation — and give every seeker a frictionless, personalised registration experience on the other end.**

Today, configuring a program is a multi-screen, multi-step, expert-only task. Tomorrow, it is a conversation.

---

## 2. The World We Are Moving Away From

```
TODAY

Admin opens program form
    → fills 30+ fields manually
    → opens form builder separately
    → picks questions one by one
    → assigns workflow
    → checks for errors
    → publishes (hoping nothing is wrong)

Seeker opens program
    → sees a form that may be incomplete
    → re-enters details they've given before
    → gets no guidance on what to fill
    → submits and waits with no visibility
```

This world is slow, inconsistent, and fragile. A misconfigured program reaches seekers. Seekers drop off. Admins redo work.

---

## 3. The World We Are Building

```
TOMORROW

Admin opens chat
    → types what they want in plain language
    → agent asks only what it needs
    → agent shows a full preview before anything is created
    → admin says yes → program and form are live

Seeker opens program
    → sees a clean, complete form
    → profile fields are pre-filled
    → submits in minutes
    → gets immediate status and next steps
```

---

## 4. Who This Is For

### Admin
- Runs programs for Infinitheism — HDB, MSD, TAT, and custom types
- Knows what program they want to run but shouldn't need to know every system field
- Needs speed: programs are announced close to their dates
- Needs confidence: cannot afford to publish something broken

### Seeker
- A sincere spiritual participant, often repeating registrations across programs
- Should not have to re-enter their name, city, and mobile number every time
- Needs clarity: what program is this, what do I need to fill, what happens after I submit

---

## 5. Core Principles

| Principle | What It Means |
|-----------|--------------|
| **Conversation first** | Admin never fills a form to create a form. Everything is chat. |
| **Preview before create** | Nothing is written to the database until the admin sees and approves it |
| **Context is never lost** | The agent remembers the full conversation — admin never has to repeat themselves |
| **Validate before publish** | The agent blocks publishing if the configuration is incomplete or inconsistent |
| **Seeker experience is the output** | The program the admin configures is judged by how well a seeker can register through it |

---

## 6. The Two Journeys

### Journey A — Admin Configures a Program

```
1. Admin describes the program
       "5-day HDB, online, June 15, 100 seats, ₹5000 fee, internal"

2. Agent fills what it knows, asks for the rest
       "When does registration close? What name on seeker emails?"

3. Admin answers → agent assembles full config
       Shows: name, type, dates, mode, fee, capacity, workflow, access

4. Admin reviews preview → approves
       Program created in DB as DRAFT

5. Agent recommends form questions from HDB template
       Shows: 12 questions across 3 sections with binding keys

6. Admin reviews form preview → approves
       Questions attached to program

7. Agent runs final validation
       Confirms: dates ok, form not empty, workflow assigned

8. Admin publishes
       Status → PUBLISHED. Program live for seekers.
```

**Admin's experience:** One chat window. One confirmation per stage. Done.

---

### Journey B — Seeker Registers

```
1. Seeker finds HDB June 2026 on the program listing

2. Seeker opens registration form
       Personal details pre-filled from last registration
       Only new/program-specific questions need input

3. Seeker fills and submits
       Validation runs per question

4. Registration created
       Status: PENDING_APPROVAL (because program requires approval)
       Confirmation shown with registration ID and next steps

5. Admin approves → seeker notified via email/WhatsApp
```

**Seeker's experience:** A clean, pre-filled form. Submit in under 3 minutes. Know what happens next.

---

## 7. What Success Looks Like

| Outcome | Measure |
|---------|---------|
| Admin time from intent to published program | Under 5 minutes |
| Programs published with misconfiguration | Zero |
| Seeker form completion rate | Higher than current baseline |
| Question consistency across same program type | 100% (agent enforces template) |
| Admin training required to configure a new program | None — conversation is the interface |

---

## 8. Scope Boundaries

### In Scope
- Conversational program configuration (all fields of `CreateProgramDto`)
- Template-based form question recommendation and attachment
- Program preview → confirm → create flow
- Form preview → confirm → attach flow
- Publish with pre-publish validation
- Seeker registration form pre-fill from previous registrations

### Out of Scope (for now)
- Agent modifying an already-published program
- Agent handling payments or invoices
- Agent managing seeker approvals or waitlist decisions
- Seeker-facing conversational registration (seeker still uses the form UI)

---

## 9. How It Fits the Existing System

The agent does not replace anything. It is a **new entry point** into the existing services:

```
Agent Chat
    │
    ├── calls → program.service.create()
    ├── calls → program-question service (attach questions)
    ├── calls → program.service.updateStatus() (publish)
    │
    └── existing registration flow unchanged
              seeker → registration.service.create()
```

All business rules, validations, entities, DTOs, and workflows already in the system remain the source of truth. The agent is an intelligent front-end to them.

---

## 10. North Star

> An admin who has never used the system before can configure and publish a complete program correctly on their first try, guided entirely by the agent — and every seeker who registers through that program has a seamless, pre-filled experience that respects their time.
