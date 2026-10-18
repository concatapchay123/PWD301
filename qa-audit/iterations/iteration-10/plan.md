# Iteration 10: Database Transactions, Referential Integrity & Cascade Soft-Deletes

## 1. Objectives & Scope
Verify the transactional boundaries, foreign key protections, cascade soft-deletion mechanics, position re-compaction algorithms, rollback atomicity, and append-only audit trail invariants across Microsoft SQL Server and PWD301 Application Layer.

## 2. Invariants Under Test
1. **Cascade Attachment Deletion & Document Hub Invariant:** Deleting a Lesson or LearningUnit automatically removes `LessonResource` entries and transitions orphaned `FileAsset` rows to status `TRASH` with `deleted_at`, immediately making them inaccessible in the Student Course Document Hub.
2. **Contiguous Lesson Position Re-Compaction (Algorithm 04 / Invariant 2.3):** Soft-deleting a lesson moves its position out of the active range (`TRASH_POSITION_BASE + lesson.id`) and shifts remaining active lessons into contiguous sequential positions `1..N` via a 2-phase offset to avoid SQL Server unique constraint collisions.
3. **Multi-Table Transaction Atomicity & Rollback:** Mid-stream failure or validation error during curriculum mutations completely rolls back the database transaction with zero orphaned rows or corrupted positions.
4. **Foreign Key Referential Integrity & Non-Destructive Soft-Delete:** Course deletion sets `deleted_at` and `status='TRASH'`, never executing destructive hard SQL `DELETE`. Historical student enrollments, assessments, and attempts remain intact. Hard delete attempts trigger database-level FK restriction.
5. **Append-Only Immutable Audit Trail (Invariant 06 / Table `audit_events`):** Administrative and security actions record immutable append-only rows in `audit_events` (no `updated_at`, no `deleted_at`).
6. **Learning Unit Soft-Delete & Child Cascading:** Deleting a LearningUnit (chapter) soft-deletes the unit, transitions child lessons to `TRASH`, cleans up associated file assets, and re-compacts remaining active units to contiguous positions `1..M`.

## 3. Test Cases
- `TC-IT10-001`: Cascade Attachment Deletion: Soft-deleting a lesson automatically cascades to `LessonResource` and orphaned `FileAsset`, removing documents from Student Document Hub.
- `TC-IT10-002`: Lesson Position Re-Compaction: Deleting a middle lesson re-compacts active lessons into contiguous sequence `1..2` without collision.
- `TC-IT10-003`: Multi-Table Transaction Atomicity & Rollback: Halfway failure in curriculum mutation triggers complete rollback with zero orphaned rows.
- `TC-IT10-004`: Foreign Key Referential Integrity & Deletion Protection: Course deletion performs soft-delete, leaving historical enrollments and attempt records intact.
- `TC-IT10-005`: Append-Only Immutable Audit Trail: Administrative mutations record immutable rows in `audit_events`.
- `TC-IT10-006`: Learning Unit Soft-Delete & Child Cascading: Soft-deleting a chapter cascades to all child lessons, resources, and re-compacts remaining chapters.

## 4. Execution Methodology
- Real Google Chrome browser automation via Playwright (`channel="chrome"`).
- Dual-persisted annotated screenshots (`qa-audit/screenshots/` and `qa-audit/iterations/iteration-10/evidence/`).
- Direct SQL Server database queries inside `pwd301_web` container via SQLAlchemy to assert row-level consistency, position values, and foreign key relations.
