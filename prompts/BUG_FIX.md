# Fix a Bug

Read `AGENTS.md` and the relevant source-of-truth rules before changing behavior.

1. Reproduce the defect or create the smallest failing regression test.
2. Identify root cause rather than patching symptoms.
3. Inspect existing code for reusable mechanisms.
4. Apply the smallest safe fix; preserve security, validation, history and compatibility.
5. Add/update regression tests.
6. Run relevant verification.
7. Report whether documentation/business behavior changed; if it would, stop and classify the conflict rather than silently altering the specification.
