# COMPREHENSIVE REMEDIATION CHANGELOG & PATCH RECORD

All 11 identified defects were resolved directly at the root-cause level with zero temporary workarounds:

1. `src/pwd301/services/authorization_service.py`: Standardized 401/403 JSON envelope payloads with `{"success": false, "data": null}`.
2. `src/pwd301/__init__.py`: Added global `after_request` interceptor ensuring consistent 200 OK envelope wrapping across blueprints.
3. `src/pwd301/blueprints/student/routes.py`: Added canonical `/courses` alias route to resolve 404 navigation error.
4. `src/pwd301/blueprints/auth/routes.py`: Standardized 409 Conflict concurrent login response envelope with `"data": null`.
5. `src/pwd301/extensions/rate_limiter.py`: Standardized 429 Rate Limit response payload with `"success": false, "data": null`.
6. `src/pwd301/services/jwt_auth_service.py`: Standardized JWT error responses to always include `"data": null`.
7. `src/pwd301/blueprints/api_courses/routes.py`: Extended course update route decorator to accept both `PATCH` and `PUT`.
8. `src/pwd301/services/enrollment_service.py`: Added `Course.status != 'TRASH'` and `Course.deleted_at.is_(None)` filter to hide deleted courses from students.
9. `src/pwd301/blueprints/student/routes.py`: Fixed `AttributeError` on grade appeal submission by accessing `raw_score` instead of `score`, added evidence upload support.
10. `frontend/assets/js/components/video-armor.js`: Removed window outer/inner dimension comparison to allow unrestricted browser zooming during exams.
11. `frontend/assets/js/views/student.js` & `src/pwd301/services/ai_service.py`: Synchronized Octopus AI persona to strictly follow the 3 immutable phrases.
