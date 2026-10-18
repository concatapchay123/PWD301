# PWD301 MASTER DEFECT REGISTRY

**Last Updated:** 2026-10-18T08:00:00Z  
**Total Iterations Audited:** 20 of 20  
**Lead Auditor:** AGENT 01 — QA Orchestrator & Test Manager, AGENT 08 — Independent Auditor  

---

## 1. Master Defect Ledger

| Defect ID | Title | Severity | Priority | Category | Status | Discovered In | Re-verified In | Affected Component | Root Cause Summary |
|---|---|---|---|---|---|---|---|---|---|
| **DEFECT-IT10-001** | `POST /instructor/courses/<id>/trash` raises HTTP 403 on serialization post-trash | High | P1 | Business Logic / Auth | **OPEN** | Iteration 10 | Iteration 19 (`TC-IT19-001`) | `src/pwd301/blueprints/instructor/routes.py` (line 1205) | `trash_instructor_course()` successfully commits `deleted_at = utcnow()` in SQL Server, then calls `_serialize_course(course)`. `_serialize_course` calls `can_manage_course()` which requires `course.deleted_at is None`, raising `ForbiddenError` (HTTP 403). Non-destructive (DB soft-delete succeeds). |
| **DEFECT-IT16-001** | `GET /instructor/courses` response latency (663ms) exceeds 500ms budget due to N+1 query serialization | Medium | P2 | Performance / N+1 Latency | **OPEN** | Iteration 16 | Iteration 19 (`TC-IT19-002`) | `src/pwd301/blueprints/instructor/routes.py` (line 1162) | `_serialize_course(summary=True)` executes un-eager-loaded SQL queries per course row for `c.lessons`, `c.enrollments`, `c.owner_instructor`, `effective_course`, and `course_review_version`, creating an $O(N)$ query cascade. |

---

## 2. Defect Summary by Severity & Impact

- **Critical (P0) Blockers:** **0** (Zero data loss, zero security bypass, zero crash bugs).
- **High (P1):** **1** (`DEFECT-IT10-001` - Trashing response serialization).
- **Medium (P2):** **1** (`DEFECT-IT16-001` - N+1 query latency on instructor course list).
- **Low (P3):** **0**.
- **Total Open Defects:** **2**.
- **Total Verified Fixed:** **0** (Audit and bug discovery directive strictly maintained; no unauthorized production mutations).

---

## 3. Remediation Roadmaps

### Remediation for DEFECT-IT10-001:
In `src/pwd301/blueprints/instructor/routes.py`:
```python
# Option A: Compact serialization for trashed entity
@instructor_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_instructor_course(course_id: str) -> tuple[Response, int]:
  actor = require_authenticated_actor()
  course = trash_course(actor, course_id, session=db.session)
  db.session.commit()
  # Return clean confirmation without re-evaluating active manager permissions:
  return (
      jsonify({
          "success": True,
          "message": "Course moved to trash.",
          "data": {
              "id": str(course.public_id),
              "title": course.title,
              "is_deleted": True,
              "deleted_at": (
                  course.deleted_at.isoformat() if course.deleted_at else None
              ),
          },
      }),
      200,
  )
```

### Remediation for DEFECT-IT16-001:
In `src/pwd301/blueprints/instructor/routes.py`:
```python
# Option A: SQLAlchemy joinedload eager loading
courses = (
    db.session.query(Course)
    .options(
        joinedload(Course.owner_instructor),
        selectinload(Course.lessons),
        selectinload(Course.enrollments),
    )
    .filter(Course.owner_instructor_id == actor.id, Course.deleted_at.is_(None))
    .all()
)
```
