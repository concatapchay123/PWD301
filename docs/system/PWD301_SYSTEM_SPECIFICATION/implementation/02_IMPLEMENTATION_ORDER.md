# Implementation Order

0. Foundation/config/app factory/logging/error model.
1. SQL Server models + migrations + reference/role seed.
2. User/Auth/RBAC/object authorization.
3. Course/Lesson/Enrollment/Progress.
4. Question Bank/QuestionRevision.
5. Assessment builder/publish/blueprint.
6. Attempt snapshot/timer/lease/autosave/offline/idempotent submit.
7. Grading/history/correction/regrading.
8. File security/storage/import.
9. Notifications/email/audit/admin.
10. AI/Gemini/RAG/recommendation.
11. Dashboards/search/export/performance.
12. Backup/health/security hardening.
13. Full concurrency/security/E2E QA and demo seed.

Each phase must preserve prior tests; do not postpone authorization/audit invariants to the end.
