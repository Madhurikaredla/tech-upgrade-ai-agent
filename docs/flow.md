# Application Flow

## Overview

The ai-platform is a conversational AI system where an admin types natural language to configure and publish a spiritual program. Instead of filling in a long form manually, the admin chats with an AI agent that extracts the required fields, previews the configuration, attaches a registration form, and publishes — all through a single chat interface.

---

## High-Level Architecture

```
Admin (Browser)
     │
     ▼
React UI (apps/ui)       ← Vite + TypeScript + Zustand + React Query
     │  POST /api/v1/program-config/chat
     ▼
FastAPI (apps/api)       ← Middleware: JWT auth, request logging, CORS
     │
     ├── ProgramConfigController
     │        │
     │        ▼
     │   ProgramConfigService
     │        │
     │        ▼
     │   run_chat()  ← packages/agents/program_config/runners.py
     │        │
     │        ├── COLLECTING  → PydanticAI LLM Agent (extraction)
     │        ├── PREVIEW     → deterministic keyword matching
     │        ├── PUBLISH     → API call to NestJS backend
     │        └── ...
     │
     ▼
Infinitheism NestJS API  ← api.portal.dev.divami.com
  POST /program
  POST /program-question
  PUT  /program/:id/status
```

---

## Conversation State Machine

Every conversation is a `SessionState` object persisted in PostgreSQL. The session moves forward through 7 stages:

```
COLLECTING
    │  (all required fields collected)
    ▼
TEMPLATE_SELECTION
    │  (admin picks a template)
    ▼
PROGRAM_PREVIEW
    │  (admin confirms or edits)
    ▼
PROGRAM_CREATED   ── auto-advances immediately after NestJS create call
    │
    ▼
FORM_PREVIEW
    │  (admin confirms form questions)
    ▼
FORM_ATTACHED     ── auto-advances immediately after NestJS attach call
    │
    ▼
READY_TO_PUBLISH
    │  (admin types "publish" or "keep as draft")
    ▼
PUBLISHED  (terminal)
```

---

## Stage-by-Stage Detail

### 1. COLLECTING

**What happens:**  
The LLM extraction agent receives the admin's message. It uses the current partial DTO and conversation history to extract any new field values from the message. Missing required fields are identified and the agent asks for them conversationally.

**Key files:**  
- [`packages/agents/program_config/stages/collecting.py`](../packages/agents/program_config/stages/collecting.py)  
- [`packages/agents/program_config/agent.py`](../packages/agents/program_config/agent.py)  
- [`packages/agents/program_config/rules.py`](../packages/agents/program_config/rules.py)

**Transition trigger:**  
All required fields present in `partial_dto` → moves to `TEMPLATE_SELECTION`.

**Special behavior:**  
When `sub_program_type` is first confirmed (e.g. "HDB"), a **type announcement** fires once: the system fetches the program type config from the DB, applies defaults, and sends a structured summary to the admin.

---

### 2. TEMPLATE_SELECTION

**What happens:**  
The system fetches available templates from NestJS for the confirmed program type. The admin picks a template (or skips) to clone as the base form.

**Key files:**  
- [`packages/agents/program_config/stages/template.py`](../packages/agents/program_config/stages/template.py)

**Transition trigger:**  
Admin selects a template number or types "skip" → moves to `PROGRAM_PREVIEW`.

---

### 3. PROGRAM_PREVIEW

**What happens:**  
A formatted summary of all collected fields is shown. The admin can type `yes` / `confirm` to proceed, or `edit <field>` to change a value (which re-enters COLLECTING for that field).

**Key files:**  
- [`packages/agents/program_config/stages/preview.py`](../packages/agents/program_config/stages/preview.py)

**Transition trigger:**  
Admin confirms → NestJS `POST /program` is called → session advances to `PROGRAM_CREATED`.

---

### 4. PROGRAM_CREATED (auto)

**What happens:**  
The program now exists in the backend with a real `program_id`. The agent immediately transitions to `FORM_PREVIEW` without waiting for another user message.

---

### 5. FORM_PREVIEW

**What happens:**  
Default registration form questions (from `templates.py`) are shown. The admin can confirm them or request customizations.

**Key files:**  
- [`packages/agents/program_config/stages/form.py`](../packages/agents/program_config/stages/form.py)  
- [`packages/agents/program_config/templates.py`](../packages/agents/program_config/templates.py)

**Transition trigger:**  
Admin confirms → NestJS `POST /program-question` is called for each question → advances to `FORM_ATTACHED`.

---

### 6. FORM_ATTACHED (auto)

**What happens:**  
Questions are attached. Agent immediately prompts for publish decision.

---

### 7. READY_TO_PUBLISH

**What happens:**  
Admin is shown a final summary. They type `publish` to go live or `keep as draft` to save without publishing.

**Key files:**  
- [`packages/agents/program_config/stages/publishing.py`](../packages/agents/program_config/stages/publishing.py)

**Transition trigger:**  
- `publish` → NestJS `PUT /program/:id/status` with `{status: "published", accessType: "PUBLIC"}` → `PUBLISHED`  
- `keep as draft` → stays `READY_TO_PUBLISH`

---

### 8. PUBLISHED (terminal)

Program is live. Seekers can discover and register. To create another program, start a new session.

---

## Chat History Persistence

Every turn stores two kinds of data:

| Data | What | Where |
|------|------|-------|
| `display_messages` | Human-readable chat log (`user` / `assistant` messages with timestamps) | Session record in DB |
| `message_history` | Raw PydanticAI message objects from the LLM call | Session record in DB |

The extraction agent receives the **last 8 display messages** (4 exchanges) embedded in the prompt as a conversation transcript — not as PydanticAI `message_history`. This avoids Gemini's restriction on consecutive tool-call/response turns when replaying structured-output histories.

---

## Request Lifecycle

```
1. POST /api/v1/program-config/chat
      { session_id, message, user_id }

2. LogfireLoggingMiddleware
      → sets request_id, user_id, bearer_token in ContextVars
      → opens logfire span: "http.request"

3. ProgramConfigController
      → delegates to ProgramConfigService.chat()

4. run_chat()  [packages/agents/program_config/runners.py]
      → repository.get_or_create(session_id, user_id)
      → _dispatch(session, message)  — routes to stage handler
      → repository.save(session)
      → _append_display_messages()

5. Return AgentChatResponse
      { session_id, reply, stage, dto_preview?, form_preview?, program_id? }
```

---

## NestJS API Calls Made by the Agent

| Stage | Method | Endpoint | Purpose |
|-------|--------|----------|---------|
| PROGRAM_PREVIEW confirm | POST | `/program` | Create program as DRAFT |
| FORM_PREVIEW confirm | POST | `/program-question` | Attach form questions |
| READY_TO_PUBLISH → publish | PUT | `/program/:id/status` | Set status = PUBLISHED |
| TEMPLATE_SELECTION | GET | `/v1/program-templates/program-type/:typeId` | List available templates |
| TEMPLATE_SELECTION (clone) | POST | `/program/clone-from-template` | Clone selected template |

All NestJS calls go through [`packages/agents/program_config/api_client.py`](../packages/agents/program_config/api_client.py), which reads the Bearer token from the request context and forwards it with each call.
