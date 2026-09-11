# TASK-028 — Full E2E, Concurrency & Retention Lifecycle QA

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Engineer  
**Started Date:** 2026-09-11  
**Completed Date:** 2026-09-11  

---

## Goal
Implement and execute a comprehensive end-to-end scenario test suite (`tests/e2e/`), high-load concurrency and race condition verification (`tests/concurrency/`), and the Algorithm 13 Data Retention and Pruning Engine (`src/pwd301/services/retention_service.py`) to guarantee production reliability before Docker packaging (TASK-029).

---

## Source-of-Truth Documents
- `AGENTS.md` (Operational contract, Fail-closed invariants, Zero PK Leakage, CSRF protection)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/testing/11_END_TO_END_SCENARIOS.md` (Standard E2E Scenarios)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/testing/07_CONCURRENCY_TEST_PLAN.md` (Concurrency & Race condition plan)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/13_RETENTION_CLEANUP_ALGORITHM.md` (Data cleanup algorithm)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/16_DATA_LIFECYCLE_RETENTION.md` & `docs/database/PWD301_DATABASE_ARCHITECTURE/15_RETENTION_DELETE_RESTORE_MATRIX.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `tasks/templates/TASK_TEMPLATE.md`

---

## Preconditions
- Virtual environment at `.venv`.
- Python 3.12 with all dependencies.
- Canonical SQL Server schema intact (71 tables verified).
- TASK-001 through TASK-027 complete.

---

## In Scope
1. **Retention & Pruning Engine (`src/pwd301/services/retention_service.py`)**:
   - `purge_expired_enrollment_details`: Purge `lesson_progress` and raw attempt answer details after 30 days of leaving, while permanently retaining `CourseCompletionSummary` for prerequisite proofs.
   - `prune_trash_entities`: Automatically hard-delete entities in `TRASH` for > 30 days: `FileAsset` (unlinking disk file when `reference_count == 0`), `Assessment`, `Course`, `Question`.
   - `purge_expired_ai_messages`: Purge raw chat content (`ai_messages.content`) after 5 minutes of inactivity, retaining minimal conversation metadata.
   - Audit Log Immunity: Guarantee `audit_events` is never deleted or truncated (Append-only invariant).
   - `run_full_retention_cycle`: Idempotent batch coordinator.
2. **Concurrency Verification (`tests/concurrency/`)**:
   - Multi-threaded enrollment capacity race when 1 slot remains.
   - Attempt lease renewal vs takeover race.
   - 5-thread concurrent submit with identical idempotency key.
   - Database restore concurrency control (`_restore_lock`).
3. **End-to-End Scenarios (`tests/e2e/`)**:
   - `test_student_lifecycle_e2e.py`: Registration, prerequisite check barrier, sequential learning, heartbeat, assessment snapshot, autosave, idempotent submission, score viewing, completion engine, AI recommendation.
   - `test_instructor_lifecycle_e2e.py`: Course DRAFT, file upload/scan/clean, question bank manual + docx import, blueprint build, publish, attempt start structure freeze, manual essay grading, score release, question revision/correction, background regrading engine.
   - `test_admin_ops_lifecycle_e2e.py`: Course approval/publish, role assignment/revocation, user suspension (immediate session & JWT revocation), append-only audit log query & diff, backup/dry-run restore/maintenance mode/controlled restore drill.
   - `test_retention_lifecycle_e2e.py`: 30-day enrollment detail purge, trash pruning (file, assessment, course), AI chat 5-min inactivity purge, audit log immunity.
4. **Verification & Quality Gate**:
   - All tests passing (Unit, API, Security, Concurrency, E2E).
   - `repo_check.py`, `ruff check`, `ruff format --check`, `mypy src` with 0 errors.

---

## Out of Scope
- Modifying SQL Server DDL or adding new database tables.
- Introducing external message brokers (RabbitMQ/Kafka) or external Redis.

---

## Acceptance Criteria Checklist
- [x] **AC-E2E-01**: Luồng sinh viên khép kín từ đăng ký -> học tập -> nộp bài thi -> nhận chứng chỉ hoàn thành chạy mượt mà không có bất kỳ lỗi logic nào.
- [x] **AC-E2E-02**: Luồng giảng viên từ soạn thảo -> import tài liệu -> duyệt bài -> chấm thi -> regrading bảo toàn 100% lịch sử điểm và không làm sai lệch kết quả thí sinh.
- [x] **AC-E2E-03**: Luồng quản trị viên cách ly tài khoản, xem audit trail và diễn tập backup/restore trong cửa sổ bảo trì thành công 100%.
- [x] **AC-E2E-04**: Thuật toán Retention (Algorithm 13) dọn dẹp chính xác các bản ghi quá hạn 30 ngày, bảo lưu tuyệt đối Audit Log và tóm tắt điều kiện tiên quyết.
- [x] **AC-E2E-05**: Toàn bộ các test tương tranh (Capacity, Lease takeover, Idempotent submission, Restore lock) đạt kết quả 100% thread-safe mà không bị deadlock.
- [x] **AC-E2E-06**: Bộ kiểm tra hợp đồng repo `python scripts/repo_check.py` vượt qua với 0 lỗi.
- [x] **AC-E2E-07**: `ruff check` và `ruff format --check` đạt 0 lỗi; `mypy src` kiểm tra tĩnh hợp lệ.
- [x] **AC-E2E-08**: Toàn bộ test suite tổng thể (Unit, API, Security, Concurrency, Integration, E2E) đạt 100% PASS (745/745 tests passed).
