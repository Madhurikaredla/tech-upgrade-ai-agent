# Best Practices

This document covers the production-grade patterns used in this project: authentication guards, role-based access, chat history, input validation, error handling, and observability.

---

## 1. Authentication Guard (OTP + JWT)

### How it works
Authentication is **delegated entirely to the Infinitheism NestJS backend**. This service does not issue its own JWTs.

**Login flow:**
```
1. Admin submits phone/email → POST /api/v1/auth/login
2. FastAPI proxies → NestJS POST /auth/login  → OTP sent
3. Admin submits OTP → POST /api/v1/auth/verify-otp
4. FastAPI proxies → NestJS POST /auth/validate-otp → returns token
5. Token returned to UI; stored in browser; sent as Authorization: Bearer <token>
```

**Request guard:**
Every protected request must include the Bearer token as a header. The `LogfireLoggingMiddleware` extracts it and stores it in a ContextVar (`set_bearer_token`). All downstream NestJS calls automatically forward this token.

```python
# middleware/logging.py
auth_header = request.headers.get("Authorization", "")
token = auth_header.removeprefix("Bearer ").strip()
set_bearer_token(token)
```

```python
# nestjs_client.py — token forwarded to all NestJS calls
headers = {"Authorization": f"Bearer {get_bearer_token()}"}
```

**Where in the code:**
- Auth service: [`packages/auth/service.py`](../packages/auth/service.py)
- Auth routes: [`apps/api/routes/v1/routers/auth.py`](../apps/api/routes/v1/routers/auth.py)
- Token forwarding: [`packages/client/nestjs_client.py`](../packages/client/nestjs_client.py)

---

## 2. Role-Based Access

### How it works
The caller's active role is forwarded from the UI to the API and on to NestJS via the `active-role` request header. This allows NestJS to apply its own role-based authorization rules on program creation and publishing.

```python
# middleware/logging.py
active_role = request.headers.get("active-role", "")
set_active_role(active_role)
```

The NestJS backend enforces which roles can create, edit, or publish programs. This API does not re-implement role authorization — it trusts NestJS as the authority.

**Pattern:**  
UI sets `active-role: admin` → FastAPI reads + stores in ContextVar → NestJS client sends it with every downstream call → NestJS enforces permission.

---

## 3. Chat History

### Two layers of history

| Layer | Purpose | Storage |
|-------|---------|---------|
| `display_messages` | Human-readable chat log shown in the UI | DB (session record) |
| `message_history` | Raw PydanticAI LLM message objects | DB (session record) |

### Display messages
After every turn, the runner appends both the user message and the agent reply to `display_messages`:

```python
# runners.py  _append_display_messages()
msgs.append({
    "id": f"u_{t}",
    "role": "user",
    "content": user_msg,
    "ts": now
})
msgs.append({
    "id": f"a_{t+1}",
    "role": "assistant",
    "content": response.reply,
    "stage": response.stage.value,
    "ts": now,
    "dto_preview": ...   # only when present
})
```

The UI reads `display_messages` to render the full conversation thread.

