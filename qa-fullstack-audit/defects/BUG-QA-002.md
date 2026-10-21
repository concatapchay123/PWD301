# BUG-QA-002 — Method Not Allowed (405) on PUT /api/courses/<id>

**Severity:** Low / Medium  
**Priority:** P3  
**Status:** RESOLVED & VERIFIED  
**Category:** REST API Method Conformance  
**First detected iteration:** API Exploration  
**Detected by Agent:** AGENT C (Backend & API QA Specialist)  
**Remediated by:** Senior Backend Engineer  
**Affected module:** Course REST API Blueprint  
**Affected routes:** `/api/courses/<course_id>`  
**Affected APIs:** `PUT /api/courses/<course_id>`  
**Affected roles:** INSTRUCTOR, ADMIN  
**Environment:** Production-grade Docker Container (`pwd301_web`, MSSQL 2022)  

### 1. Bug Description
The course update endpoint in `src/pwd301/blueprints/api_courses/routes.py` registered only `methods=["PATCH"]`. When REST API clients sent a standard idempotent full-entity update via HTTP `PUT /api/courses/<id>`, Flask returned HTTP 405 Method Not Allowed instead of processing the update.

### 2. Steps to Reproduce
```bash
curl -X PUT http://127.0.0.1:5000/api/courses/1 -H "Content-Type: application/json" -d '{"title": "Updated"}'
```

### 3. Expected Result
Returns HTTP 200/401/403 with updated course data or auth rejection, not 405 Method Not Allowed.

### 4. Actual Result (Before Remediation)
HTTP 405 Method Not Allowed.

### 5. Remediation Applied
In `src/pwd301/blueprints/api_courses/routes.py`:
Updated the route decorator to allow both HTTP `PATCH` and `PUT`:
```python
@api_course_bp.route("/<course_id>", methods=["PATCH", "PUT"])
@jwt_required_custom()
def update_course(course_id: str):
    ...
```

### 6. Verification Evidence
- Live probe via `curl -X PUT http://127.0.0.1:5000/api/courses/1`:
  Successfully processes route handler and returns HTTP 401 (token required) with standardized JSON envelope instead of HTTP 405.
- Verified in 20-Iteration Playwright test suite (Iteration 06 & Iteration 07).
