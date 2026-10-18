# 08-DEFECT REGISTRY & TRIAGE SUMMARY

This registry aggregates all defects discovered during the 20-iteration full-stack quality audit. Full defect specifications are maintained in [qa-fullstack-audit/defects/](file:///e:/PWD301/qa-fullstack-audit/defects/).

| Defect ID | Title | Severity | Priority | Status | Component | Root Cause |
|---|---|---|---|---|---|---|
| **DEFECT-AUTH-01** | Sensitive Security Verification Token Exposed Directly in REST Response | High | P1 | OPEN | API Auth (`/api/v1/auth/email-change`) | Route returns `raw_token` in HTTP response JSON instead of solely delivering via out-of-band email. |
| **DEFECT-IT10-001** | Course Soft-Delete Route Crashes with HTTP 403 on Post-Trash Serialization | High | P1 | OPEN | Instructor API (`POST /instructor/courses/<id>/trash`) | `_serialize_course` calls `require_course_manager` on entity that was just soft-deleted, raising 403 Forbidden. |
| **DEFECT-BOLA-01** | Information Disclosure / BOLA on Draft Course Lessons Outline | Medium | P2 | OPEN | Courses API (`GET /api/courses/<id>/lessons`) | Route only checks TRASH/ARCHIVED status but omits `can_view_course` check, leaking lesson metadata. |
| **DEFECT-ROUTE-01** | Duplicate Route Registration and Handler Shadowing on Admin Course Inspection | Medium | P2 | OPEN | Admin API (`GET /admin/courses/<id>`) | Duplicate `@admin_bp.route("/courses/<course_id>")` registrations at lines 155 and 514 shadow each other. |
| **DEFECT-AUTH-02** | Missing Dedicated `/auth/session` GET Endpoint | Low | P3 | OPEN | Auth Blueprint (`/auth/routes.py`) | No route handles `GET /auth/session`, forcing SPA to probe `GET /auth/login` to inspect session status. |
| **DEFECT-IT16-001** | Latency Budget Violation on `/instructor/courses` due to N+1 Queries | Medium | P2 | OPEN | Instructor API (`GET /instructor/courses`) | Un-eager-loaded relationships cause latency to exceed 500ms budget (~663ms). |
