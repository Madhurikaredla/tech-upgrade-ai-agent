## Summary

- What changed:
- Why:

## Standards Checklist (Required)

- [ ] No business logic added in UI pages/components or API routes.
- [ ] No `any`, unsafe casts, or untyped public payload/return contracts in changed code.
- [ ] Frontend changes follow `service -> mapper -> hook -> UI`.
- [ ] Backend changes follow `route -> runner/service -> repository`.
- [ ] No DTO leaks into UI; mapping to domain types is present.
- [ ] No duplicated state across local/store/query cache.
- [ ] No silent catches; errors mapped to `validation` / `domain` / `infra` / `unknown`.
- [ ] No hardcoded routes, credentials, or environment-specific secrets.
- [ ] No `console.*` / `print` logging in production paths.
- [ ] Async requests include cancellation and explicit retry/timeout strategy where applicable.
- [ ] Loading/error boundaries are handled for new async UI surfaces.
- [ ] Performance guardrails considered (splitting, debounce, virtualization where relevant).
- [ ] Security guardrails considered (token handling, PII redaction, dependency risk).

## Validation

- [ ] Unit tests updated (hooks/services/utilities where applicable).
- [ ] Integration tests updated (page/flow behavior where applicable).
- [ ] Critical flow verification completed (manual or e2e).
- [ ] Lint passes.
- [ ] Typecheck passes.
- [ ] Tests pass.

## Notes

- Risks / follow-ups:

