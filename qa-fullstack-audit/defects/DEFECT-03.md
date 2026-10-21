# DEFECT-03 — Missing Canonical /student/courses Endpoint (Returns 404)

**Severity:** Low  
**Priority:** P3  
**Status:** RESOLVED & VERIFIED  
**Category:** Routing & API Specification Gap  
**First detected iteration:** Iteration 03  
**Detected by Agent:** AGENT C  
**Remediated by:** Senior Backend Engineer  
**Affected module:** Student Blueprint  
**Affected routes:** `/student/courses`  
**Affected APIs:** `GET /student/courses`  
**Affected roles:** STUDENT  
**Environment:** Live Flask REST API Platform at `http://127.0.0.1:5000`  

### 1. Bug Description
The student blueprint registered `/student/enrollments` to list enrolled courses, but omitted the canonical REST endpoint `/student/courses`. When a client called `GET /student/courses`, the server responded with HTTP 404 Resource Not Found.

### 2. Steps to Reproduce
```bash
curl -s -b cookies.txt http://127.0.0.1:5000/student/courses
```

### 3. Expected Result
Returns HTTP 200 with enrolled courses list or an HTTP 308 redirect to `/student/enrollments`.

### 4. Actual Result (Before Remediation)
HTTP 404 Resource Not Found.

### 5. Remediation Applied
In `src/pwd301/blueprints/student/routes.py`:
Added the canonical route alias `@student_bp.route("/courses", methods=["GET"])` directly mapped to `student_list_enrollments`, returning both `courses` and `enrollments` keys in the standardized JSON envelope.

### 6. Verification Evidence
- Live probe via `curl -s -b cookies.txt http://127.0.0.1:5000/student/courses` returns HTTP 200 with `{"success": true, "data": {"courses": [...], "enrollments": [...]}, "error": null}`.
- Verified in 20-Iteration Playwright run:
  Iteration 03 (`TC-RBAC-005`) and Iteration 08 (`TC-E2E-001`) executed with 100% PASS rate.
