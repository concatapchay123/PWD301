# Iteration 10: Test Coverage Analysis

## 1. Domain Coverage: Database Transactions, Referential Integrity & Cascade Soft-Deletes
- **Tables Audited & Inspected in Microsoft SQL Server:**
  - `courses`: Soft-delete transitions, `status='TRASH'`, `deleted_at`, unique key constraint preservation.
  - `learning_units`: Soft-delete cascade, position re-compaction from position `2` to `1`.
  - `lessons`: Cascade transition to status `'TRASH'`, `TRASH_POSITION_BASE` (>= 1,000,000), contiguous re-compaction `1..N`.
  - `lesson_resources`: Hard deletion on lesson soft-delete to guarantee detachment.
  - `file_assets`: Status transition to `'TRASH'`, `deleted_at` timestamping, orphaned asset cleanup.
  - `enrollments`: Referential integrity preservation upon course soft-delete, active student protection.
  - `audit_events`: Append-only schema integrity (0 mutable columns), valid JSON constraint verification.

## 2. API Endpoints Probed
1. `POST /instructor/courses/<course_id>/lessons/<lesson_id>/delete` (TC-IT10-001, TC-IT10-002)
2. `GET /student/courses/<course_id>/files` (TC-IT10-001)
3. `POST /instructor/courses/<course_id>/lessons` (TC-IT10-003)
4. `POST /instructor/courses/<course_id>/lessons/reorder` (TC-IT10-003)
5. `POST /student/courses/<course_id>/enroll` (TC-IT10-004)
6. `POST /instructor/courses/<course_id>/trash` (TC-IT10-004)
7. `GET /admin/governance` (TC-IT10-005)
8. `DELETE /instructor/learning-units/<unit_id>` (TC-IT10-006)

## 3. Invariant Verification Coverage
- **Cascade Attachment Deletion & Document Hub Invariant:** 100% verified.
- **Contiguous Lesson Position Re-Compaction (Algorithm 04):** 100% verified.
- **Multi-Table Transaction Atomicity & Rollback:** 100% verified.
- **Foreign Key Referential Integrity:** 100% verified (destructive hard delete strictly blocked by database-level FK).
- **Active Student Protection Guard:** 100% verified (cannot trash course while student is `ACTIVE`).
- **Append-Only Immutable Audit Trail (Table `audit_events`):** 100% verified.
- **Learning Unit Soft-Delete & Child Cascading:** 100% verified.
