# PWD301 Coding Agent — Repository Prompt

You are implementing the PWD301 repository.

Before changing anything:

1. Read `AGENTS.md` and obey it.
2. Read `tasks/CURRENT.md`; work only on that task unless the user explicitly changes scope.
3. Inspect current repository code and tests for reuse.
4. Read the relevant canonical System Specification and Database Architecture files.
5. Read relevant acceptance criteria/test plans.

During implementation:

- make the smallest correct change;
- reuse existing code/dependencies before adding abstractions;
- preserve validation, authorization, security, audit, accessibility, logging, concurrency and retention safeguards;
- never silently change confirmed business rules or database invariants;
- add/update tests alongside behavior;
- keep migrations safe and SQL Server compatible.

Before finishing:

- run relevant tests/lint/typecheck/build/migrations and `scripts/verify.*` where applicable;
- explicitly report any check not executed;
- report overengineering/deletion candidates and deferred `PONYTAIL` debt according to `AGENTS.md`;
- do not start the next task automatically.
