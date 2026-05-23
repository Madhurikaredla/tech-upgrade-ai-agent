# Developer

This manual is for engineers contributing to the AI Platform codebase. Use it to understand the module structure, the agent stage machine, the conventions to follow when adding features, and how to keep the NestJS backend contract in sync.

## Overview

This section describes the repository layout — `packages/agents/`, `packages/common/`, `packages/handlers/`, `packages/repositories/`, `apps/api/` — and how the program config agent's stage machine (COLLECTING → TEMPLATE_SELECTION → PROGRAM_PREVIEW → PUBLISHED) maps onto the code.

## Prerequisites

This section lists what a developer needs to get the platform running locally: Python 3.11+, uv, Node.js 18+, PostgreSQL 14+, and at least one AI provider key (GOOGLE_API_KEY or GROQ_API_KEY).

## Core procedures

This section holds the numbered workflows developers follow most often: setting up the local environment, running the test suite, adding a new agent stage, and extending the NestJS API client.

## Engineering guardrails

### Bad practices to avoid

- Mixing business logic into UI pages/components or API route handlers.
- Using `any`, unsafe casts, untyped payloads, or untyped return values.
- Calling APIs directly in components (`useEffect + fetch`, raw axios/fetch in UI).
- Letting DTOs leak into UI instead of mapping to domain models.
- Duplicating the same source of truth across local state, store state, and query cache.
- Silent error handling (`catch {}` / swallowed exceptions) or surfacing raw backend errors in UI.
- Hardcoded routes, colors, URLs, credentials, or environment-specific values.
- Logging via `console.*`, `print`, or ad hoc logger usage outside the centralized observability path.
- Monolithic files that exceed module size limits and mix multiple responsibilities.
- Missing request cancellation, undefined retry behavior, and missing loading/error boundaries.

### Best standards to adopt

- Enforce strict type safety in CI (`mypy/pyright`, TypeScript strict mode, and lint checks).
- Use explicit architecture boundaries:
  - Frontend: service -> mapper -> hook -> UI.
  - Backend: route -> runner/service -> repository.
- Require explicit error taxonomy and mapping (validation, domain, infra, unknown).
- Require `APIResponse[T]` wrappers and typed schemas at every API boundary.
- Define a single-owner rule per state source:
  - Local UI state -> `useState`.
  - Shared domain state -> Zustand.
  - Server state -> React Query.
- Add request lifecycle defaults for all API clients:
  - Cancellation support.
  - Explicit retry policy.
  - Timeout policy.
- Require observability standards:
  - `logfire.span()` for routes, runners, and external calls.
  - Structured fields (`session_id`, `user_id`, `request_id`) when available.
- Add quality gates in CI/CD:
  - Lint, typecheck, tests, formatting, and import-boundary checks.
  - Block merge on failed checks.
- Add modularity constraints:
  - File size limits for components/hooks/services.
  - Single responsibility per file.
  - No cross-feature tight coupling.
- Add release-readiness checks:
  - Accessibility baseline.
  - Dark-mode parity.
  - Error and loading boundary coverage on async screens.
- Add performance guardrails:
  - Route/code splitting for non-critical pages.
  - Virtualize list views above agreed thresholds.
  - Debounce high-frequency search/filter inputs.
- Add security guardrails:
  - No auth token storage in `localStorage`.
  - Secret/PII redaction in logs.
  - Dependency scanning in CI.
- Add testing policy by layer:
  - Hooks/services -> unit tests.
  - Pages -> integration tests.
  - Critical user flows -> end-to-end checks.

### Definition of done (required)

- Architecture contract is preserved (`service -> mapper -> hook -> UI`, `route -> service/runner -> repository`).
- Type safety passes with no `any`/unsafe cast regressions in changed code.
- Error handling maps to taxonomy (`validation`, `domain`, `infra`, `unknown`).
- Async flows include cancellation behavior and explicit retry/timeout policy where relevant.
- Logging/observability includes structured context (`session_id`, `user_id`, `request_id`) where available.
- Tests are added/updated at the correct layer (unit/integration/e2e based on change scope).
- Lint, typecheck, and tests pass before merge.

## Reference

This section documents the module API boundaries, the APIResponse[T] wrapper contract, the versioned routes pattern under `apps/api/routes/v1/routers/`, and the NestJS endpoint contracts the platform depends on.

## Troubleshooting

This section covers common development failures — import errors from the old package locations, PydanticAI schema mismatches, NestJS enum casing bugs — and how to diagnose and fix them.

## Changelog

This section records breaking changes to the internal module API across platform releases.
