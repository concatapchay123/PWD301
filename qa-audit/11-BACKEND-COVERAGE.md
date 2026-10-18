# PWD301 BACKEND & DATABASE INTEGRITY AUDIT

**Database Engine:** Microsoft SQL Server 2022 (Docker container `pwd301_db`)  
**ORM:** SQLAlchemy 2.0 / Alembic Migrations  
**Total Tables:** 77 Relational Tables  
**Total Models:** 84 Registered Domain Classes  

---

## 1. Relational Integrity & Transaction Coverage

| Domain Entity | Primary Key / Indexing | Foreign Key Semantics | Invariants Verified | Audit Result |
|---|---|---|---|---|
| `User` / `UserRole` | `BIGINT` PK, `UUID` public_id | `user_roles` $\rightarrow$ `users(id)` | Unique email, allowed role combinations | **PASS** |
| `Course` | `BIGINT` PK, `UUID` public_id | `owner_instructor_id` $\rightarrow$ `users(id)` | Soft-delete retention, zero broad cascades | **PASS (Defect on serialization logged)** |
| `Lesson` / `LearningUnit` | `BIGINT` PK, `UUID` public_id | `course_id` $\rightarrow$ `courses(id)` | Soft-delete cascading to `LessonResource` & `FileAsset` | **PASS** |
| `LessonResource` / `FileAsset` | `BIGINT` PK, `UUID` public_id | `lesson_id` $\rightarrow$ `lessons(id)` | Automatic detachment from Course Document Hub | **PASS** |
| `AssessmentAttempt` | `BIGINT` PK, `UUID` public_id | `student_user_id` $\rightarrow$ `users(id)` | Algorithm 07 Single Active Editing Lease, Idempotent submit | **PASS** |
| `AttemptQuestion` / `Grade` | `BIGINT` PK, `UUID` public_id | `attempt_id` $\rightarrow$ `assessment_attempts(id)` | Decimal scoring, frozen question/choice presentation | **PASS** |
| `AuditEvent` | `BIGINT` PK, `UUID` public_id | Append-only audit table | Append-only integrity, actor metadata persistence | **PASS** |

---

## 2. Concurrency & Locking Mechanics

- **Row-Level Capacity Lock (`UPDLOCK, HOLDLOCK`):** Verified concurrent student enrollment capacity enforcement (`TC-IT11-005`). Seat 1 of 1 allocated atomically; simultaneous second applicant rejected with HTTP 409 `CAPACITY_EXCEEDED`.
- **Single Active Editing Lease (Algorithm 07):** Stale write fencing confirmed across lease takeovers (`TC-IT11-002`, `TC-IT19-005`).
- **N+1 Relationship Performance Bottleneck:** Confirmed `_serialize_course(summary=True)` executes un-eager-loaded queries per course row, requiring `joinedload` optimization (`DEFECT-IT16-001`).
