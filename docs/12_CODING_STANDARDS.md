# Coding Standards

These standards govern implementation style; they do not redefine business behavior.

## Python

- Python 3.11+.
- Prefer small modules with explicit responsibilities.
- Use type hints for public service/domain boundaries and non-obvious values.
- Avoid catch-all `except Exception` unless converting/logging at a well-defined boundary and re-raising/returning a safe error.
- Avoid module-level mutable global business state.
- Use UTC internally; convert for display at the application edge.

## Flask architecture

- Prefer application-factory/configuration patterns when the bootstrap task establishes them.
- Keep routes/controllers thin: parse/validate/authenticate/authorize, call services, format response.
- Business invariants belong in services/transactions, not scattered across templates/routes.
- SQLAlchemy models represent persistence; do not hide complex business workflows in model event magic.
- Session-authenticated Web/AJAX and JWT REST API must remain distinct as specified.

## Database

- SQL Server is canonical.
- Use migrations for schema evolution.
- Respect documented FK/delete semantics and `ROWVERSION`/optimistic concurrency.
- Use database constraints for structural invariants, transactions/locking for race-sensitive invariants, and service/auth layers for workflow/authorization.
- Avoid N+1 queries and unbounded result loading; paginate/filter/sort server-side.

## HTML/Jinja/JavaScript

- Escape untrusted output by default.
- Sanitize rich/AI-generated content according to security specification.
- Preserve CSRF on state-changing session requests.
- Use accessible labels, keyboard behavior, focus handling and status messages.
- Search input is debounced; Assessment autosave follows dedicated algorithms rather than generic form submission logic.

## Errors and logging

- Use the documented API error model.
- Do not expose stack traces or secrets to clients.
- Include correlation/request IDs in operational logs where available.
- Never log passwords, tokens, API keys or unnecessary student answer/AI raw content.

## Testing

- Every bug fix should add/adjust a regression test when reasonably possible.
- Critical business rules require tests traceable to the specification.
- Concurrency/idempotency rules require race/retry coverage, not only single-request tests.

## Formatting and tools

- Ruff is the baseline Python linter/formatter check.
- Mypy is the baseline type-checking tool where applicable.
- Pytest is the baseline test runner.
- Do not change tooling solely for preference without repository-level rationale.
