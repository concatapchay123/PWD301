# DEFECT-BOLA-01: Information Disclosure / BOLA on Draft Course Lessons Outline

- **Defect ID:** DEFECT-BOLA-01
- **Component:** Course & Lesson REST API (`src/pwd301/blueprints/api_courses/routes.py`, `src/pwd301/services/lesson_service.py`)
- **Severity:** Medium (P2)
- **OWASP Classification:** API1:2023 - Broken Object Level Authorization (BOLA) / CWE-285 Improper Authorization
- **Status:** OPEN

---

## 1. Description
When retrieving course details via `GET /api/courses/<course_id>`, access control is strictly enforced by [can_view_course](file:///e:/PWD301/src/pwd301/services/authorization_service.py#L524-L553). If a course is in `DRAFT`, `SUBMITTED_FOR_REVIEW`, or `REJECTED` state, unauthenticated users or unrelated students are denied access with HTTP 404/403.

However, the dedicated lesson outline endpoint `GET /api/courses/<course_id>/lessons` implemented in [get_course_lessons_api](file:///e:/PWD301/src/pwd301/blueprints/api_courses/routes.py#L276-L288) calls [get_course_lessons](file:///e:/PWD301/src/pwd301/services/lesson_service.py#L1947-L1980) without passing the actor or verifying `can_view_course`. The service logic only checks:
```python
if course.status in ("TRASH", "ARCHIVED"):
    raise CourseNotFoundError("Course not found.")
```
As a result, any unauthenticated anonymous caller or unprivileged student can query `GET /api/courses/<course_id>/lessons` for any unpublished course (e.g. `DRAFT` or pending admin approval) and obtain the complete curriculum structure, learning unit groupings, lesson public IDs, titles, positions, and summary metadata.

---

## 2. Reproduction Steps
1. Create a new course as Instructor A: `POST /instructor/courses` with title `"Confidential Advanced Penetration Testing"` (status is `DRAFT`).
2. Create learning units and lessons under this course as Instructor A.
3. Without authenticating (or using a student JWT Bearer token), issue a GET request:
   ```http
   GET /api/courses/<draft_course_public_id>/lessons HTTP/1.1
   Host: localhost:5000
   ```
4. **Observed Result:** HTTP 200 OK with the full list of draft lessons, titles, and IDs:
   ```json
   {
     "course_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
     "lessons": [
       {
         "id": "e8293774-7294-4d89-9d5f-b52adfe5a8d1",
         "title": "Zero-Day Exploit Development",
         "position": 1
       }
     ]
   }
   ```
5. **Expected Result:** HTTP 403 Forbidden or 404 Not Found since the course is not published and the caller is neither the course owner nor an administrator.

---

## 3. Code Evidence
In [src/pwd301/blueprints/api_courses/routes.py](file:///e:/PWD301/src/pwd301/blueprints/api_courses/routes.py#L276-L288):
```python
@api_course_bp.route("/<course_id>/lessons", methods=["GET"])
def get_course_lessons_api(course_id: str) -> Response | tuple[Response, int]:
    """Retrieve public lesson summaries for an approved course."""
    lessons = get_course_lessons(course_id, session=db.session)
    return (
        jsonify(
            {
                "course_id": course_id,
                "lessons": lessons,
                "count": len(lessons),
            }
        ),
        200,
    )
```

In [src/pwd301/services/lesson_service.py](file:///e:/PWD301/src/pwd301/services/lesson_service.py#L1947-L1957):
```python
def get_course_lessons(
    course_identifier: str | int,
    session: Session | None = None,
) -> list[dict[str, Any]]:
    sess = session or db.session
    course = resolve_course(session, course_identifier)
    if course is None:
        raise CourseNotFoundError("Course not found.")
    if course.status in ("TRASH", "ARCHIVED"):
        raise CourseNotFoundError("Course not found.")
```

---

## 4. Remediation Recommendation
Update [get_course_lessons_api](file:///e:/PWD301/src/pwd301/blueprints/api_courses/routes.py#L276) and [get_course_lessons](file:///e:/PWD301/src/pwd301/services/lesson_service.py#L1947) to accept `actor: User | None` and check [can_view_course](file:///e:/PWD301/src/pwd301/services/authorization_service.py#L524):

```python
# In lesson_service.py
def get_course_lessons(
    course_identifier: str | int,
    actor: User | None = None,
    session: Session | None = None,
) -> list[dict[str, Any]]:
    sess = session or db.session
    course = resolve_course(sess, course_identifier)
    if course is None or not can_view_course(actor, course, session=sess):
        raise CourseNotFoundError("Course not found.")
    ...
```