### Conversation context in LLM calls
The extraction agent does **not** use PydanticAI `message_history` replay (this breaks Gemini's tool-call format). Instead, the last 8 display messages (4 exchanges) are embedded in the prompt as a plain text transcript:

```python
# collecting.py
recent = display[-8:]
lines = [f"{'Admin' if m['role']=='user' else 'Assistant'}: {m['content']}" for m in recent]
conversation_history = "\n".join(lines)

prompt = EXTRACTION_PROMPT.format(
    conversation_history=conversation_history,
    ...
)
```

This gives the LLM full context of what was already discussed without API format constraints.

### Where in the code
- History append: [`packages/agents/program_config/runners.py`](../packages/agents/program_config/runners.py) → `_append_display_messages()`
- History storage: [`packages/agents/program_config/repository.py`](../packages/agents/program_config/repository.py)
- Context injection: [`packages/agents/program_config/stages/collecting.py`](../packages/agents/program_config/stages/collecting.py) → `run_extraction()`

---

## 4. Input Validation

### Request-level validation
All API request bodies are Pydantic `BaseModel` subclasses. FastAPI validates them automatically and returns `422 Unprocessable Entity` on failure.

```python
class AgentChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = Field(..., min_length=1, max_length=10_000)
    user_id: str = Field(..., min_length=1)
```

### Business rule validation (field rules)
Before advancing to PROGRAM_PREVIEW, all fields pass through `rules.apply_rules()` which enforces cross-field constraints:

- `mode_of_operation = ONLINE` → `is_travel_involved = False` (forced)
- `requires_payment = True` → `base_price` must be set
- `limited_seats = True` → `total_seats` must be set
- `has_checkin_checkout = True` → check-in/out times required

```python
# rules.py
session.partial_dto = rules.apply_rules(session.partial_dto)
```

### Publish-time validation
Before calling the NestJS publish endpoint, `validate_for_publish()` checks that all fields required for a live program are present:

```python
errors = validate_for_publish(session.partial_dto)
if errors:
    return AgentChatResponse(reply="Cannot publish — ...", ...)
```

### Where in the code
- Field rules: [`packages/agents/program_config/rules.py`](../packages/agents/program_config/rules.py)
- Pydantic request models: [`packages/agents/program_config/schemas.py`](../packages/agents/program_config/schemas.py)
- Publish validation: [`packages/agents/program_config/rules.py`](../packages/agents/program_config/rules.py) → `validate_for_publish()`

---

## 5. Typed Exception Hierarchy

### Pattern
All application errors extend a base `AppError`. FastAPI exception handlers catch specific types and return consistent JSON error shapes.

```
AppError
├── NotFoundError     → 404
├── UnauthorizedError → 401
├── ForbiddenError    → 403
└── ValidationError   → 422
```

```python
# handlers/exceptions.py
class AppError(Exception):
    status_code: int
    detail: str

class NotFoundError(AppError):
    status_code = 404
```

```python
# handlers/http_handlers.py
@app.add_exception_handler(AppError, app_error_handler)
```

All errors produce the same envelope:
```json
{
  "success": false,
  "error": "Not found",
  "detail": "Session abc123 does not exist"
}
```

### Where in the code
- Exception types: [`packages/handlers/exceptions.py`](../packages/handlers/exceptions.py)
- FastAPI handlers: [`packages/handlers/http_handlers.py`](../packages/handlers/http_handlers.py)

---

## 6. APIResponse[T] — Consistent Response Envelope

All successful API responses are wrapped in a generic `APIResponse[T]`:

```python
class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None
```

**Usage in routes:**
```python
@router.post("/chat", response_model=APIResponse[AgentChatResponse])
async def chat(...):
    result = await service.chat(request)
    return ok(result)
```

This makes client-side handling predictable — always check `success`, always read from `data`.

### Where in the code
- Schema: [`packages/common/schemas/api_response.py`](../packages/common/schemas/api_response.py)
- Helpers: [`packages/common/services/api_response.py`](../packages/common/services/api_response.py)

---

## 7. Retry & Resilience

### NestJS client retries
All HTTP calls to NestJS use an exponential backoff retry wrapper (`packages/client/retry.py`) with up to 3 retries on transient errors (502, 503, 504, connection errors).

### LLM call retries
The extraction agent (`collecting.py`) retries up to 2 times on transient model HTTP errors (429, 502, 503, 504) with exponential backoff:

```python
for attempt in range(_MAX_RETRIES + 1):
    try:
        result = await agent.run(prompt)
        break
    except ModelHTTPError as exc:
        if exc.status_code in _TRANSIENT_STATUSES:
            await asyncio.sleep(1.5 ** attempt)
            continue
        raise
```

On exhausting retries, the agent returns a "model is temporarily busy" message rather than crashing the session.

---

## 8. Repository Pattern

All database access goes through repository classes — never from service or agent code directly. This keeps SQL/ORM logic isolated and testable.

```
Controllers / Services
       │
       ▼
  Repositories        ← only place that talks to DB
       │
       ▼
  SQLAlchemy (async)  ← packages/db/database.py
```

**Repositories used:**
- [`packages/repositories/session_repository.py`](../packages/repositories/session_repository.py) — read/write `SessionState`
- [`packages/repositories/user_repository.py`](../packages/repositories/user_repository.py) — user lookups
- [`packages/agents/program_config/repository.py`](../packages/agents/program_config/repository.py) — display messages + message history

---

## 9. Observability Best Practices

- Use `logfire.span(name, **attrs)` for every significant operation — never `print()`
- Attach `request_id` and `user_id` to every span (done automatically by the decorators)
- Use `logfire.info()` for expected business events, `logfire.warning()` for recoverable errors, `logfire.exception()` for unexpected failures
- Never log secrets — `SecretStr` in Pydantic settings prevents `.env` values from appearing in logs

```python
# Good
logfire.info("auth.send_otp", phone=phone)
logfire.warning("agent.model_http_error", status=exc.status_code, attempt=attempt)
logfire.exception("publish_program failed")

# Bad
print(f"sending OTP to {phone}")
logging.error(str(exc))
```

---

## 10. Frontend Best Practices

| Concern | Pattern |
|---------|---------|
| Server state | React Query (`useQuery`, `useMutation`) |
| Shared UI state | Zustand store |
| Form state | React Hook Form + Zod schema |
| Component size | Max 200 lines; split if larger |
| Styling | Tailwind classes in `.styles.ts` only, not in `.tsx` |
| Type safety | TypeScript strict mode, no `any` |
| Dark mode | Required — use CSS semantic tokens |
| Accessibility | Semantic HTML + ARIA labels mandatory |
| API layer | Service → mapper → hook → component (never fetch in component) |
| DTOs | Never import backend DTO types directly into UI components |
