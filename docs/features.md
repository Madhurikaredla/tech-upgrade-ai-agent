# Features Used

This document covers the key AI/platform features used in this project — what they are, why we use them, and where they appear in the codebase.

---

## 1. LLM (Large Language Model)

### What it is
A large language model processes natural language input and generates structured output. We do not call OpenAI/Gemini directly — we use **PydanticAI** as the agent framework, which handles prompt construction, structured output parsing, and retry logic.

### What we use it for
The LLM powers the **COLLECTING stage** only. It receives the admin's message plus the current partial program DTO and extracts structured field values from natural language.

**Example:**  
Admin says: `"HDB, online via Zoom, June 15–17 2026, 100 seats, ₹5000"`  
LLM extracts: `{ name, mode_of_operation: ONLINE, starts_at, ends_at, total_seats, base_price }`

### Multi-provider support
The model factory (`packages/config/model_factory.py`) auto-selects the provider based on which API key is present:

| Provider | Model | Key |
|----------|-------|-----|
| Azure OpenAI | any deployment | `AZURE_OPENAI_MODEL_ENDPOINT` + `AZURE_OPENAI_MODEL_KEY` |
| Google Gemini | `gemini-2.5-flash` (default) | `GOOGLE_API_KEY` |
| Groq | `qwen/qwen3-32b` (default) | `GROQ_API_KEY` |
| Anthropic Claude | configurable | `ANTHROPIC_API_KEY` |

Priority: Azure → Gemini → Groq → Anthropic

### Where in the code
- Agent definition: [`packages/agents/program_config/agent.py`](../packages/agents/program_config/agent.py)
- Model factory: [`packages/config/model_factory.py`](../packages/config/model_factory.py)
- Extraction call: [`packages/agents/program_config/stages/collecting.py`](../packages/agents/program_config/stages/collecting.py) → `run_extraction()`
- Output schema: [`packages/agents/program_config/schemas.py`](../packages/agents/program_config/schemas.py) → `ProgramConfigTurn`, `ExtractedFields`

---

## 2. Agents vs Chatbots

### The difference
A **chatbot** only generates text replies — it has no ability to take actions or produce structured data. An **agent** can use tools, produce structured output, and drive real-world side effects (e.g. create a record in a database).

### How this project uses an agent
This project is an **agent**, not a chatbot:

- The LLM outputs a **typed Pydantic model** (`ProgramConfigTurn`) — not raw text
- Field extraction results are merged into a `CreateProgramDto` that drives API calls
- The agent **creates programs**, **attaches forms**, and **publishes** via NestJS APIs
- A deterministic **state machine** controls stage transitions — the LLM only handles natural language extraction, not control flow

```
Chatbot: user message → LLM → text reply

Agent:   user message → LLM → structured fields
                           → merge into DTO
                           → state machine checks completeness
                           → API calls to create/publish program
                           → structured reply back to user
```

### Where in the code
- Runner (state machine): [`packages/agents/program_config/runners.py`](../packages/agents/program_config/runners.py)
- Stage handlers: [`packages/agents/program_config/stages/`](../packages/agents/program_config/stages/)
- API calls: [`packages/agents/program_config/api_client.py`](../packages/agents/program_config/api_client.py)

---

## 3. Python Environment Management with `uv`

### What it is
`uv` is a fast Python package manager and virtual environment tool (replaces pip + virtualenv). It reads `pyproject.toml` and manages a deterministic `.venv/`.

### Why we use it
- Significantly faster than pip for dependency resolution
- Single command (`uv sync`) installs all dependencies from the lockfile
- Works with standard `pyproject.toml` — no special config needed

### How to use it
```bash
uv sync                     # install all deps from pyproject.toml
uv add <package>            # add a new dependency
uv run pytest               # run a command in the venv
uv run uvicorn apps.api.main:app --reload
```

### Python version
Requires Python 3.11+. Specified in `pyproject.toml`:
```toml
[project]
requires-python = ">=3.11"
```

---

## 4. RAG — Retrieval-Augmented Generation

### What it is
RAG = fetch relevant data from a store, then include it in the LLM prompt. This grounds the model's output in real facts rather than hallucinated ones.

### How this project uses it
We use a lightweight form of RAG called **DB Lookup**:

