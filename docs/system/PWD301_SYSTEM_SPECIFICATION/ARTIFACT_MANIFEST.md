# Artifact Manifest — Live Repository Layout

This manifest describes the **deduplicated live repository** version of `PWD301_SYSTEM_SPECIFICATION`.

> The original standalone ZIP embedded a full Database Architecture snapshot plus a duplicate SQL copy so that it could be self-contained. In the live repository those copies are intentionally removed. The canonical database source is `docs/database/PWD301_DATABASE_ARCHITECTURE/`.

| Path | Type | Domain | Status |
|---|---|---|---|
| `00_MASTER_SYSTEM_SPEC.md` | Markdown | root documentation | REVIEWED |
| `01_PRODUCT_SCOPE_AND_GOALS.md` | Markdown | root documentation | PRESENT |
| `02_GLOSSARY_AND_TERMINOLOGY.md` | Markdown | root documentation | PRESENT |
| `03_ACTORS_AND_PERMISSIONS.md` | Markdown | root documentation | PRESENT |
| `04_SYSTEM_ARCHITECTURE.md` | Markdown | root documentation | PRESENT |
| `ARTIFACT_MANIFEST.md` | Markdown | root documentation | PRESENT |
| `CODING_AGENT_START_HERE.md` | Markdown | root documentation | REVIEWED |
| `DECISION_INVENTORY.md` | Markdown | root documentation | PRESENT |
| `FINAL_SYSTEM_REVIEW.md` | Markdown | root documentation | REVIEWED |
| `OPEN_ISSUES.md` | Markdown | root documentation | REVIEWED |
| `README.md` | Markdown | root documentation | REVIEWED |
| `SOURCE_INVENTORY.md` | Markdown | root documentation | PRESENT |
| `algorithms/01_COURSE_PROGRESS_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/02_LESSON_COMPLETION_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/03_PREREQUISITE_EVALUATION.md` | Markdown | algorithms | PRESENT |
| `algorithms/04_QUESTION_SELECTION_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/05_BLUEPRINT_GENERATION_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/06_ASSESSMENT_DEADLINE_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/07_ATTEMPT_LEASE_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/08_AUTOSAVE_AND_OFFLINE_RECONCILIATION.md` | Markdown | algorithms | PRESENT |
| `algorithms/09_SUBMISSION_IDEMPOTENCY.md` | Markdown | algorithms | PRESENT |
| `algorithms/10_GRADING_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/11_REGRADING_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/12_FILE_DEDUPLICATION.md` | Markdown | algorithms | PRESENT |
| `algorithms/13_RETENTION_CLEANUP_ALGORITHM.md` | Markdown | algorithms | PRESENT |
| `algorithms/14_COURSE_RECOMMENDATION_RULES.md` | Markdown | algorithms | PRESENT |
| `api/01_API_ARCHITECTURE.md` | Markdown | api | PRESENT |
| `api/02_ENDPOINT_CATALOG.md` | Markdown | api | PRESENT |
| `api/03_AUTH_API.md` | Markdown | api | PRESENT |
| `api/04_COURSE_API.md` | Markdown | api | PRESENT |
| `api/05_ENROLLMENT_PROGRESS_API.md` | Markdown | api | PRESENT |
| `api/06_QUESTION_BANK_API.md` | Markdown | api | PRESENT |
| `api/07_ASSESSMENT_API.md` | Markdown | api | PRESENT |
| `api/08_ATTEMPT_API.md` | Markdown | api | PRESENT |
| `api/09_FILE_IMPORT_API.md` | Markdown | api | PRESENT |
| `api/10_AI_API.md` | Markdown | api | PRESENT |
| `api/11_NOTIFICATION_API.md` | Markdown | api | PRESENT |
| `api/12_ADMIN_API.md` | Markdown | api | PRESENT |
| `api/13_REQUEST_RESPONSE_CONTRACTS.md` | Markdown | api | PRESENT |
| `api/14_ERROR_MODEL.md` | Markdown | api | PRESENT |
| `api/15_API_AUTHORIZATION_MATRIX.md` | Markdown | api | PRESENT |
| `authentication/01_AUTHENTICATION_ARCHITECTURE.md` | Markdown | authentication | PRESENT |
| `authentication/02_SESSION_AUTHENTICATION.md` | Markdown | authentication | PRESENT |
| `authentication/03_JWT_AUTHENTICATION.md` | Markdown | authentication | PRESENT |
| `authentication/04_EMAIL_VERIFICATION.md` | Markdown | authentication | PRESENT |
| `authentication/05_PASSWORD_AND_REAUTHENTICATION.md` | Markdown | authentication | PRESENT |
| `authentication/06_SESSION_TOKEN_REVOCATION.md` | Markdown | authentication | PRESENT |
| `authentication/07_AUTH_SECURITY_REQUIREMENTS.md` | Markdown | authentication | PRESENT |
| `authorization/01_RBAC_MODEL.md` | Markdown | authorization | PRESENT |
| `authorization/02_PERMISSION_MATRIX.md` | Markdown | authorization | PRESENT |
| `authorization/03_RESOURCE_AUTHORIZATION_RULES.md` | Markdown | authorization | PRESENT |
| `authorization/04_ADMIN_PERMISSION_RULES.md` | Markdown | authorization | PRESENT |
| `authorization/05_IDOR_PREVENTION.md` | Markdown | authorization | PRESENT |
| `backend/01_BACKEND_ARCHITECTURE.md` | Markdown | backend | PRESENT |
| `backend/02_MODULE_RESPONSIBILITIES.md` | Markdown | backend | PRESENT |
| `backend/03_SERVICE_LAYER_RULES.md` | Markdown | backend | PRESENT |
| `backend/04_TRANSACTION_BOUNDARIES.md` | Markdown | backend | PRESENT |
| `backend/05_BACKGROUND_JOBS.md` | Markdown | backend | PRESENT |
| `backend/06_IDEMPOTENCY_AND_RETRY.md` | Markdown | backend | PRESENT |
| `backend/07_CONCURRENCY_CONTROL.md` | Markdown | backend | PRESENT |
| `backend/08_ERROR_HANDLING.md` | Markdown | backend | PRESENT |
| `business/01_BUSINESS_RULE_CATALOG.md` | Markdown | business | PRESENT |
| `business/02_USER_ACCOUNT_LIFECYCLE.md` | Markdown | business | PRESENT |
| `business/03_COURSE_MANAGEMENT.md` | Markdown | business | PRESENT |
| `business/04_LESSON_AND_PROGRESS.md` | Markdown | business | PRESENT |
| `business/05_ENROLLMENT_AND_PREREQUISITES.md` | Markdown | business | PRESENT |
| `business/06_QUESTION_BANK.md` | Markdown | business | PRESENT |
| `business/07_QUESTION_VERSIONING_AND_CORRECTION.md` | Markdown | business | PRESENT |
| `business/08_ASSESSMENT_ENGINE.md` | Markdown | business | PRESENT |
| `business/09_ASSESSMENT_ATTEMPT.md` | Markdown | business | PRESENT |
| `business/10_GRADING_AND_REGRADING.md` | Markdown | business | PRESENT |
| `business/11_FILE_MANAGEMENT.md` | Markdown | business | PRESENT |
| `business/12_DOCX_PDF_IMPORT.md` | Markdown | business | PRESENT |
| `business/13_AI_GEMINI_RAG.md` | Markdown | business | PRESENT |
| `business/14_NOTIFICATION_AND_EMAIL.md` | Markdown | business | PRESENT |
| `business/15_AUDIT_AND_ADMIN_ACTIONS.md` | Markdown | business | PRESENT |
| `business/16_DATA_LIFECYCLE_RETENTION.md` | Markdown | business | PRESENT |
| `business/17_MAJOR_FEATURE_SPECIFICATIONS.md` | Markdown | business | PRESENT |
| `database/DATABASE_CONVENTIONS.md` | Markdown | database | PRESENT |
| `database/DATABASE_INTEGRITY_TEST_PLAN.md` | Markdown | database | PRESENT |
| `database/DATABASE_INVARIANTS.md` | Markdown | database | PRESENT |
| `database/DATA_DICTIONARY.md` | Markdown | database | PRESENT |
| `database/ERD.md` | Markdown | database | PRESENT |
| `database/INDEX_STRATEGY.md` | Markdown | database | PRESENT |
| `database/MIGRATION_STRATEGY.md` | Markdown | database | PRESENT |
| `database/README.md` | Markdown | database | PRESENT |
| `database/RETENTION_MATRIX.md` | Markdown | database | PRESENT |
| `frontend/01_FRONTEND_INFORMATION_ARCHITECTURE.md` | Markdown | frontend | PRESENT |
| `frontend/02_STUDENT_UI_FLOWS.md` | Markdown | frontend | PRESENT |
| `frontend/03_INSTRUCTOR_UI_FLOWS.md` | Markdown | frontend | PRESENT |
| `frontend/04_ADMIN_UI_FLOWS.md` | Markdown | frontend | PRESENT |
| `frontend/05_AJAX_INTERACTION_RULES.md` | Markdown | frontend | PRESENT |
| `frontend/06_FORM_VALIDATION.md` | Markdown | frontend | PRESENT |
| `frontend/07_LOADING_ERROR_EMPTY_STATES.md` | Markdown | frontend | PRESENT |
| `frontend/08_ACCESSIBILITY_REQUIREMENTS.md` | Markdown | frontend | PRESENT |
| `implementation/01_PROJECT_STRUCTURE.md` | Markdown | implementation | PRESENT |
| `implementation/02_IMPLEMENTATION_ORDER.md` | Markdown | implementation | PRESENT |
| `implementation/03_MODULE_DEPENDENCY_MAP.md` | Markdown | implementation | PRESENT |
| `implementation/04_CODING_AGENT_GUIDE.md` | Markdown | implementation | PRESENT |
| `implementation/05_DEFINITION_OF_DONE.md` | Markdown | implementation | PRESENT |
| `implementation/06_NON_NEGOTIABLE_INVARIANTS.md` | Markdown | implementation | PRESENT |
| `implementation/07_MIGRATION_AND_SEED_PLAN.md` | Markdown | implementation | PRESENT |
| `implementation/08_IMPLEMENTATION_CHECKLIST.md` | Markdown | implementation | PRESENT |
| `operations/01_DOCKER_AND_ENVIRONMENT.md` | Markdown | operations | PRESENT |
| `operations/02_CONFIGURATION.md` | Markdown | operations | PRESENT |
| `operations/03_SECRET_MANAGEMENT.md` | Markdown | operations | PRESENT |
| `operations/04_DATABASE_BACKUP_RESTORE.md` | Markdown | operations | PRESENT |
| `operations/05_LOGGING_AND_MONITORING.md` | Markdown | operations | PRESENT |
| `operations/06_SYSTEM_HEALTH.md` | Markdown | operations | PRESENT |
| `operations/07_STORAGE_MANAGEMENT.md` | Markdown | operations | PRESENT |
| `operations/08_FAILURE_RECOVERY.md` | Markdown | operations | PRESENT |
| `security/01_THREAT_MODEL.md` | Markdown | security | PRESENT |
| `security/02_SECURITY_REQUIREMENTS.md` | Markdown | security | PRESENT |
| `security/03_AUTHENTICATION_SECURITY.md` | Markdown | security | PRESENT |
| `security/04_AUTHORIZATION_SECURITY.md` | Markdown | security | PRESENT |
| `security/05_FILE_UPLOAD_SECURITY.md` | Markdown | security | PRESENT |
| `security/06_AI_RAG_SECURITY.md` | Markdown | security | PRESENT |
| `security/07_AUDIT_SECURITY.md` | Markdown | security | PRESENT |
| `security/08_WEB_SECURITY.md` | Markdown | security | PRESENT |
| `security/09_SECURITY_TEST_PLAN.md` | Markdown | security | PRESENT |
| `state-machines/ASSESSMENT_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `state-machines/ATTEMPT_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `state-machines/COURSE_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `state-machines/ENROLLMENT_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `state-machines/FILE_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `state-machines/IMPORT_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `state-machines/KNOWLEDGE_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `state-machines/REGRADING_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `state-machines/USER_STATE_MACHINE.md` | Markdown | state-machines | PRESENT |
| `testing/01_TEST_STRATEGY.md` | Markdown | testing | PRESENT |
| `testing/02_ACCEPTANCE_CRITERIA.md` | Markdown | testing | PRESENT |
| `testing/03_BUSINESS_RULE_TEST_MATRIX.md` | Markdown | testing | PRESENT |
| `testing/04_API_TEST_PLAN.md` | Markdown | testing | PRESENT |
| `testing/05_DATABASE_TEST_PLAN.md` | Markdown | testing | PRESENT |
| `testing/06_AUTH_TEST_PLAN.md` | Markdown | testing | PRESENT |
| `testing/07_CONCURRENCY_TEST_PLAN.md` | Markdown | testing | PRESENT |
| `testing/08_SECURITY_TEST_PLAN.md` | Markdown | testing | PRESENT |
| `testing/09_FILE_IMPORT_TEST_PLAN.md` | Markdown | testing | PRESENT |
| `testing/10_AI_RAG_TEST_PLAN.md` | Markdown | testing | PRESENT |
| `testing/11_END_TO_END_SCENARIOS.md` | Markdown | testing | PRESENT |
| `traceability/API_FEATURE_TRACEABILITY.md` | Markdown | traceability | PRESENT |
| `traceability/BUSINESS_RULE_TRACEABILITY.md` | Markdown | traceability | PRESENT |
| `traceability/FEATURE_REQUIREMENT_MATRIX.md` | Markdown | traceability | PRESENT |
| `traceability/TEST_TRACEABILITY.md` | Markdown | traceability | PRESENT |
| `workflows/01_USER_ACCOUNT_WORKFLOWS.md` | Markdown | workflows | PRESENT |
| `workflows/02_COURSE_LIFECYCLE.md` | Markdown | workflows | PRESENT |
| `workflows/03_ENROLLMENT_LIFECYCLE.md` | Markdown | workflows | PRESENT |
| `workflows/04_QUESTION_LIFECYCLE.md` | Markdown | workflows | PRESENT |
| `workflows/05_ASSESSMENT_LIFECYCLE.md` | Markdown | workflows | PRESENT |
| `workflows/06_ATTEMPT_LIFECYCLE.md` | Markdown | workflows | PRESENT |
| `workflows/07_FILE_LIFECYCLE.md` | Markdown | workflows | PRESENT |
| `workflows/08_IMPORT_WORKFLOW.md` | Markdown | workflows | PRESENT |
| `workflows/09_AI_KNOWLEDGE_LIFECYCLE.md` | Markdown | workflows | PRESENT |
| `workflows/10_REGRADING_WORKFLOW.md` | Markdown | workflows | PRESENT |
| `workflows/11_NOTIFICATION_WORKFLOW.md` | Markdown | workflows | PRESENT |

## Summary

- Total System Specification files: **155**
- Markdown files: **155**
- SQL files inside System Specification: **0** (expected: 0 after deduplication)
- Other files: **0**
- Directory count (including package root): **16**
- Canonical database architecture: `docs/database/PWD301_DATABASE_ARCHITECTURE/`
- Canonical SQL Server DDL: `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/`
