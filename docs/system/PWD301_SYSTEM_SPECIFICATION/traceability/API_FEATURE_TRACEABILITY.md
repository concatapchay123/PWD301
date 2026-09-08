# API Feature Traceability

The authoritative endpoint list is `../api/02_ENDPOINT_CATALOG.md`. Endpoint groups map to features as follows: Auth→AUTH/USER; Courses/Lessons→COURSE/LESSON; enroll/progress→ENROLL/PROGRESS; Questions→QBANK/QREV; Assessments→ASSESS; Attempts/Grades/Regrade→ATTEMPT/GRADE/REGRADE; Files/Imports→FILE/IMPORT; AI→AI/RAG; Notifications→NOTIFY; Admin→RBAC/AUDIT/OPS. Every write calls the corresponding service rather than mutating tables directly.
