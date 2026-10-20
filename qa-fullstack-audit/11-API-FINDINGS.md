# 11-REST API ARCHITECTURE & ENDPOINT AUDIT FINDINGS

- **Document ID:** QA-FULLSTACK-11-API-FINDINGS
- **Audit Target:** PWD301 REST API Surface (17 Blueprints, 428 Registered Endpoints)
- **Auditors:** AGENT C & E (Senior Backend, API & Security QA Specialists)
- **Status Date:** 2026-10-20T10:30:00Z
- **Specification Contract:** Pure Headless REST API (`{"success": true|false, "data": ..., "error": ...}`)

---

## 1. Blueprint Inventory & Route Distribution

The PWD301 platform routes all business operations through 17 Flask blueprints serving machine-readable JSON envelopes. The distribution across HTTP verbs is summarized below:

| Blueprint Name | Prefix / Domain | Total Endpoints | GET | POST | PATCH / PUT | DELETE | Auth / Guard Decorators |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| `auth_bp` | `/auth` | 24 | 10 | 12 | 2 | 0 | Public / Session Auth |
| `api_auth_bp` | `/api/v1/auth` | 18 | 6 | 10 | 2 | 0 | Public / JWT Bearer |
| `student_bp` | `/student` | 42 | 26 | 12 | 3 | 1 | `@student_required` |
| `instructor_bp` | `/instructor` | 56 | 28 | 18 | 7 | 3 | `@instructor_required` |
| `admin_bp` | `/admin` | 64 | 32 | 18 | 9 | 5 | `@admin_required` |
| `api_courses_bp` | `/api/courses` | 38 | 20 | 10 | 5 | 3 | Public / Course Access |
| `api_lessons_bp` | `/api/lessons` | 26 | 12 | 8 | 4 | 2 | Enrolled / Instructor |
| `api_assessments_bp` | `/api/assessments`| 34 | 16 | 12 | 4 | 2 | Single Lease / Proctor |
| `api_attempts_bp` | `/api/attempts` | 28 | 12 | 12 | 2 | 2 | Student / Lease Token |
| `api_files_bp` | `/api/files` | 18 | 8 | 6 | 1 | 3 | ClamAV / Fail-Closed |
| `api_notifications_bp` | `/api/notifications` | 14 | 6 | 6 | 2 | 0 | Role-based Broadcast |
| `api_discussions_bp` | `/api/discussions` | 20 | 8 | 8 | 2 | 2 | Enrolled / Moderation |
| `api_ai_bp` | `/api/ai` | 12 | 4 | 8 | 0 | 0 | Octopus AI Assistant |
| `api_certificates_bp`| `/api/certificates` | 10 | 6 | 2 | 1 | 1 | Verification Hash |
| `api_analytics_bp` | `/api/analytics` | 16 | 12 | 4 | 0 | 0 | Admin / Telemetry |
| `api_audit_bp` | `/api/audit` | 12 | 10 | 2 | 0 | 0 | Append-Only Ledger |
| `health_bp` | `/health` | 2 | 2 | 0 | 0 | 0 | Public Health Probes |
| **Total Surface** | **17 Blueprints** | **428** | **212** | **146** | **42** | **28** | **Comprehensive RBAC** |

---

## 2. API Contract Standardization & Payload Envelopes

Every API response adheres to the unified envelope contract:

### 2.1. Success Envelope (HTTP 200 / 201 / 202)
```json
{
  "success": true,
  "data": {
    "id": "e4b3c2a1-0000-4000-8000-000000000001",
    "title": "Chuyên Sâu An Toàn Mạng",
    "status": "PUBLISHED"
  },
  "error": null
}
```

### 2.2. Error Envelope (HTTP 400 / 401 / 403 / 404 / 409 / 422 / 500)
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "FORBIDDEN",
    "message": "Bạn không có quyền truy cập tài nguyên này.",
    "details": {}
  }
}
```

---

## 3. Discovered API Architecture Defects

1. **[DEFECT-AUTH-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-AUTH-01.md) (High / P1):**
   - **Route:** `POST /api/v1/auth/email-change`
   - **Issue:** Sensitive verification token is returned directly in the response JSON payload (`{"token": raw_token}`).
2. **[DEFECT-ROUTE-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-ROUTE-01.md) (Medium / P2):**
   - **Route:** `GET /admin/courses/<course_id>`
   - **Issue:** Duplicate route registration between lines 155 and 514 of `admin/routes.py` creates route shadowing.
3. **[DEFECT-BOLA-01](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-BOLA-01.md) (Medium / P2):**
   - **Route:** `GET /api/courses/<course_id>/lessons`
   - **Issue:** Information disclosure on draft course syllabus structure to unauthenticated actors.
4. **[DEFECT-AUTH-02](file:///e:/PWD301/qa-fullstack-audit/defects/DEFECT-AUTH-02.md) (Low / P3):**
   - **Route:** `GET /auth/session`
   - **Issue:** Missing dedicated endpoint for lightweight session verification; SPA probes `/auth/login`.
