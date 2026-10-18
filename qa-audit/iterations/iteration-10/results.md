# Iteration 10: Execution Results

**Iteration:** 10  
**Domain:** Database Transactions, Referential Integrity & Cascade Soft-Deletes  
**Timestamp:** 2026-10-18T06:38:40Z  
**Browser Engine:** Real Google Chrome 155 via Playwright (`channel="chrome"`)  
**Backend:** Local Docker container `pwd301_web` (Flask REST API + SQL Server)  
**Execution Summary:** 6 executed | 5 PASS | 1 FAIL (1 Defect Discovered: DEFECT-IT10-001)

---

## 1. Test Case Execution Breakdown

| Test ID | Test Case Title | Status | Evidence Screenshot | DB Verification |
|---|---|---|---|---|
| **TC-IT10-001** | Cascade Attachment Deletion & Document Hub Invariant | **PASS** | `IT10_TC01_cascade_attachment_deletion.png` | `LessonResource` deleted; `FileAsset` marked `TRASH`; fail-closed Student Hub access confirmed. |
| **TC-IT10-002** | Contiguous Lesson Position Re-Compaction | **PASS** | `IT10_TC02_lesson_position_recompaction.png` | L2 shifted to `TRASH_POSITION_BASE` (10,200,061); remaining lessons re-compacted to contiguous `[1, 2]`. |
| **TC-IT10-003** | Multi-Table Transaction Atomicity & Rollback | **PASS** | `IT10_TC03_transaction_atomicity_rollback.png` | Oversized title (>200 chars) & invalid reorder rejected; row counts 100% identical before/after (0 leak). |
| **TC-IT10-004** | Foreign Key Referential Integrity & Non-Destructive Soft-Delete | **FAIL** | `IT10_TC04_foreign_key_soft_delete.png` | **Defect Discovered (DEFECT-IT10-001):** API returns 403 on serialization. DB FK successfully blocked raw hard delete; historical enrollment preserved. |
| **TC-IT10-005** | Append-Only Immutable Audit Trail | **PASS** | `IT10_TC05_immutable_audit_trail.png` | `audit_events` table verified with 0 mutable columns (`updated_at`/`deleted_at`), valid JSON payloads. |
| **TC-IT10-006** | Learning Unit Soft-Delete & Child Cascading | **PASS** | `IT10_TC06_chapter_cascade_soft_delete.png` | Chapter 1 soft-deleted; all child lessons trashed; Chapter 2 re-compacted from position 2 to position 1. |

---

## 2. In-Depth Empirical Findings

### TC-IT10-001: Cascade Attachment Deletion & Document Hub Invariant
- **Setup:** Instructor created Chapter 1 and Lesson 1, uploading an authentic clean PDF `tai_lieu_hoc_tap.pdf`. Database linked `LessonResource` and verified `FileAsset.status == 'ACTIVE'` with clean malware scan.
- **Action:** Instructor soft-deleted Lesson 1 via `POST /instructor/courses/<course_id>/lessons/<lesson_id>/delete`.
- **Database Proof:**
  - `Lesson.status = 'TRASH'`, `Lesson.position = 10200059` (offset beyond active domain).
  - `LessonResource` row linking the file to the lesson was completely deleted (`lr_found = False`).
  - Orphaned `FileAsset` transitioned to status `'TRASH'`, `deleted_at = '2026-10-18T06:38:52.347000'`.
  - Student Document Hub endpoint `GET /student/courses/<course_id>/files` returned 0 items. Fail-closed document protection verified.

### TC-IT10-002: Contiguous Lesson Position Re-Compaction
- **Setup:** Three lessons created in Chapter 1: Lesson A (pos 1), Lesson B (pos 2), Lesson C (pos 3).
- **Action:** Instructor deleted middle lesson B via `POST /instructor/courses/<course_id>/lessons/<l2_id>/delete`.
- **Database Proof:**
  - Lesson B moved to `TRASH_POSITION_BASE + id` = `10200061`.
  - Remaining active lessons: Lesson A remains position `1`, Lesson C re-compacted to position `2`.
  - Active positions in course are strictly contiguous `[1, 2]`. No gaps, no collisions against SQL Server unique constraint `(course_id, position)`.

### TC-IT10-003: Multi-Table Transaction Atomicity & Rollback
- **Setup:** Baseline database snapshot recorded: 62 active lessons, 89 total lessons.
- **Action:**
  - Probe 1: Attempted creating a lesson with title of 250 characters. Backend rejected with HTTP 400 `code: 'VALIDATION_ERROR'`.
  - Probe 2: Attempted reordering curriculum with an invalid/mismatched UUID. Backend rejected with HTTP 409 Conflict.
- **Database Proof:** Post-probe SQL query confirmed exact row counts remained 62 active / 89 total. Zero orphaned entities, zero corrupted positions.

### TC-IT10-004: Foreign Key Referential Integrity & Non-Destructive Soft-Delete
- **Setup:** Published course with active enrolled student.
- **Action 1 (Active Student Guard):** Instructor attempted trashing course with active enrolled student. Backend rejected with `CourseStateViolationError`: *"Không thể chuyển khóa học vào thùng rác vì đang có 1 học viên đang theo học."*
- **Action 2 (Historical Soft-Delete & Defect Discovery):** Student enrollment was completed. Instructor called `POST /instructor/courses/<course_id>/trash`.
  - **Defect Discovered (DEFECT-IT10-001):** The endpoint transitioned the course to `TRASH` in the database, but crashed during response serialization with HTTP 403 `ForbiddenError: You do not have permission to manage this course.` because `_serialize_course` calls `list_learning_units`, which triggers `require_course_manager` -> `can_manage_course`, returning `False` for non-admins when `course.deleted_at is not None`.
- **Database Proof:**
  - SQL Server `courses.status = 'TRASH'`, `courses.deleted_at` populated.
  - Historical student enrollment record remained 100% intact in table `enrollments`.
  - Direct SQL hard delete `DELETE FROM courses WHERE id = :cid` was strictly blocked by SQL Server Foreign Key constraint (`hard_delete_blocked = True`).

### TC-IT10-005: Append-Only Immutable Audit Trail
- **Setup:** Schema inspection of SQL Server table `audit_events` and inspection of course transition audit records.
- **Database Proof:**
  - Schema inspection confirmed: `has_updated_at = False`, `has_deleted_at = False`.
  - Actions recorded in chronological order: `COURSE_TRASHED`, `COURSE_PUBLISHED`, `COURSE_APPROVED`, `COURSE_SUBMITTED_FOR_REVIEW`, `COMPLETION_RULE_UPDATED`.
  - Check constraints `ISJSON(before_json) = 1` and `ISJSON(after_json) = 1` strictly satisfied.

### TC-IT10-006: Learning Unit Soft-Delete & Child Cascading
- **Setup:** Course with Chapter 1 (containing 4 lessons) and Chapter 2.
- **Action:** Instructor deleted Chapter 1 via `DELETE /instructor/learning-units/<unit1_id>`.
- **Database Proof:**
  - Chapter 1: `deleted_at = '2026-10-18T06:39:24.636000'`.
  - All 4 child lessons transitioned to status `'TRASH'` with populated timestamps and offset positions.
  - Chapter 2 re-compacted from position `2` to position `1`.