1. When the admin confirms a program type (e.g. "HDB"), the system queries the database for that type's configuration (default fields, workflow_id, etc.)
2. These retrieved values are injected into the LLM extraction prompt
3. The agent's replies and field defaults are grounded in the retrieved config — not hallucinated

**Example retrieval → prompt injection flow:**
```
Admin: "Create an HDB program"
  → normalize_admin_type("HDB") → "HDB"
  → get_program_type_config("HDB") → fetches from DB
  → apply_type_config_to_dto() → sets type_id, workflow_id, default fields
  → EXTRACTION_PROMPT includes partial_dto_json with retrieved values
  → LLM sees real type config, not a guess
```

### Where in the code
- DB lookup: [`packages/agents/program_config/db_lookup.py`](../packages/agents/program_config/db_lookup.py)
- Type announcement + config application: [`packages/agents/program_config/stages/type_announcement.py`](../packages/agents/program_config/stages/type_announcement.py)
- Session-level data retrieval: [`packages/agents/program_config/repository.py`](../packages/agents/program_config/repository.py)

---

## 5. MCP / Tool Use

### What it is
**MCP (Model Context Protocol)** is an open protocol that lets LLMs call external tools in a standardized way. PydanticAI's agent framework supports tool use natively.

### How this project uses it
The analysis agent (`packages/agents/analysis/`) exposes tools the LLM can call during analysis tasks — defined in `tools.py`. The program config agent uses PydanticAI's **structured output** mode (via tool calling internally) rather than explicit tool use, because the extraction output is a fully typed Pydantic model.

PydanticAI uses tool-calling under the hood to produce structured output: the model "calls" a special function whose argument schema matches `ProgramConfigTurn`. This is why replaying `message_history` to Gemini breaks (consecutive tool-call turns) — we embed conversation context in the prompt instead.

### Where in the code
- Analysis tools: [`packages/agents/analysis/tools.py`](../packages/agents/analysis/tools.py)
- Agent definitions: [`packages/agents/analysis/agent.py`](../packages/agents/analysis/agent.py), [`packages/agents/program_config/agent.py`](../packages/agents/program_config/agent.py)

---

## 6. Structured Output (Pydantic + LLM)

### What it is
Instead of parsing free-text LLM responses with regex or string matching, we define a Pydantic model and instruct the LLM to fill it. The framework enforces type safety at the boundary.

### How this project uses it
Every agent call returns a fully validated `ProgramConfigTurn` object:

```python
class ProgramConfigTurn(BaseModel):
    reply: str                              # natural language reply to admin
    extracted_fields: ExtractedFields       # only fields mentioned this turn
    all_required_collected: bool            # agent's self-assessment
```

`ExtractedFields` has 40+ typed fields (dates as `str | None`, enums for mode, etc.). Fields not mentioned in the message default to `None` and are excluded from the DTO merge via `model_dump(exclude_none=True)`.

### Why it matters
- No parsing fragility — Pydantic validates the LLM output, not string matching
- Safe partial merging — only explicitly extracted fields overwrite session state
- Type safety flows all the way to the NestJS API call

---

## 7. Observability with Logfire

### What it is
[Logfire](https://logfire.pydantic.dev) is a structured observability platform built by the Pydantic team. It provides distributed tracing, structured logging, and dashboards.

### How this project uses it
- Every HTTP request is wrapped in a `logfire.span("http.request", ...)`
- Every agent run is wrapped in `log_agent_run("program_config")` decorator
- Key business events are logged with `logfire.info(...)` and `logfire.warning(...)`
- FastAPI is auto-instrumented via `logfire.instrument_fastapi(app)` at startup
- Request ID and User ID flow through all spans via ContextVars

### What gets traced
| Event | Span name |
|-------|-----------|
| Every HTTP request | `http.request` |
| Agent run | `agent_run:program_config` |
| Stage dispatch | `program_config.chat` |
| Field extraction | `extraction.fields_extracted` |
| Type announcement | `program_config.type_announcement` |
| NestJS API calls | `nestjs.auth_post`, etc. |

### Where in the code
- Setup: [`packages/logging/setup.py`](../packages/logging/setup.py)
- Context vars: [`packages/logging/context.py`](../packages/logging/context.py)
- Decorators: [`packages/logging/decorators.py`](../packages/logging/decorators.py)
- Middleware: [`apps/api/middleware/logging.py`](../apps/api/middleware/logging.py)
