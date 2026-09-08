# Implementation Roadmap

This roadmap converts the canonical implementation order into task-sized phases. `tasks/BACKLOG.md` is the execution tracker.

1. Repository & Flask foundation
2. Database models, migrations and seed baseline
3. User/account/authentication foundation
4. RBAC + resource authorization
5. Course/Lesson/Enrollment/Prerequisites/Progress
6. Question Bank + QuestionRevision
7. Assessment definition/build/publish engine
8. Attempt snapshot/timer/autosave/lease/offline/submit
9. Grading + manual essay grading + regrading
10. File storage/security + DOCX/PDF import
11. Notifications/email + audit/admin sensitive actions
12. Gemini/AI/RAG
13. Dashboards/analytics/performance
14. Security hardening and full cross-domain QA
15. Docker/deployment/demo readiness

Do not implement a later phase merely because it is interesting; follow `tasks/CURRENT.md` and dependency order.

Canonical detail: [`system/PWD301_SYSTEM_SPECIFICATION/implementation/02_IMPLEMENTATION_ORDER.md`](system/PWD301_SYSTEM_SPECIFICATION/implementation/02_IMPLEMENTATION_ORDER.md).
