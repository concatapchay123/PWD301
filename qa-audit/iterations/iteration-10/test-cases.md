# Iteration 10: Test Cases Specification

## TC-IT10-001: Cascade Attachment Deletion & Document Hub Invariant
- **Objective:** Verify that soft-deleting a lesson automatically cascades to associated `LessonResource` records and marks unshared `FileAsset` entries as `TRASH`, immediately removing them from the Student Course Document list.
- **Preconditions:** Instructor is logged in; course in `DRAFT` status with a chapter and a lesson containing an attached PDF learning document (`LessonResource`). Student is enrolled and can see the document.
- **Action:** Instructor soft-deletes the lesson via `POST /instructor/courses/<course_id>/lessons/<lesson_id>/delete`.
- **Expected Outcome:**
  - HTTP 200 response.
  - SQL Server `lessons.status` set to `'TRASH'`, `lessons.deleted_at` populated.
  - Corresponding `lesson_resources` record deleted.
  - Corresponding `file_assets.status` set to `'TRASH'`, `file_assets.deleted_at` populated.
  - Student Document Hub (`GET /student/courses/<course_id>/files`) no longer lists the trashed document (fail-closed access).
- **Evidence:** Browser screenshot in Instructor Studio and Student Document Hub + database query snapshot.

---

## TC-IT10-002: Contiguous Lesson Position Re-Compaction
- **Objective:** Verify that soft-deleting a middle lesson (position 2 of 3) triggers position re-compaction to sequential `1..2` without unique constraint collisions.
- **Preconditions:** Course with 3 active lessons at positions 1, 2, 3.
- **Action:** Instructor deletes Lesson 2.
- **Expected Outcome:**
  - HTTP 200 response.
  - Lesson 2 moved to `position = TRASH_POSITION_BASE + lesson_2.id` (>= 1,000,000) and `status = 'TRASH'`.
  - Remaining lessons re-compacted: Lesson 1 has `position = 1`, Lesson 3 has `position = 2`.
  - Database unique index `(course_id, position)` remains valid and unbroken.
- **Evidence:** Browser Studio curriculum tree + SQL Server position inspection.

---

## TC-IT10-003: Multi-Table Transaction Atomicity & Rollback
- **Objective:** Verify that an invalid mutation or halfway failure in curriculum manipulation triggers complete rollback with zero orphaned records or altered positions.
- **Preconditions:** Course with active lessons.
- **Action:**
  1. Instructor attempts invalid lesson creation (title > 200 characters).
  2. Instructor attempts invalid reordering payload with non-existent or mismatched lesson IDs.
- **Expected Outcome:**
  - HTTP 400 / 409 error envelope.
  - Database transaction rolls back completely: lesson count unchanged, position ordering preserved, zero orphaned rows.
- **Evidence:** Browser error response modal/toast + SQL Server row count comparison before and after failure.

---

## TC-IT10-004: Foreign Key Referential Integrity & Non-Destructive Soft-Delete
- **Objective:** Verify that trashing a course soft-deletes the course record without deleting historical student enrollments or assessment attempts.
- **Preconditions:** Course with enrolled student who has an active enrollment and assessment record.
- **Action:** Instructor/Admin trashes the course via `POST /instructor/courses/<course_id>/trash`.
- **Expected Outcome:**
  - HTTP 200 response.
  - `courses.status = 'TRASH'`, `courses.deleted_at` populated.
  - `enrollments` records remain in the database (never hard-deleted).
  - `assessment_attempts` records remain in the database with their FK referencing the assessment/course.
- **Evidence:** Browser screenshot of trashing confirmation + database foreign key verification.

---

## TC-IT10-005: Append-Only Immutable Audit Trail
- **Objective:** Verify that administrative and security actions record immutable append-only events in table `audit_events`.
- **Preconditions:** Admin/Instructor performs an audited action (e.g. course status transition, trashing, or publishing).
- **Action:** Query SQL Server `audit_events` for recent events associated with the target course.
- **Expected Outcome:**
  - New `AuditEvent` row created with valid `event_id`, `actor_user_id`, `action`, `target_type`, `created_at`.
  - Table has no `updated_at` or `deleted_at` columns, enforcing append-only semantics.
  - `ISJSON(before_json) == 1` and `ISJSON(after_json) == 1` constraints satisfied.
- **Evidence:** Browser audit history / admin review pane + database SQL inspection.

---

## TC-IT10-006: Learning Unit Soft-Delete & Child Cascading
- **Objective:** Verify that deleting a LearningUnit (chapter) soft-deletes the unit, cascades soft-delete to all child lessons, cascades resource cleanup, and re-compacts remaining units to contiguous `1..M`.
- **Preconditions:** Course with 2 chapters (Chapter 1 with child lesson + PDF document, Chapter 2).
- **Action:** Instructor deletes Chapter 1 via `DELETE /instructor/learning-units/<unit_id>`.
- **Expected Outcome:**
  - HTTP 200 response.
  - Chapter 1 `deleted_at` populated.
  - Child lesson in Chapter 1 transitioned to `TRASH` with position offset.
  - Child lesson's attached document `LessonResource` deleted and `FileAsset` marked `TRASH`.
  - Chapter 2 re-compacted from position 2 to position 1.
- **Evidence:** Browser Studio curriculum tree + SQL Server unit and lesson state snapshot.
