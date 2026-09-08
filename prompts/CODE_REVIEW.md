# Code Review

Review the diff against `AGENTS.md`, `tasks/CURRENT.md` and canonical specification.

Prioritize correctness/security/integrity over style. Flag:

- business-rule divergence;
- missing validation/authz;
- broken historical/audit behavior;
- concurrency/idempotency races;
- unsafe migrations/cascades;
- sensitive logging;
- untested edge cases;
- unnecessary dependencies/abstractions;
- duplicated code that should reuse repository mechanisms.

Separate blockers from non-blocking suggestions. Do not invent new requirements during review.
