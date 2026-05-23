# AI Platform — Program Configuration Agent

An AI-powered platform that lets admins configure and publish programs through a single conversation instead of manually filling multi-screen forms.

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| PostgreSQL | 14+ | [postgresql.org](https://www.postgresql.org/download/) |
| Git | any | [git-scm.com](https://git-scm.com/) |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Madhurikaredla/tech-upgrade-ai-agent.git
cd tech-upgrade-ai-agent
```

### 2. Install Python dependencies

```bash
make install
# or: uv sync
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
# Database (required)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ai_platform

# AI provider — at least one key is required
GOOGLE_API_KEY=AIzaSy...       # https://aistudio.google.com/app/apikey
GROQ_API_KEY=gsk_...           # https://console.groq.com (free, recommended for dev)

# NestJS backend URL
NESTJS_BASE_URL=http://localhost:3000

# JWT secret — change before going to production
JWT_SECRET_KEY=your-secret-here
```

> At least one AI provider key (`GOOGLE_API_KEY` or `GROQ_API_KEY`) is required. Everything else has a working default.

### 4. Start the database

Make sure PostgreSQL is running and the database exists:

```bash
createdb ai_platform
```

Tables are created automatically on first startup.

### 5. Start the API server

```bash
make dev
# API starts at http://localhost:8000
```

### 6. (Optional) Start the UI

```bash
make dev-ui
# UI starts at http://localhost:3001
```

---

## Environment Variables — Full Reference

### App

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_NAME` | No | `ai-platform` | Application name |
| `APP_VERSION` | No | `0.1.0` | Application version |
| `DEBUG` | No | `false` | Enable debug / hot-reload |
| `API_HOST` | No | `0.0.0.0` | API bind host |
| `API_PORT` | No | `8000` | API bind port |

### Database

| Variable       | Required | Default | Description                        |
| -------------- | -------- | ------- | ---------------------------------- |
| `DATABASE_URL` | **Yes**  | —       | Async PostgreSQL connection string |

### AI Providers (at least one required)

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | One of these | — | Google Gemini API key |
| `GROQ_API_KEY` | One of these | — | Groq API key (free tier, fast — recommended for dev) |
| `ANTHROPIC_API_KEY` | No | — | Anthropic Claude key |
| `OPENAI_API_KEY` | No | — | OpenAI key |
| `DEFAULT_MODEL` | No | `gemini-2.5-flash` | Model when `GOOGLE_API_KEY` is set |
| `GROQ_MODEL` | No | `qwen/qwen3-32b` | Model when `GROQ_API_KEY` is set |

### NestJS / Auth

| Variable | Required | Default | Description |
|---|---|---|---|
| `NESTJS_BASE_URL` | No | `http://localhost:3000` | Downstream NestJS service URL |
| `NESTJS_TIMEOUT` | No | `30.0` | Request timeout in seconds |
| `NESTJS_MAX_RETRIES` | No | `3` | Retry attempts on transient failures |
| `NESTJS_CLIENT_ID` | No | — | Service-to-service auth client ID |
| `NESTJS_CLIENT_SECRET` | No | — | Service-to-service auth secret |
| `JWT_SECRET_KEY` | No | `change-me-in-production` | JWT signing key |
| `JWT_EXPIRE_MINUTES` | No | `60` | JWT token TTL |

### Observability

| Variable | Required | Default | Description |
|---|---|---|---|
| `LOGFIRE_TOKEN` | No | — | Logfire token (leave blank to disable remote export) |
| `LOGFIRE_PROJECT_NAME` | No | `ai-platform` | Logfire project name |

### Choosing a model

| Provider | Model | Speed | Best for |
|---|---|---|---|
| Google | `gemini-2.5-flash` | Fast | Default — form extraction, conversations |
| Google | `gemini-2.5-pro` | Slower | Complex reasoning, edge cases |
| Groq | `qwen/qwen3-32b` | Very fast | Development — generous free tier |
| Groq | `meta-llama/llama-4-scout-17b-16e-instruct` | Fast | Lightweight tasks |

---

## API Endpoints

### Health check

```
GET  /health
```

### Generic AI agent (analysis / chat)

```
POST /api/v1/analyze        — synchronous analysis
POST /api/v1/prompt         — alias for /analyze
POST /api/v1/chat           — streaming SSE response
```

**Request body:**
```json
{
  "prompt": "your message here",
  "user_id": "user-123",
  "session_id": "optional-uuid"
}
```

---

### Program Configuration Agent ← main feature

```
POST /api/v1/program-config/chat
```

**Request body:**
```json
{
  "session_id": "uuid-from-first-response",
  "message": "Create an HDB program for June 2026, online via Zoom, 100 seats, ₹5000 fee",
  "user_id": "admin-123"
}
```

**Response:**
```json
{
  "session_id": "...",
  "reply": "Got it! Here's what I have so far...",
  "stage": "COLLECTING",
  "dto_preview": null,
  "form_preview": null,
  "requires_confirmation": false,
  "program_id": null,
  "success": true
}
```

#### Conversation stages

| Stage | What's happening | What admin should type |
|---|---|---|
| `COLLECTING` | Agent extracting fields, asking for missing ones | Answer the questions |
| `PROGRAM_PREVIEW` | Full config shown for review | `yes` to confirm, `edit` to change |
| `PROGRAM_CREATED` | Program saved as DRAFT | *(auto-advances to FORM_PREVIEW)* |
| `FORM_PREVIEW` | Registration form questions shown | `ok` to attach, `edit` to modify |
| `FORM_ATTACHED` | Questions attached | *(auto-advances to READY_TO_PUBLISH)* |
| `READY_TO_PUBLISH` | Final check before going live | `publish` or `keep as draft` |
| `PUBLISHED` | Program is live | *(terminal — start new session for next program)* |

#### Example conversation

```
Admin:  "Create an HDB program, June 15–20 2026, online via Zoom,
         100 seats, ₹5000 fee, registration closes June 10"

Agent:  "Got it! A few more details:
         1. What name should appear on emails sent to seekers?
         2. Should there be a waitlist if seats fill up?"

Admin:  "Emails from Infinitheism Team. Yes, enable waitlist."

Agent:  "Here's the complete program:
         ┌──────────────────────────────────┐
         │  Name    : HDB June 2026         │
         │  Mode    : Online (Zoom Meeting) │
         │  Starts  : June 15, 2026         │
         │  ...                             │
         └──────────────────────────────────┘
         Shall I create this program? (yes / edit)"

Admin:  "yes"

Agent:  "Program created (ID: 4821).
         Here's the registration form I'll attach:
           PERSONAL DETAILS
             ✓ Full Name    (required)
             ✓ Date of Birth (required)
             ...
         Want to add or remove any questions? (ok / edit)"

Admin:  "ok"

Agent:  "Type 'publish' to go live or 'keep as draft'."

Admin:  "publish"

Agent:  "✓ HDB June 2026 is now PUBLISHED."
```

---

## Interactive API Docs

Start the server first, then open:

```bash
make dev   # starts API at http://localhost:8000
```

- **Swagger UI** → [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc** → [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Development Commands

```bash
make install     # Install all dependencies
make dev         # Run API server with hot-reload (port 8000)
make dev-ui      # Run React UI (port 3001)
make test        # Run all tests
make lint        # Lint with Ruff
make format      # Auto-format with Ruff
make typecheck   # Type-check with mypy
make clean       # Remove __pycache__ and build artifacts
```

---

## Project Structure

```
ai-platform/
├── apps/
│   ├── api/
│   │   ├── main.py                    # FastAPI app factory + lifespan + middleware
│   │   ├── dependencies.py            # FastAPI Depends() factories
│   │   ├── controllers/               # HTTP handlers — parse request, call service, return response
│   │   │   ├── agent_controller.py    # POST /api/v1/analyze, /prompt, /chat
│   │   │   ├── auth_controller.py     # POST /api/v1/auth/login, /verify-otp, /resend-otp
│   │   │   ├── health_controller.py   # GET /health
│   │   │   └── program_config_controller.py  # POST /api/v1/program-config/chat + sessions
│   │   ├── services/                  # Business logic + orchestration
│   │   │   ├── agent_service.py
│   │   │   ├── auth_service.py
│   │   │   └── program_config_service.py
│   │   ├── repositories/              # Data access (re-exports from packages/repositories)
│   │   │   └── session_repository.py
│   │   ├── dto/                       # Request / response Pydantic models
│   │   │   ├── agent_dto.py
│   │   │   ├── auth_dto.py
│   │   │   ├── health_dto.py
│   │   │   └── program_config_dto.py
│   │   ├── entities/                  # Domain entity models
│   │   │   └── session_entity.py
│   │   ├── common/                    # Shared API utilities
│   │   │   └── errors.py              # nestjs_error(), service_unreachable()
│   │   ├── middleware/
│   │   │   ├── auth.py                # JWT validation
│   │   │   └── logging.py             # Request/response logging + context vars
│   │   └── routes/                    # Router registration only
│   │       ├── routes.py              # Root router (health + v1)
│   │       └── v1/
│   │           └── routes.py          # Aggregates all v1 controllers
│   └── ui/                            # React + Vite frontend (port 3001)
│
├── packages/
│   ├── agents/
│   │   ├── analysis/                  # Generic analysis agent
│   │   │   ├── agent.py               # PydanticAI agent singleton
│   │   │   ├── schemas.py             # Input / output models
│   │   │   ├── prompts.py             # System prompt constants
│   │   │   ├── runners.py             # run_analysis(), stream_analysis()
│   │   │   └── tools.py
│   │   └── program_config/            # Program configuration agent
│   │       ├── agent.py
│   │       ├── schemas.py             # SessionState, CreateProgramDto, etc.
│   │       ├── prompts.py
│   │       ├── runners.py             # run_chat() state machine
│   │       ├── rules.py               # Conditional field rules & validation
│   │       ├── templates.py           # Default form question sets
│   │       └── stages/                # Per-stage handler modules
│   ├── repositories/
│   │   └── session_repository.py      # SessionRepository (DB-backed)
│   ├── common/
│   │   └── schemas/
│   │       └── api_response.py        # APIResponse[T] generic wrapper
│   ├── handlers/
│   │   ├── exceptions.py              # Typed exception hierarchy
│   │   └── http_handlers.py           # FastAPI exception handlers
│   ├── config/
│   │   ├── settings.py                # Pydantic BaseSettings (reads .env)
│   │   └── model_factory.py           # get_model() — Google / Groq / Anthropic
│   ├── db/
│   │   ├── database.py                # Async engine + SessionLocal + init_db()
│   │   └── models.py                  # SQLAlchemy ORM models
│   ├── auth/
│   │   └── service.py                 # OTP send / verify (delegates to NestJS)
│   ├── client/
│   │   └── nestjs_client.py           # NestJS HTTP client singleton
│   ├── models/
│   │   └── input.py                   # Shared request models (PromptRequest, InputPayload)
│   └── logging/
│       ├── setup.py                   # configure_logfire()
│       ├── context.py                 # ContextVar request_id / user_id
│       └── decorators.py              # @log_agent_run()
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── .env.example                       # Environment variable template
├── pyproject.toml                     # Python dependencies & tool config
└── Makefile                           # Dev commands
```

---

## Running Tests

```bash
make test                          # Run all tests (pytest -v)

# Specific file or with coverage — use uv run directly
uv run pytest tests/unit/test_program_config_rules.py -v
uv run pytest --cov=packages --cov-report=term-missing
```

---

## Code Quality

```bash
make lint        # Check for errors and style issues (Ruff)
make format      # Auto-fix formatting in-place (Ruff)
make typecheck   # Static type checking (mypy)
```

Run all three before committing:

```bash
make lint && make format && make typecheck
```

---

## Troubleshooting

### `RuntimeError: No AI provider configured`

Add `GOOGLE_API_KEY=...` to your `.env` file, then restart:

```bash
make dev
```

### `uv: command not found`

Install uv, restart your terminal, then install dependencies:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
make install
```

### `ModuleNotFoundError` or stale `.pyc` cache

Clear build artifacts and reinstall:

```bash
make clean
make install
```

### Port 8000 already in use

Find and kill the process using the port, then restart:

```bash
# Find what's on the port
lsof -i :8000

# Kill it (replace 8000 with whichever port)
lsof -ti:8000 | xargs kill -9

# Or kill the UI port (default 5173 / 3001)
lsof -ti:5173 | xargs kill -9
lsof -ti:3001 | xargs kill -9
```

On Windows:

```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

Then restart:

```bash
make dev        # API
make dev-ui     # UI
```

Alternatively, change the port in `.env`: `API_PORT=8001`

### Linting or type errors

```bash
make lint        # See what Ruff flagged
make format      # Auto-fix formatting
make typecheck   # Run mypy
```

### NestJS connection errors in program-config agent

The program-config agent calls `NESTJS_BASE_URL` to create/publish programs. If you don't have NestJS running, the agent will work through `COLLECTING → PROGRAM_PREVIEW` but fail at the create step. Set `NESTJS_BASE_URL` to your running backend.
