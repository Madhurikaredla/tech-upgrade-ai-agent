# AI Platform — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Admin Browser                                  │
│                    React 18 + Vite  (port 4002)                         │
│                                                                         │
│  ChatWindow ──► ProgramPreviewCard ──► FormPreviewCard                  │
│     │                │                       │                          │
│  Zustand           dto_preview            form_preview                  │
│  React Query       (from API)             (from API)                    │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │ HTTP / JSON
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend  (port 8000)                         │
│                                                                         │
│   POST /api/v1/program-config/chat                                      │
│   POST /api/v1/analyze | /prompt | /chat                                │
│   POST /api/v1/auth/login | /verify-otp                                 │
│   GET  /health                                                          │
│                                                                         │
│  Middleware: CORS · JWT auth · Logfire request logging                  │
│  Exception handlers: AppError · HTTP · Validation · Generic             │
└──────────┬──────────────────────────────┬───────────────────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────┐      ┌───────────────────────────────────────────┐
│  Analysis Agent      │      │        Program Config Agent               │
│  packages/agents/    │      │        packages/agents/program_config/    │
│  analysis/           │      │                                           │
│                      │      │  runners.py ──► _dispatch()               │
│  agent.py            │      │      │                                    │
│  schemas.py          │      │      └── stage router (see state machine) │
│  prompts.py          │      │                                           │
│  runners.py          │      │  agent.py   ← PydanticAI singleton        │
│  tools.py            │      │  schemas.py ← ExtractedFields, DTOs       │
│                      │      │  prompts.py ← SYSTEM_PROMPT, EXTRACTION   │
│  run_analysis()      │      │  rules.py   ← field rules & validation    │
│  stream_analysis()   │      │  templates.py ← default form questions    │
│                      │      │  db_lookup.py ← type/workflow IDs         │
└──────────────────────┘      │  repository.py ← session CRUD            │
                              │  api_client.py ← NestJS HTTP calls        │
                              └───────────────────────────────────────────┘
```

---

## Program Config Agent — Conversation State Machine

The AI model is called **only in COLLECTING**. Every other stage is
deterministic — keyword detection + NestJS API calls.

```
  Admin sends message
         │
         ▼
  ┌─────────────┐    AI model call (PydanticAI)
  │  COLLECTING │◄─── extraction + missing field questions
  └──────┬──────┘
         │ all_required_collected = true
         ▼
  ┌────────────────────┐
  │  TEMPLATE_SELECTION│  show available templates; admin picks one
  └──────┬─────────────┘
         │ template chosen
         ▼
  ┌───────────────┐
  │ PROGRAM_PREVIEW│  render preview card; wait for confirm / edit
  └──────┬─────────┘
         │ confirm ("yes" / "ok" / natural language)
         ▼
  ┌────────────────┐   POST /programs  →  NestJS
  │ PROGRAM_CREATED│──────────────────────────────► NestJS Backend
  └──────┬─────────┘                                (creates DRAFT)
         │ auto-advance
         ▼
  ┌──────────────┐
  │ FORM_PREVIEW │  show registration form questions; admin can edit
  └──────┬───────┘
         │ confirm ("ok" / natural language)
         ▼
  ┌─────────────┐   POST /programs/:id/questions  →  NestJS
  │ FORM_ATTACHED│─────────────────────────────────► NestJS Backend
  └──────┬───────┘
         │ auto-advance
         ▼
  ┌──────────────────┐
  │ READY_TO_PUBLISH │  final review; admin types "publish" or "keep as draft"
  └──────┬───────────┘
         │ publish
         ▼
  ┌───────────┐   PATCH /programs/:id/publish  →  NestJS
  │ PUBLISHED │──────────────────────────────────► NestJS Backend
  └───────────┘                                    (status → PUBLIC)
