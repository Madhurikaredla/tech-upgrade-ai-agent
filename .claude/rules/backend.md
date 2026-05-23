# Backend Engineering Rules (PydanticAI + FastAPI)

## Project Layout

```
ai-platform/
├── apps/api/
│   ├── main.py                          # App factory + lifespan + middleware + handlers
│   ├── dependencies.py                  # FastAPI Depends() factories
│   └── routes/
│       ├── routes.py                    # Root router (health + v1)
│       └── v1/
│           ├── routes.py                # Aggregates all v1 routers
│           └── routers/
│               ├── agent.py
│               ├── auth.py
│               ├── health.py
│               └── program_config.py
│
├── packages/
│   ├── agents/
│   │   ├── analysis/                    # Analysis agent
│   │   │   ├── agent.py                 # Agent singleton factory
│   │   │   ├── schemas.py               # Input/output Pydantic models
│   │   │   ├── prompts.py               # System prompt constants
│   │   │   ├── tools.py                 # @agent.tool functions
│   │   │   └── runners.py               # run_analysis(), stream_analysis()
│   │   └── program_config/              # Program config agent
│   │       ├── agent.py
│   │       ├── schemas.py               # CreateProgramDto, SessionState, etc.
│   │       ├── prompts.py               # SYSTEM_PROMPT, EXTRACTION_PROMPT
│   │       ├── rules.py                 # apply_rules(), validate_for_publish()
│   │       ├── templates.py             # Default form question sets
│   │       ├── db_lookup.py             # Cached DB lookups
│   │       ├── repository.py            # Session CRUD (was db_session.py)
│   │       ├── api_client.py            # NestJS API calls (_create_program, etc.)
│   │       ├── runners.py               # run_chat() → _dispatch() orchestrator
│   │       └── stages/
│   │           ├── collecting.py        # COLLECTING stage handler
│   │           ├── preview.py           # PROGRAM_PREVIEW stage handler
│   │           ├── form.py              # FORM_PREVIEW / FORM_ATTACHED handlers
│   │           └── publishing.py        # READY_TO_PUBLISH / PUBLISHED handlers
│   ├── common/
│   │   ├── schemas/
│   │   │   └── api_response.py          # APIResponse[T] generic wrapper
│   │   └── services/
│   │       └── api_response.py          # success_response() / error_response()
│   ├── handlers/
│   │   ├── exceptions.py                # Typed exception hierarchy
│   │   └── http_handlers.py             # FastAPI exception handlers
│   ├── repositories/
│   │   ├── session_repository.py        # SessionRepository (thin adapter)
│   │   └── user_repository.py           # UserRepository
│   ├── config/
│   │   ├── settings.py                  # Pydantic BaseSettings
│   │   └── model_factory.py             # get_model() → PydanticAI Model
│   ├── db/
│   │   ├── database.py                  # Engine + SessionLocal + init_db()
│   │   └── models.py                    # SQLAlchemy ORM models
│   ├── client/
│   │   ├── nestjs_client.py             # NestJSClient singleton
│   │   └── retry.py                     # @with_retry decorator
│   ├── auth/
│   │   └── service.py                   # OTP send/verify (delegates to NestJS)
│   ├── tools/
│   │   ├── data_tools.py                # Shared PydanticAI tools
│   │   └── enrichment_tools.py
│   ├── models/
│   │   ├── input.py                     # Shared request models
│   │   └── output.py                    # Shared response models
│   └── logging/
│       ├── setup.py                     # configure_logfire()
│       ├── context.py                   # ContextVar request_id / user_id
│       └── decorators.py                # @log_agent_run() / @log_span()
```

---

## Agent Pattern

```python
# packages/agents/<name>/agent.py
from pydantic_ai import Agent
from packages.config.model_factory import get_model
from .schemas import OutputSchema
from .prompts import SYSTEM_PROMPT

_agent: Agent[None, OutputSchema] | None = None


def _build_agent() -> Agent[None, OutputSchema]:
    return Agent(
        model=get_model(),
        output_type=OutputSchema,
        system_prompt=SYSTEM_PROMPT,
    )


def get_<name>_agent() -> Agent[None, OutputSchema]:
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent
```

