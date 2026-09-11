# PWD301 Backlog

This backlog follows the documented dependency order. IDs are repository execution IDs, not business-rule IDs.

| ID | Task | Depends on | Status |
|---|---|---|---|
| TASK-001 | Project Foundation & Flask Bootstrap | Documentation baseline | DONE |
| TASK-002 | SQLAlchemy Models + Initial Migration + Seed Baseline | TASK-001 | DONE |
| TASK-003 | User / Account / Email Verification Foundation | TASK-002 | DONE |
| TASK-004 | Session Authentication + JWT REST Authentication | TASK-003 | DONE |
| TASK-005 | RBAC + Resource/Object Authorization | TASK-004 | DONE |
| TASK-006 | Course Management + Ownership/Reassignment | TASK-005 | DONE |
| TASK-007 | Lessons + Completion Tracking | TASK-006 | DONE |
| TASK-008 | Enrollment + Capacity + Prerequisites + Re-enrollment | TASK-006,TASK-007 | DONE |
| TASK-009 | Course Progress + Completion Engine | TASK-008 | DONE |
| TASK-010 | Question Bank | TASK-006 | DONE |
| TASK-011 | QuestionRevision + Correction Rules | TASK-010 | DONE |
| TASK-012 | Assessment Builder / Blueprint / Publish Rules | TASK-011 | DONE |
| TASK-013 | AssessmentAttempt Snapshot + Server Timer | TASK-012 | DONE |
| TASK-014 | Attempt Lease + Multi-tab Takeover | TASK-013 | DONE |
| TASK-015 | Autosave + Offline Reconciliation + Idempotent Submit | TASK-013,TASK-014 | DONE |
| TASK-016 | Grading + Manual Essay Grading | TASK-015 | DONE |
| TASK-017 | Regrading + Score History | TASK-011,TASK-016 | DONE |
| TASK-018 | File Blob/Asset Storage + Authorization | TASK-005 | DONE |
| TASK-019 | File Security / Quarantine / Malware Scan | TASK-018 | DONE |
| TASK-020 | DOCX/PDF Assessment Import | TASK-011,TASK-019 | DONE |
| TASK-021 | Notifications + Email Delivery/Retry | TASK-005 | DONE |
| TASK-022 | Audit + Sensitive Admin Actions | TASK-005 | DONE |
| TASK-023 | Gemini Integration + Backend Rule Recommendation | TASK-005,TASK-009 | DONE |
| TASK-024 | RAG Knowledge Lifecycle + AI Security | TASK-019,TASK-023 | DONE |
| TASK-025 | Dashboards / Analytics / Performance | Core domains | DONE |
| TASK-026 | Backup / Restore / Operational Health | Foundation + DB | DONE |
| TASK-027 | Security Hardening + Abuse/Rate-Limit Controls | Core features | DONE |
| TASK-028 | Full E2E / Concurrency / Retention QA | All relevant features | DONE |
| TASK-029 | Docker/Deployment/Demo Readiness | TASK-028 | BACKLOG |

Do not skip dependency checks because an agent can generate code quickly.
