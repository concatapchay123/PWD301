# TASK-025 — Dashboards, Learning Analytics & Performance Optimization Engine

**Status:** COMPLETED  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-024  
**Completed Date:** 2026-09-10  

---

## Goal
Implement the **Dashboards, Learning Analytics & Performance Optimization Engine** for PWD301:
1. **Analytics Engine Service (`src/pwd301/services/analytics_service.py`)**:
   - High-performance database-level aggregations (`func.count`, `func.avg`, `case`, `func.coalesce`, `group_by`) avoiding $N+1$ table scans.
   - `get_admin_system_overview(actor: User, session: Session) -> dict[str, Any]`: Total counts of users, courses by status, enrollments by status, attempts, completed lessons, and storage/audit metrics.
   - `get_instructor_overview_analytics(actor: User, session: Session) -> dict[str, Any]`: Instructor-managed courses, total/active students, pending submissions requiring grading, and quick course performance summaries.
   - `get_instructor_course_analytics(actor: User, course_id: str, session: Session) -> dict[str, Any]`: Course-level deep dive with enrollment statistics, completion rates, average scores, 4-bucket score distribution (`<50%`, `50-69%`, `70-84%`, `85-100%`), and per-assessment performance metrics.
   - `get_student_learning_overview(actor: User, session: Session) -> dict[str, Any]`: Personal student learning metrics, active/completed enrollments, upcoming assessments with server-authoritative deadlines, and released results.
   - Zero-division resilience across all 0-student, 0-submission, 0-course states.
   - Score release policy enforcement (`ScoreReleasePolicyError` rules for hidden/unreleased assessment scores).
2. **ADR-002 Zero Internal PK Leakage**:
   - 100% public UUID identifiers (`course_id`, `student_id`, `assessment_id`, `attempt_id`).
   - Zero internal BIGINT PKs exposed in any responses or queries.
3. **Security & IDOR Isolation**:
   - Strict resource-level authorization: Instructor A cannot inspect Instructor B's course analytics (HTTP 403 `FORBIDDEN`).
   - Student isolation: strictly own personal data visible; student attempts to access instructor/admin analytics rejected with 403 `FORBIDDEN`.
   - Admin platform-wide oversight.
   - Fail-closed unauthenticated access (HTTP 401 `UNAUTHORIZED`).
4. **Endpoints Connected**:
   - Admin: `GET /admin/dashboard` (Web) & `GET /api/admin/analytics/overview` (REST API)
   - Instructor: `GET /instructor/dashboard` (Web), `GET /instructor/courses/<course_id>/analytics` (Web/JSON), & `GET /api/courses/<course_id>/analytics` (REST API)
   - Student: `GET /student/dashboard` (Web) & `GET /api/student/analytics/overview` (REST API)

---

## Source-of-Truth Documents Consulted
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero PK Leakage, CSRF protection)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/08_ASSESSMENT_ENGINE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/09_SCORING_GRADING_FEEDBACK.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/11_REPORTING_LEARNING_ANALYTICS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/01_SECURITY_MODEL.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `docs/decisions/ADR-002-database-identifiers.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/002_courses_enrollments.sql`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/004_attempts_regrades.sql`
- `frontend-preview/` (`views/dashboard.js`, `views/course_analytics.js`, `components.js`, `app.css`)


