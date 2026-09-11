# Project: PWD301 Comprehensive Codebase Audit

## Architecture & Scope
The PWD301 project is a Flask-based Learning Management System with role-based access control (Student, Instructor, Admin), course management, lesson tracking, assessment engine with anti-cheat/locking, file storage with quarantine, and AI/RAG integration.

### Canonical Sources of Truth
1. `docs/system/PWD301_SYSTEM_SPECIFICATION/` (business rules, system architecture, non-negotiables)
2. `docs/database/PWD301_DATABASE_ARCHITECTURE/` (ERD, DDL, invariants)
3. `AGENTS.md` (operating contract, non-negotiable invariants)
4. `frontend-preview/` (canonical UI reference)

## Feature / Subsystem Inventory
| # | Subsystem / Area | Focus & Requirements | Assigned Milestone |
|---|------------------|----------------------|-------------------|
| 1 | Static Checks & Automated Tests | `scripts/repo_check.py`, `ruff`, `mypy`, `pytest` test suite | M1 |
| 2 | Auth, Session, JWT & RBAC | Business rules (BR-AUTH-*), session auth on UI, JWT on API, suspension, role combinations | M2 |
| 3 | Courses, Lessons, Prerequisites & Enrollments | Business rules (BR-CRS-*, BR-ENR-*, BR-LES-*), prerequisite acyclicity, single active enrollment | M2 |
| 4 | Assessments, Attempts & Grading | Business rules (BR-ASM-*), attempt snapshots, server-side locking after publish/start, lease takeover, autosave, idempotent submission, regrading | M3 |
| 5 | Files, Security, Quarantine & Media | Business rules (BR-FIL-*), fail-closed quarantine, < 1 GB video limit, no public paths | M3 |
| 6 | AI/RAG & Operational Audit Logging | Business rules (BR-AI-*, BR-AUD-*), RAG pre-auth filtering, 5-min ephemeral chat deletion, append-only audit, DB backup safety | M3 |
| 7 | Security Vulnerability Inspection | Object-level authorization (IDOR), mass assignment, SQLi, CSRF, credential/secret leakage | M4 |
| 8 | Synthesis & Categorized Deliverable | Synthesis of findings into high/medium/low severity report with reproduction & remediation | M5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Static & Test Verification | Run verify.ps1, repo_check.py, ruff, mypy, pytest | none | IN_PROGRESS |
| M2 | Invariants: Auth & Course Subsystems | Audit BR-AUTH, BR-CRS, BR-ENR against specs | none | IN_PROGRESS |
| M3 | Invariants: Assessment, Files, AI Subsystems | Audit BR-ASM, BR-FIL, BR-AI, BR-AUD against specs | none | IN_PROGRESS |
| M4 | Security & Operational Vulnerabilities | Inspect routes, decorators, CSRF, SQL queries, secrets | none | IN_PROGRESS |
| M5 | Final Synthesis & Bug Report | Consolidate all evidence into comprehensive deliverable | M1, M2, M3, M4 | PLANNED |
