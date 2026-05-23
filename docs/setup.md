# Setup & Run Guide

## Prerequisites

| Tool | Version | Install |
| --- | --- | --- |
| Python | 3.11+ | [python.org](https://python.org) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| PostgreSQL | 14+ | [postgresql.org](https://postgresql.org) |
| Git | any | [git-scm.com](https://git-scm.com) |

---

## 1. Clone the Repository

```bash
git clone <repo-url>
cd ai-platform
```

---

## 2. Install Dependencies

### Backend (Python)

```bash
uv sync
```

This creates a `.venv/` and installs all packages from `pyproject.toml`.

### Frontend (Node)

```bash
cd apps/ui
npm install
cd ../..
```

Or using the Makefile:

```bash
make install
```

---

## 3. Configure Environment

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

### Required variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_platform

# At least one AI provider key (pick one)
GOOGLE_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
ANTHROPIC_API_KEY=your_anthropic_key

# Azure OpenAI (alternative — takes highest priority)
AZURE_OPENAI_MODEL_ENDPOINT=https://your-resource.openai.azure.com/openai/deployments/gpt-4o/chat/completions
AZURE_OPENAI_MODEL_KEY=your_azure_key
```

### Optional variables

```env
# App
APP_NAME=ai-platform
DEBUG=false
API_PORT=8000

# Downstream NestJS API (Infinitheism portal)
NESTJS_BASE_URL=https://api.portal.dev.divami.com

# Observability
LOGFIRE_TOKEN=your_logfire_token
```

### AI model priority

The system picks the first configured provider in this order:

```text
Azure OpenAI → Google Gemini → Groq → Anthropic
```

Default model when using Google: `gemini-2.5-flash`
Default model when using Groq: `qwen/qwen3-32b`

---

## 4. Database

```bash
take dump from infinitheism_dev db 
and the run the script file
```

The tables are auto-created on first startup via `init_db()`.

---

## 5. Run the API

```bash
# Using make
make dev

# Or directly
uv run uvicorn apps.api.main:app --reload --port 8000
```

API is available at: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

---

## 6. Run the Frontend

```bash
# Using make
make dev-ui

# Or directly
cd apps/ui && npm run dev
```

UI is available at: `http://localhost:4002`

---

## 7. Run Tests

```bash
make test
# or
uv run pytest
```

---

## 8. Run Linting / Type Checks

```bash
make lint        # ruff check + format check
make typecheck   # mypy strict mode
```

---

## Makefile Reference

| Command | What it does |
| --- | --- |
| `make install` | Install all Python + Node deps |
| `make dev` | Start API with hot-reload |
| `make dev-ui` | Start React dev server |
| `make test` | Run pytest suite |
| `make lint` | Run ruff linter |
| `make typecheck` | Run mypy |

---

## Troubleshooting

**`asyncpg` connection refused**
Make sure PostgreSQL is running: `pg_ctl status`

**`RuntimeError: No AI provider configured`**
At least one of `GOOGLE_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, or `AZURE_OPENAI_MODEL_KEY` must be set in `.env`.

**`Model not found on this provider`**
Check that `DEFAULT_MODEL` or `GROQ_MODEL` in your `.env` matches a model your API key has access to.

**Port already in use**
Change `API_PORT` in `.env` or kill the existing process: `lsof -ti:8000 | xargs kill`
