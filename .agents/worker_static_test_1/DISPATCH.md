## 2026-09-11T15:28:44Z

You are worker_static_test_1, working in directory: e:\PWD301\.agents\worker_static_test_1.
Original user request is at: e:\PWD301\.agents\ORIGINAL_REQUEST.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Mission:
Run the full static analysis, repository checks, linters, and automated test suite on the PWD301 codebase at e:\PWD301.

Tasks to execute:
1. Check the environment and available virtual environments (e.g. e:\PWD301\.venv\Scripts\python.exe, pytest, ruff, mypy).
2. Run repository checks: `python scripts/repo_check.py` or with the virtualenv python.
3. Run linters: `ruff check .` and `mypy src tests` (or as configured in pyproject.toml / scripts/lint.ps1).
4. Run the full test suite: `pytest -v` (or `./scripts/verify.ps1` / `./scripts/test.ps1`).
5. Capture ALL output, exit codes, warnings, syntax errors, type inconsistencies, and failing tests with full failure tracebacks.
6. Write a detailed, self-contained handoff report to `e:\PWD301\.agents\worker_static_test_1\handoff.md`.
7. Once finished, use `send_message` to report completion and summarize the results back to the orchestrator.
