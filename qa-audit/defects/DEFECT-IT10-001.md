# DEFECT-IT10-001: Course Soft-Delete Route Crashes with HTTP 403 on Response Serialization

- **Defect ID:** DEFECT-IT10-001  
- **Discovered In:** Iteration 10 (TC-IT10-004)  
- **Component:** Backend REST API (`src/pwd301/blueprints/instructor/routes.py`) / Course Management  
- **Severity:** High (P1)  
- **Category:** Business Logic / Authorization Desynchronization  
- **Status:** OPEN  

---

## 1. Description
When an Instructor calls `POST /instructor/courses/<course_id>/trash` to soft-delete an eligible course (e.g., a course with no active enrolled students), the backend executes `trash_course` which successfully updates `courses.status = 'TRASH'` and `courses.deleted_at = utc_now()`. 

However, before returning the response, the route calls `return jsonify(_serialize_course(course)), 200`. In `_serialize_course(course)`, line 568 invokes `list_learning_units(actor, c.id)`. Inside `list_learning_units`, line 205 enforces `course = require_course_manager(actor, course_id)`.

Because `course.deleted_at` was just set, `can_manage_course` evaluates:
```python
if course.deleted_at is not None:
    return bool(user.is_admin)
```
Since the actor is an Instructor (not an Administrator), `can_manage_course` returns `False`, causing `require_course_manager` to raise:
`ForbiddenError: You do not have permission to manage this course.`

As a result, the request aborts with an HTTP 403 Forbidden error envelope (`code: FORBIDDEN`), despite the database mutation having succeeded. The client receives an error toast ("You do not have permission to manage this course."), leading the user to believe the deletion failed when the course was actually trashed.

---

## 2. Reproduction Steps
1. Log in as an Instructor (`instructor1@pwd301.local`).
2. Create and publish a course, or have a DRAFT/ARCHIVED course owned by the instructor.
3. Ensure no students currently have `ACTIVE` status in `enrollments`.
4. Send an authenticated HTTP POST request to `/instructor/courses/<course_id>/trash` with payload `{"reason": "Testing soft-delete"}`.
5. Observe the response: HTTP 403 Forbidden with error envelope:
```json
{
  "data": null,
  "error": {
    "code": "FORBIDDEN",
    "correlation_id": "8e18c9f133224a76861a890901508b0a",
    "field_errors": {},
    "message": "You do not have permission to manage this course."
  },
  "success": false
}
```
6. Inspect SQL Server: Query `SELECT id, status, deleted_at FROM courses WHERE public_id = ...`. The course in fact has `status = 'TRASH'` and `deleted_at` populated.

---

## 3. Stack Trace Evidence
```python
Traceback (most recent call last):
  File "/app/src/pwd301/blueprints/instructor/routes.py", line 1126, in trash_course_route
    return jsonify(_serialize_course(course)), 200
  File "/app/src/pwd301/blueprints/instructor/routes.py", line 568, in _serialize_course
    list_learning_units(actor, c.id, session=db.session)
  File "/app/src/pwd301/services/lesson_service.py", line 205, in list_learning_units
    course = require_course_manager(actor, course_id, session=sess)
  File "/app/src/pwd301/services/authorization_service.py", line 791, in require_course_manager
    raise ForbiddenError("You do not have permission to manage this course.")
pwd301.services.exceptions.ForbiddenError: You do not have permission to manage this course.
```

---

## 4. Root Cause Analysis
`_serialize_course(c)` attempts to fetch learning units for the course by calling `list_learning_units(actor, c.id)`. However, `list_learning_units` invokes `require_course_manager(actor, course_id)`. By design, `can_manage_course` locks out non-administrators from managing soft-deleted courses (`if course.deleted_at is not None: return bool(user.is_admin)`).

When a course is being serialized *within* the deletion endpoint, the course has already been flagged as deleted, creating a circular denial: the instructor was permitted to delete the course, but is immediately denied permission to serialize the deleted course.

---

## 5. Recommended Remediation
In `src/pwd301/blueprints/instructor/routes.py`, `_serialize_course` should not invoke `list_learning_units` if `c.deleted_at is not None` or `c.status == 'TRASH'`. Alternatively, `_serialize_course` can query learning units directly via `sess.query(LearningUnit).filter(...)` without re-triggering course manager authorization, or `trash_course_route` can return a standardized success envelope without full curriculum serialization:
```python
return jsonify({
    "success": True,
    "data": {
        "course_id": str(course.public_id),
        "status": course.status,
        "deleted_at": course.deleted_at.isoformat() if course.deleted_at else None,
        "message": "Khóa học đã được đưa vào thùng rác."
    },
    "error": None
}), 200
```
