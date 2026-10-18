# DEFECT REPORT: DEFECT-IT16-001

## 1. Defect Header
- **Defect ID:** DEFECT-IT16-001
- **Title:** Response Latency Budget Violation on Instructor Courses Endpoint due to N+1 Relational Query Cascades
- **Severity:** Medium (P2)
- **Priority:** P2
- **Component:** `src/pwd301/blueprints/instructor/routes.py` (`instructor_list_courses`)
- **Status:** OPEN
- **Discovered In:** Iteration 16 (Performance Profiling)

---

## 2. Vulnerability / Defect Summary
Calling `GET /instructor/courses` incurs an un-eager-loaded $O(N)$ query cascade across courses, learning units, enrollments, and pending change requests. The measured response latency reaches ~663.4 ms, which exceeds the system performance budget of 500 ms for standard administrative read queries.

---

## 3. Root Cause Analysis
In `src/pwd301/blueprints/instructor/routes.py`, `_serialize_course_summary(course)` is executed in a loop for each managed course:
```python
def _serialize_course_summary(course):
    return {
        "id": course.id,
        "title": course.title,
        "total_units": len(course.learning_units), # Triggers lazy SQL query
        "total_students": len(course.enrollments),  # Triggers lazy SQL query
        "pending_changes": len(course.change_requests), # Triggers lazy SQL query
    }
```
For an instructor managing 15 courses, SQLAlchemy issues 1 initial course query plus 45 secondary queries ($1 + 15 \times 3 = 46$ queries) over the PyODBC connection to SQL Server.

---

## 4. Reproduction Steps
1. Authenticate as instructor (`instructor2@pwd301.local`).
2. Dispatch a `GET` request to `http://127.0.0.1:5000/instructor/courses`.
3. Record server-side execution time and network response latency.
4. Observe that total latency is ~663 ms, exceeding the 500 ms budget.

---

## 5. Remediation Plan
Update `get_instructor_managed_courses` in `src/pwd301/services/instructor_service.py` to use SQLAlchemy eager-loading:
```python
from sqlalchemy.orm import selectinload

stmt = (
    select(Course)
    .where(Course.instructor_id == actor.user_id)
    .options(
        selectinload(Course.learning_units),
        selectinload(Course.enrollments),
        selectinload(Course.change_requests)
    )
)
```
This reduces the query count to 4 queries total regardless of the number of courses, reducing latency to < 100 ms.
