# AGENTS.md — AI Platform Engineering Standards

This file is automatically loaded by Codex at the start of every session.
All detailed rules live in `.Codex/rules/`.
These rules are **non-negotiable** and apply to every task.

---

# Project Overview

`ai-platform` is a Python (FastAPI + PydanticAI) backend with a React/TypeScript frontend.

**Backend stack:** FastAPI · PydanticAI · SQLAlchemy (async) · Logfire · Pydantic v2  
**Frontend stack:** React 18 · TypeScript · Vite · shadcn/ui · Tailwind CSS · React Query · Zustand · Zod

**Architecture mirrors `ai-enterprise-brain`:**
- `packages/agents/` — each agent has `agent.py · schemas.py · prompts.py · runners.py · tools.py`
- `apps/api/routes/v1/routers/` — versioned route handlers
- `packages/common/` — shared APIResponse wrapper
- `packages/handlers/` — typed exceptions + FastAPI handlers
- `packages/repositories/` — data access layer

---

# Non-Negotiables (Always Apply)

## TypeScript (Frontend)
- TypeScript only — never JavaScript
- Never use `any`
- Never use `as any`
- Never use unsafe type assertions
- Explicit types for props, hooks, service returns, payloads, DTOs
- API types and domain types must be separate
- Exhaustive switch statements required (`assertNever`)
- Prefer `type` over `interface` unless extension is required

---

## React Architecture
- Pages compose only — no business logic in pages
- Components render only — business logic belongs in hooks
- No API calls in components
- No data transformation in UI
- No prop drilling beyond 2 levels — use composition/context
- Single responsibility per component
- Component file max 200 lines
- Hook file max 150 lines
- Service file max 100 lines
- No anonymous functions in JSX
- Never use array index as React key

---

## Component Standards
- One component = one folder
- Required structure:

```text
ComponentName/
  ComponentName.tsx
  ComponentName.styles.ts
  types.ts
  index.ts
```

- Named exports preferred
- Barrel exports required
- No component should import from another component's internals
- Shared UI primitives only in `shared-components/ui`

---

## State Management
- Local UI state → `useState`
- Form state → React Hook Form
- Shared domain state → Zustand
- Server state → React Query
- Never store derived state
- Never duplicate state across local/store/query cache
- No global state for component-only concerns

---

## Data Fetching
- React Query required for async data
- Never use `useEffect + fetch`
- Service → mapper → hook → UI architecture mandatory
- DTOs never reach UI
- All API endpoints from constants
- Requests must support cancellation
- Retry strategy must be explicit
- Errors must be mapped before reaching UI

---

## Forms
- Forms use Zod + React Hook Form only
- Schema is source of truth
- Infer TS types from schema
- No manual validation in components
- No local `useState` for form fields
- Submit disabled while pending
- Validation messages from schema only

---

## Styling
- shadcn/ui only
- Never use MUI / Chakra / AntD
- No raw Tailwind classes in `.tsx`
- Extract classes to `ComponentName.styles.ts`
- No inline style attribute
- No hardcoded colors
- Only CSS variables from `globals.css`
- Every light-mode class must have `dark:` counterpart
- No arbitrary Tailwind values unless tokenized
- Typography must use theme scale
- Spacing must use design scale
- Mobile-first responsive styling mandatory

---

## Theming
- Dark mode support required
- No theme-specific hardcoding
- Theme tokens only
- Colors must come from semantic tokens

---

## Accessibility
- All interactive elements keyboard accessible
- All controls require visible focus state
- Buttons must use `<button>`
- Inputs require labels
- Images require valid `alt`
- ARIA attributes required where applicable
- No clickable `div`

---

## Routing
- Route constants only
- No hardcoded paths
- Route params typed
- Protected routes through route guards only
- Lazy-load all route pages unless shell-critical

---

## Error Handling (Frontend)
- No silent catches
- Every error must be: logged · mapped · surfaced appropriately
- UI never consumes raw backend error
- Error boundaries required at: app root · route boundaries · async widget boundaries

---

## Notifications
- Toasts from hooks only
- Never call toast in UI components
- Success/error messaging centralized

---

## Security (Frontend)
- Never store tokens in localStorage
- Never trust frontend validation
- Sanitize any HTML rendering
- No secrets in frontend code
- No sensitive data in query params
- Environment variables must be prefixed and typed

---

## Performance
- Lazy-load routes
- Virtualize lists > 50 items
- Debounce search inputs
- Memo only when justified
- Avoid unnecessary re-renders
- Suspense boundaries required for async UI

---

## Logging (Frontend)
- No `console.log`
- No `console.error`
- No `debugger`
- Use centralized logging service only

---

## Testing (Frontend)
- Hooks require unit tests
- Services require unit tests
- Pages require integration tests
- Utilities require unit tests
- Prefer semantic selectors over test IDs
- Mock only external boundaries

---

