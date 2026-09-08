# Product Scope and Goals

## In scope
Course/Lesson management, enrollment/prerequisites/progress, Question Bank/versioning, rich Assessment engine, resumable attempts, autosave/offline reconciliation, manual essay grading, correction/regrading, secure file resources/import, LMS-scoped Gemini/RAG, notifications/email, audit, dashboards/exports, backup/health/retention.

## Required course capabilities
Flask + SQL Server + Docker, SQLAlchemy models/migrations, Flask-WTF/CSRF/server validation, Flask-Login and minimum three roles, JWT JSON REST endpoints, AJAX/Fetch dynamic behavior, Jinja inheritance/Bootstrap responsive UI, seed data, tests, Git/README and AI usage logging.

## Product goals
- Correctness and historical fairness for assessment data.
- Strong authorization boundaries with practical Admin governance.
- Recoverability from browser/network/file-worker failures.
- Traceable content corrections, grading and sensitive actions.
- Safe self-hosted operation without unnecessary distributed-system complexity.
- Documentation usable directly by coding agents.

## Explicit non-goals for MVP
No microservices, no local primary LLM, no automatic essay final grading, no public raw storage URLs, no OCR dependency for scanned PDFs unless later explicitly added, no default video transcoding requirement, no enterprise event sourcing/CQRS.
