# Iteration 10: Defect Report

## Summary of Defects Discovered in Iteration 10
- **Total Defects Discovered:** 1
- **Critical (P0):** 0
- **High (P1):** 1 (DEFECT-IT10-001)
- **Medium (P2):** 0
- **Low (P3):** 0

---

## DEFECT-IT10-001: Course Soft-Delete Route Crashes with HTTP 403 on Response Serialization
- **ID:** DEFECT-IT10-001
- **Severity:** High (P1)
- **Component:** `POST /instructor/courses/<course_id>/trash` (`src/pwd301/blueprints/instructor/routes.py`)
- **Impact:** Instructor attempts to soft-delete an owned course. The database mutation executes and soft-deletes the course, but the route crashes during serialization with HTTP 403 `ForbiddenError: You do not have permission to manage this course.`, showing an error toast and causing client state desynchronization.
- **Root Cause:** `_serialize_course` calls `list_learning_units(actor, c.id)`, which enforces `require_course_manager`. In `can_manage_course`, non-administrators are denied if `course.deleted_at is not None`. Because `trash_course` already set `deleted_at`, the instructor is immediately rejected on serialization.
- **Reference Document:** [DEFECT-IT10-001.md](../../defects/DEFECT-IT10-001.md)