## Code Hygiene (Frontend)
- No dead code
- No commented old code
- No circular dependencies
- Import order enforced:
  1. React
  2. External libs
  3. App aliases
  4. Relative imports
  5. Types
- ESLint + Prettier must pass
- Husky pre-commit checks required

---

## File / Folder Rules (Frontend)
- Feature-first architecture preferred
- One responsibility per folder
- No cross-feature tight coupling
- No editing generated files
- Constants, types, hooks, services must use barrel exports

---

## Forbidden (Frontend)
Codex must NEVER generate:
- `any`
- `style={{ }}` inline styles — use `.styles.ts` or `.module.scss`
- raw Tailwind class strings inside `.tsx` files — they belong in `.styles.ts`
- `<style>` tags inside component files
- global CSS imported from a component — only CSS modules
- raw fetch in components
- toast in components
- hardcoded colors
- business logic in pages
- API calls in UI
- array index keys
- clickable divs
- localStorage auth token storage
- useEffect data fetching
- duplicate state
- direct DTO usage in UI
- monolithic components / hooks / services beyond the line limits in the Modularization Rules

---

# Backend Standards (PydanticAI)

## Agent Architecture
- Every agent lives in `packages/agents/<name>/`
- Required files: `agent.py · schemas.py · prompts.py · runners.py`
- Optional: `tools.py · stages/`
- `agent.py` — singleton factory via `get_<name>_agent()`
- `schemas.py` — ALL Pydantic models for that agent (input DTOs, output types, session state)
- `prompts.py` — system prompt + any extraction/template prompts as module-level constants
- `runners.py` — thin orchestrator; delegates to `stages/` for complex state machines
- `tools.py` — `@agent.tool` decorated functions only

## PydanticAI Rules
- Use `pydantic_ai.Agent` with explicit `output_type` — never untyped
- Agent output must be a `BaseModel` subclass — never `str` or `dict`
- Tools declared as `async def tool_name(ctx: RunContext[DepsT], ...) -> ...`
- System prompt is a module-level `str` constant in `prompts.py`
- Agent is a module-level singleton — never recreated per request
- Use `agent.run(prompt, message_history=history)` for stateful conversations
- Use `agent.run_stream(prompt)` for streaming — always inside `async with`
- Handle `ModelHTTPError` and `UnexpectedModelBehavior` explicitly in runners

## API Layer
- Routes live in `apps/api/routes/v1/routers/<name>.py`
- `apps/api/routes/routes.py` — top-level router (includes `/health` + v1)
- `apps/api/routes/v1/routes.py` — aggregates all v1 routers
- Route files only: parse request → call service/runner → return response
- No business logic in routes
- All routes use `response_model=` explicitly
- Wrap every route body in `logfire.span()`

## Common / Shared
- `packages/common/schemas/api_response.py` — `APIResponse[T]` generic wrapper
- `packages/common/services/api_response.py` — `success_response()` / `error_response()` helpers
- All API responses wrapped in `APIResponse`

## Exception Handling
- Typed exceptions in `packages/handlers/exceptions.py`
- FastAPI exception handlers in `packages/handlers/http_handlers.py`
- Handlers registered in `main.py` at startup
- Never raise generic `Exception` — use typed subclasses
- Never catch and swallow exceptions silently

## Repository Pattern
- Data access lives in `packages/repositories/<name>_repository.py`
- Repository class with async methods only
- Never call `SessionLocal` directly from routes or runners
- Repository injected via FastAPI `Depends()`

## Settings
- All config via `packages/config/settings.py` (Pydantic `BaseSettings`)
- `get_settings()` cached with `@lru_cache`
- No hardcoded URLs, ports, or credentials anywhere
- Secret values use `SecretStr`

## Logging
- Use `logfire` everywhere — never `print`, `logging`, or `console.*`
- Every agent run wrapped in `logfire.span()`
- Every external API call wrapped in `logfire.span()`
- Structured fields: `session_id`, `user_id`, `request_id` in every span
- Use `@log_agent_run("agent_name")` decorator on runner entry points

## Database
- SQLAlchemy async engine only (`create_async_engine`)
- All ORM models in `packages/db/models.py` (shared) or agent-specific `entities/`
- Migrations via raw SQL or Alembic — never `Base.metadata.create_all` in production
- Use `text()` for raw SQL queries — never string concatenation

## Type Safety
- No `dict[str, Any]` in public function signatures — use typed Pydantic models
- No untyped `list` or `tuple` — always parameterized
- `model_dump()` only at API boundaries — pass model objects internally
- Enums for all discriminated values — never bare strings

## Forbidden (Backend)
Codex must NEVER generate:
- `dict[str, Any]` as a function return type
- Untyped agent (`Agent` without `output_type`)
- Raw `print()` or `logging.*` — use logfire
- Business logic in route handlers
- Direct DB access outside repositories
- `except Exception: pass` (silent catch)
- Hardcoded credentials or URLs
- Sync DB calls inside async functions
