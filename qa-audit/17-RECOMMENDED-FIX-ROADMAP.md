# PWD301 RECOMMENDED DEFECT FIX & REFACTORING ROADMAP

**Document Purpose:** Detailed engineering remediation guides for all open defects discovered during the 20-Iteration QA Audit.

---

## 1. Remediation for DEFECT-IT10-001 (Priority: P1 - High)

### Problem Description:
Calling `POST /instructor/courses/<course_id>/trash` successfully marks the course as deleted in SQL Server (`deleted_at = utcnow()`), but then attempts to return `_serialize_course(course)`. `_serialize_course` executes `require_course_manager(actor, course)` which checks `if course.deleted_at is not None: raise ForbiddenError("You do not have permission to manage this course.")`.

### Exact File & Lines:
- File: `src/pwd301/blueprints/instructor/routes.py`
- Route function: `trash_instructor_course(course_id: str)` (around lines 1200–1215)

### Recommended Code Patch:
```python
@instructor_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_instructor_course(course_id: str) -> tuple[Response, int]:
  """Soft-delete (trash) an instructor-owned course."""
  actor = require_authenticated_actor()
  course = trash_course(actor, course_id, session=db.session)
  db.session.commit()

  # Fix: Return deletion confirmation without calling active-only serialization:
  return (
      jsonify({
          "success": True,
          "message": "Khóa học đã được chuyển vào thùng rác thành công.",
          "data": {
              "id": str(course.public_id),
              "title": course.title,
              "is_deleted": True,
              "deleted_at": (
                  course.deleted_at.isoformat() if course.deleted_at else None
              ),
          },
          "error": None,
      }),
      200,
  )
```

---

## 2. Remediation for DEFECT-IT16-001 (Priority: P2 - Medium)

### Problem Description:
Calling `GET /instructor/courses` takes an average of **$663.2\text{ms}$** (exceeding the $500\text{ms}$ budget) because `_serialize_course(c, summary=True)` lazily accesses:
- `c.owner_instructor` (triggers 1 SQL query per course)
- `c.lessons` (triggers 1 SQL query per course to count active lessons)
- `c.enrollments` (triggers 1 SQL query per course to count active enrollments)
- `c.course_review_version` / `effective_course` (triggers multiple relational queries per course)

### Exact File & Lines:
- File: `src/pwd301/blueprints/instructor/routes.py`
- Route function: `list_instructor_courses()` (around lines 1150–1180)

### Recommended Code Patch:
```python
from sqlalchemy.orm import joinedload, selectinload


@instructor_bp.route("/courses", methods=["GET"])
@instructor_required
def list_instructor_courses() -> tuple[Response, int]:
  """List all courses owned by current instructor with eager loading."""
  actor = require_authenticated_actor()

  # Fix: Apply joinedload and selectinload to eliminate N+1 queries
  courses = (
      db.session.query(Course)
      .options(
          joinedload(Course.owner_instructor),
          selectinload(Course.lessons),
          selectinload(Course.enrollments),
      )
      .filter(
          Course.owner_instructor_id == actor.id, Course.deleted_at.is_(None)
      )
      .order_by(Course.created_at.desc())
      .all()
  )

  serialized = [_serialize_course(c, summary=True) for c in courses]
  return (
      jsonify({
          "success": True,
          "data": {"courses": serialized, "total": len(serialized)},
          "error": None,
      }),
      200,
  )
```

---

## 3. Verification Post-Fix Procedure
1. Re-run `python qa-audit/test-scripts/run_iteration_19.py`.
2. Confirm `TC-IT19-001` transitions from `DEFECT_CONFIRMED` to `PASS` (HTTP 200).
3. Confirm `TC-IT19-002` transitions from `DEFECT_CONFIRMED` to `PASS` (average latency $\le 200\text{ms}$).