```

---

## Data Flow — Single Chat Turn

```
  Admin message
       │
       ▼
  AgentChatRequest { session_id, message, user_id }
       │
       ▼
  repository.get_or_create(session_id)          ← PostgreSQL
       │ SessionState { stage, partial_dto, template_questions, … }
       ▼
  _dispatch(session, message)
       │
       ├── COLLECTING ──► run_extraction()
       │                      │
       │                      ▼
       │              PydanticAI agent.run(EXTRACTION_PROMPT + transcript)
       │                      │ ExtractedFields (structured JSON)
       │                      ▼
       │              merge into session.partial_dto
       │                      │
       │                      ▼
       │              rules.get_missing_required_fields()
       │                      │
       │              [missing?] → ask follow-up
       │              [complete] → advance to TEMPLATE_SELECTION
       │
       ├── PROGRAM_PREVIEW ──► is_confirm() / is_edit() / run_extraction()
       │
       ├── FORM_PREVIEW ──► _is_confirm() / _is_edit() / apply_form_edit()
       │
       └── READY_TO_PUBLISH ──► _contains_publish() / validate_for_publish()
                                       │
                                       ▼
                              api_client.publish_program()  →  NestJS
       │
       ▼
  repository.save(session)                      ← PostgreSQL
       │
       ▼
  AgentChatResponse { session_id, reply, stage, dto_preview, form_preview, … }
```

---

## Package Dependency Map

```
apps/api/
  main.py
    └── routes/ ──► controllers/ ──► services/
                                         ├── program_config_service ──► packages/agents/program_config/runners
                                         ├── agent_service           ──► packages/agents/analysis/runners
                                         └── auth_service            ──► packages/auth/service

packages/
  agents/
    program_config/
      runners      ──► stages/{collecting, template, preview, form, publishing}
      stages/      ──► api_client ──► packages/client/nestjs_client
                   ──► repository ──► packages/db/database (PostgreSQL)
                   ──► agent      ──► packages/config/model_factory (Google / Groq / Anthropic)
  common/
    schemas/api_response   ← APIResponse[T] — all routes wrap output here
  handlers/
    exceptions             ← typed AppError hierarchy
    http_handlers          ← FastAPI exception → JSON response
  config/
    settings               ← Pydantic BaseSettings (reads .env)
    model_factory          ← get_model() selects AI provider from env
  db/
    database               ← async SQLAlchemy engine + SessionLocal
    models                 ← ORM models (ChatSession, DisplayMessage, …)
  client/
    nestjs_client          ← singleton HTTP client (httpx) with retry
  logging/
    setup                  ← configure_logfire()
    context                ← ContextVar request_id / user_id
    decorators             ← @log_agent_run, @log_span
```

---

## Infrastructure & External Services

```
┌────────────────────────────────────────────────────────────┐
│                    ai-platform (this repo)                 │
│                                                            │
│  FastAPI :8000  ◄──────────────────────► React UI :4002   │
│       │                                                    │
│       ├── PostgreSQL (session state + display messages)    │
│       │                                                    │
│       ├── AI Provider (one of):                            │
│       │     Google Gemini  (GOOGLE_API_KEY)                │
│       │     Groq           (GROQ_API_KEY)                  │
│       │     Anthropic      (ANTHROPIC_API_KEY)             │
│       │                                                    │
│       └── NestJS Backend   (NESTJS_BASE_URL)               │
│             ├── POST /programs           (create draft)    │
│             ├── POST /programs/:id/questions (attach form) │
│             └── PATCH /programs/:id      (publish)         │
│                                                            │
│  Observability: Logfire  (LOGFIRE_TOKEN)                   │
└────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Why |
|---|---|
| AI model called only in COLLECTING | Keeps latency low; all other stages are instant keyword matching |
| Prompt-embedded transcript (not `message_history`) | Gemini rejects consecutive tool-call turns; plain text avoids 400 errors |
| `ExtractedFields` typed model (not `dict`) | Forces structured output; catches hallucinated field names at parse time |
| Stage handlers in `stages/` sub-package | Each stage is a pure function — easy to test, replace, or extend independently |
| `SessionState` persisted to PostgreSQL | Survives server restarts; allows multi-tab and mobile resume |
| NestJS as the source of truth for programs | ai-platform only orchestrates; actual data lives in the existing platform DB |
