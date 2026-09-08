# PWD301 Backlog

This backlog follows the documented dependency order. IDs are repository execution IDs, not business-rule IDs.

| ID | Task | Depends on | Initial status |
|---|---|---|---|
| TASK-001 | Project Foundation & Flask Bootstrap | Documentation baseline | READY |
| TASK-002 | SQLAlchemy Models + Initial Migration + Seed Baseline | TASK-001 | BACKLOG |
| TASK-003 | User / Account / Email Verification Foundation | TASK-002 | BACKLOG |
| TASK-004 | Session Authentication + JWT REST Authentication | TASK-003 | BACKLOG |
| TASK-005 | RBAC + Resource/Object Authorization | TASK-004 | BACKLOG |
| TASK-006 | Course Management + Ownership/Reassignment | TASK-005 | BACKLOG |
| TASK-007 | Lessons + Completion Tracking | TASK-006 | BACKLOG |
| TASK-008 | Enrollment + Capacity + Prerequisites + Re-enrollment | TASK-006,TASK-007 | BACKLOG |
| TASK-009 | Course Progress + Completion Engine | TASK-008 | BACKLOG |
| TASK-010 | Question Bank | TASK-006 | BACKLOG |
| TASK-011 | QuestionRevision + Correction Rules | TASK-010 | BACKLOG |
| TASK-012 | Assessment Builder / Blueprint / Publish Rules | TASK-011 | BACKLOG |
| TASK-013 | AssessmentAttempt Snapshot + Server Timer | TASK-012 | BACKLOG |
| TASK-014 | Attempt Lease + Multi-tab Takeover | TASK-013 | BACKLOG |
| TASK-015 | Autosave + Offline Reconciliation + Idempotent Submit | TASK-013,TASK-014 | BACKLOG |
| TASK-016 | Grading + Manual Essay Grading | TASK-015 | BACKLOG |
| TASK-017 | Regrading + Score History | TASK-011,TASK-016 | BACKLOG |
| TASK-018 | File Blob/Asset Storage + Authorization | TASK-005 | BACKLOG |
| TASK-019 | File Security / Quarantine / Malware Scan | TASK-018 | BACKLOG |
| TASK-020 | DOCX/PDF Assessment Import | TASK-011,TASK-019 | BACKLOG |
| TASK-021 | Notifications + Email Delivery/Retry | TASK-005 | BACKLOG |
| TASK-022 | Audit + Sensitive Admin Actions | TASK-005 | BACKLOG |
| TASK-023 | Gemini Integration + Backend Rule Recommendation | TASK-005,TASK-009 | BACKLOG |
| TASK-024 | RAG Knowledge Lifecycle + AI Security | TASK-019,TASK-023 | BACKLOG |
| TASK-025 | Dashboards / Analytics / Performance | Core domains | BACKLOG |
| TASK-026 | Backup / Restore / Operational Health | Foundation + DB | BACKLOG |
| TASK-027 | Security Hardening + Abuse/Rate-Limit Controls | Core features | BACKLOG |
| TASK-028 | Full E2E / Concurrency / Retention QA | All relevant features | BACKLOG |
| TASK-029 | Docker/Deployment/Demo Readiness | TASK-028 | BACKLOG |

Do not skip dependency checks because an agent can generate code quickly.
