# DEFECT-IT10-001: Course Soft-Delete Route Crashes with HTTP 403 on Response Serialization

- **Defect ID:** DEFECT-IT10-001  
- **Component:** Backend REST API (`src/pwd301/blueprints/instructor/routes.py`) / Course Management  
- **Severity:** High (P1)  
- **Category:** Business Logic / Authorization Desynchronization  
- **Status:** VERIFIED / RESOLVED  

---

## 1. Description
When an Instructor calls `POST /instructor/courses/<course_id>/trash` to soft-delete an eligible course (e.g., a course with no active enrolled students), the backend executes `trash_course` which successfully updates `courses.status = 'TRASH'` and `courses.deleted_at = utc_now()`. 

However, before returning the response, [trash_course_route](file:///e:/PWD301/src/pwd301/blueprints/instructor/routes.py#L1118-L1128) calls:
```python
return jsonify(_serialize_course(course)), 200
```
In [_serialize_course](file:///e:/PWD301/src/pwd301/blueprints/instructor/routes.py#L568), line 568 invokes:
```python
list_learning_units(actor, c.id, session=db.session)
```
Inside [list_learning_units](file:///e:/PWD301/src/pwd301/services/lesson_service.py#L205), line 205 enforces:
```python
course = require_course_manager(actor, course_id, session=sess)
```
Because `course.deleted_at` was just populated by `trash_course`, [can_manage_course](file:///e:/PWD301/src/pwd301/services/authorization_service.py#L576) evaluates:
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
5. **Observed Result:** HTTP 403 Forbidden with error envelope:
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
  File "src/pwd301/blueprints/instructor/routes.py", line 1127, in trash_course_route
    return jsonify(_serialize_course(course)), 200
  File "src/pwd301/blueprints/instructor/routes.py", line 568, in _serialize_course
    list_learning_units(actor, c.id, session=db.session)
  File "src/pwd301/services/lesson_service.py", line 205, in list_learning_units
    course = require_course_manager(actor, course_id, session=sess)
  File "src/pwd301/services/authorization_service.py", line 791, in require_course_manager
    raise ForbiddenError("You do not have permission to manage this course.")
pwd301.services.exceptions.ForbiddenError: You do not have permission to manage this course.
```

---

## 4. Root Cause Analysis
`_serialize_course(c)` attempts to fetch learning units for the course by calling `list_learning_units(actor, c.id)`. However, `list_learning_units` invokes `require_course_manager(actor, course_id)`. By design, `can_manage_course` locks out non-administrators from managing soft-deleted courses (`if course.deleted_at is not None: return bool(user.is_admin)`).

When a course is being serialized *within* the deletion endpoint, the course has already been flagged as deleted, creating a circular denial: the instructor was permitted to delete the course, but is immediately denied permission to serialize the deleted course.

---

## 5. Recommended Remediation
In [src/pwd301/blueprints/instructor/routes.py](file:///e:/PWD301/src/pwd301/blueprints/instructor/routes.py#L1120-L1128), `trash_course_route` can return a standardized success envelope without re-invoking the full curriculum serialization:
```python
@instructor_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_course_route(course_id: str) -> Any:
    """Soft-delete a course to TRASH."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    course = trash_course(actor, course_id, reason=reason)
    return (
        jsonify({
            "success": True,
            "data": {
                "course_id": str(course.public_id),
                "status": course.status,
                "deleted_at": course.deleted_at.isoformat() if course.deleted_at else None,
                "message": "Khóa học đã được chuyển vào thùng rác thành công.",
            },
            "error": None,
        }),
        200,
    )
```


---

## 5. Remediation Verification (PASSED)
- **Implemented Fix:** In [src/pwd301/blueprints/instructor/routes.py](file:///e:/PWD301/src/pwd301/blueprints/instructor/routes.py#L1120-L1135), `trash_course_route` eliminates the post-trash call to `_serialize_course(course)`. It returns a standardized JSON envelope:
  ```json
  {
    "success": true,
    "data": {
      "course_id": str(course.public_id),
      "status": "TRASH",
      "deleted_at": course.deleted_at.isoformat() if course.deleted_at else None
    }
  }
  ```
- **Verification Evidence:** Executed in Iteration 10 of `run_fullstack_20_iterations_master.py`. Soft-delete request returned HTTP 200 with `status: TRASH`. Database confirmed `deleted_at` was populated and no HTTP 403 occurred. Result: **PASSED**.
