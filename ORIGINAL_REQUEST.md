# Original User Request

## 2026-09-11T15:27:07Z

Audit and identify all bugs, errors, security vulnerabilities, business logic violations, and test failures across the entire PWD301 codebase.

Working directory: e:\PWD301
Integrity mode: development

## Requirements

### R1. Comprehensive Static & Verification Audit
Run repository checks, linters (`ruff`, `mypy`), and the full test suite (`pytest`) to capture any existing crashes, syntax errors, type inconsistencies, or broken test assertions.

### R2. Invariant & Business Rule Conformance Audit
Verify adherence against the 73 business rules in `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` and non-negotiable invariants in `AGENTS.md` (e.g. auth splitting, assessment locking, fail-closed file security, cycle-free prerequisites).

### R3. Security & Operational Vulnerability Analysis
Inspect endpoints for authorization checks, mass assignment vulnerabilities, SQL injection, CSRF enforcement on session routes, and secret leakage.

### R4. Actionable Bug Report & Categorization
Deliver a comprehensive categorized report of all detected defects with file locations, severity levels, reproduction steps or evidence, and concrete remediation recommendations.

## Acceptance Criteria

### Automated Verification
- [ ] Pytest suite execution results documented with all failing tests identified (if any).
- [ ] Static analysis tools (`scripts/repo_check.py`, `ruff`, `mypy`) run and all errors/warnings enumerated.

### Deep Logic & Invariant Audit
- [ ] Every major subsystem (Auth, Courses/Lessons, Assessments & Grading, Files/Security, AI/RAG) audited against its specifications.
- [ ] Discrepancies between implementation and `docs/system/` or `docs/database/` explicitly listed.

### Final Deliverable
- [ ] Clear markdown audit report detailing high, medium, and low severity issues found across the codebase.
