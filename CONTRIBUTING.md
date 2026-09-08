# Contributing to PWD301

## Before starting

1. Read `AGENTS.md`.
2. Read `tasks/CURRENT.md`.
3. Read the relevant canonical specification and tests/acceptance criteria.
4. Inspect existing code before adding new abstractions or dependencies.

## Branching and commits

Use small task-scoped branches when working with Git, for example `task/TASK-003-auth-foundation`.
Prefer clear commits such as:

- `feat(auth): add session login service`
- `fix(attempt): reject stale autosave sequence`
- `test(enrollment): cover capacity race`
- `docs(task): close TASK-007`

Conventional-commit wording is a repository convention, not a business requirement.

## Pull-request / review expectations

A change is not ready merely because the happy path works. Review must consider:

- validation and authorization;
- migration safety;
- security and sensitive logging;
- concurrency/idempotency where relevant;
- tests and acceptance criteria;
- documentation/traceability updates when contracts change;
- whether existing code could have been reused instead.

## Database changes

Read the canonical Database Architecture first. Schema changes require a migration, appropriate tests and an explanation when the change differs from reference DDL. Never silently create a second schema source of truth.

## Secrets

Never commit `.env`, API keys, passwords, access/refresh tokens, private keys or production connection strings.

## Completion

Run `scripts/verify.ps1` on Windows or `scripts/verify.sh` on Unix-like systems and report any check that could not be run.