Rules:
- `output_type` is always a `BaseModel` subclass defined in `schemas.py`
- Agent is module-level singleton (`_agent`) — never instantiated per request
- System prompt is `str` constant from `prompts.py`
- Never import agent from outside `packages/agents/<name>/`

---

## Schemas Pattern

```python
# packages/agents/<name>/schemas.py
from __future__ import annotations
from pydantic import BaseModel, Field

# Agent output — what the LLM returns
class AgentOutput(BaseModel):
    reply: str
    extracted_fields: dict[str, str] = Field(default_factory=dict)

# Domain DTOs — internal data transfer
class CreateProgramDto(BaseModel):
    name: str | None = None
    # ...

# API request/response — what routes expose
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    reply: str
```

Rules:
- Separate classes for: LLM output · domain DTOs · API contracts
- Never use `dict[str, Any]` as a field type — define a nested model
- All optional fields default to `None` or a factory
- Enums in `schemas.py` alongside the models that use them

---

## Runner Pattern

```python
# packages/agents/<name>/runners.py
import logfire
from packages.logging.decorators import log_agent_run
from .agent import get_<name>_agent
from .schemas import ChatRequest, ChatResponse

@log_agent_run("<name>")
async def run_chat(request: ChatRequest) -> ChatResponse:
    with logfire.span("<name>.chat", session_id=request.session_id):
        # orchestrate — delegate to stage handlers or service layer
        ...
```

Rules:
- Entry-point function decorated with `@log_agent_run()`
- Every external call (DB, NestJS) wrapped in `logfire.span()`
- Handle `ModelHTTPError`, `UnexpectedModelBehavior`, `httpx.ConnectError`
- Never raise `HTTPException` from a runner — let routes translate

---

## Repository Pattern

```python
# packages/repositories/session_repository.py
from packages.db.database import SessionLocal
from packages.agents.program_config.schemas import SessionState

class SessionRepository:
    async def get_or_create(self, session_id: str, user_id: str) -> SessionState:
        async with SessionLocal() as db:
            ...

    async def save(self, session: SessionState) -> None:
        ...
```

Rules:
- One repository class per aggregate root
- All methods `async`
- `SessionLocal` context manager only inside repository methods
- Never leak SQLAlchemy rows — always map to domain models before returning

---

## Exception Hierarchy

```python
# packages/handlers/exceptions.py
class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"

class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"

class AgentProcessingError(AppError):
    status_code = 502
    code = "AGENT_ERROR"
```

```python
# packages/handlers/http_handlers.py — registered in main.py
async def app_error_handler(request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        {"success": False, "error": {"code": exc.code, "message": str(exc)}},
        status_code=exc.status_code,
    )
```

---

## Route Pattern

```python
# apps/api/routes/v1/routers/<name>.py
import logfire
from fastapi import APIRouter, HTTPException, status
from packages.agents.<name>.runners import run_chat
from packages.agents.<name>.schemas import ChatRequest, ChatResponse
from packages.logging.context import get_request_id

router = APIRouter(prefix="/api/v1/<name>", tags=["<name>"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    with logfire.span("route.<name>.chat", session_id=request.session_id):
        try:
            return await run_chat(request)
        except Exception as exc:
            logfire.exception("<name>.chat failed", request_id=get_request_id())
            raise HTTPException(status_code=500, detail="Agent error") from exc
```

Rules:
- `response_model=` always specified
- Route body only: parse → delegate to runner → return
- No business logic — no DB calls — no agent calls
- Wrap in `logfire.span()` every time
- Translate runner exceptions to `HTTPException` only in routes

---

## Settings Rules

```python
# Always use get_settings() — never instantiate Settings() directly
from packages.config.settings import get_settings

settings = get_settings()  # lru_cache — zero overhead repeated calls
```

Add new settings:
1. Add field to `Settings` class with `SecretStr` for secrets
2. Add to `.env.example`
3. Document in README

---

## Logfire Rules

```python
# Spans for every significant operation
with logfire.span("operation.name", key=value):
    ...

# Info for significant state changes
logfire.info("program.published", program_id=pid, user_id=uid)

# Warning for recoverable errors
logfire.warning("db.fallback_to_memory", session_id=sid)

# Exception for unhandled errors (includes traceback)
logfire.exception("operation.failed", session_id=sid)
```

Never:
- `print()` anything
- `import logging` or use stdlib logger
- Swallow exceptions without logging
