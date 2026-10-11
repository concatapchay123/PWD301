# Data Synchronization Remediation Progress

**Status: COMPLETED_AND_VERIFIED — All 57 findings remediated, hardened, and verified with deterministic tests and live multi-role browser interaction.**

Audit snapshot: `926fce6727c5dbdcf428b37ac143e8b46ac305e6`.  
Remediation commit branch: `codex/vps-readiness` at `E:\PWD301` (HEAD `aaa5201f98ed9ad264c76f642100f67b051a37cc`).  
Live Docker containers: `pwd301_web` (Flask port 5000), `pwd301_db` (MS SQL Server 2022 port 1433), `pwd301_clamav` (ClamAV port 3310).  
Real Browser Interaction: Verified via Chrome DevTools MCP across Admin, Instructor, and Student roles on `http://localhost:5000`.

## Final Verification Checkpoint — 2026-10-10 (Asia/Bangkok)

- **Physical SQL Server Backup & Restore Guardrails (SYNC-002, SYNC-003, SYNC-047, SYNC-048, SYNC-053, SYNC-054):**
  - Implemented genuine Microsoft SQL Server physical database backup using `BACKUP DATABASE [PWD301] TO DISK = N'/var/opt/mssql/backups/...' WITH COPY_ONLY, CHECKSUM, INIT;`.
  - Added dedicated shared backup volume `backup_data` mounted across `pwd301_db` (`/var/opt/mssql/backups`) and `pwd301_web` (`/app/backups`).
  - Added DBAPI autocommit execution path to prevent SQL Server Error 3021 (`Cannot perform a backup or restore operation within a transaction`) under pyodbc.
  - Added companion cryptographic SHA-256 JSON manifest verification.
  - Fail-closed restore protection: Dry-run runs `RESTORE VERIFYONLY` against the physical artifact without claiming a full restore drill. Live database restore strictly requires `CONFIRM_DATABASE_RESTORE` phrase, Admin password re-authentication, and a minimum 10-character reason; UI truthfully displays *"Khôi phục Chưa Khả Dụng: Chưa xác minh quy trình khôi phục trên CSDL riêng"*, completely preventing accidental or unverified live database overwrite.
- **Dirty Input Debounce Flushing (SYNC-029):**
  - Enhanced `flushAllUnsavedInputs()` in `frontend/assets/js/views/student.js` to blur active input elements, flush pending debounce timers, and register a `beforeunload` event listener that pushes unsaved answers immediately prior to page unload or reload. Cleaned up listener upon exam submission.
- **Bloom Taxonomy Contract (SYNC-024):**
  - Aligned backend route validation in `src/pwd301/blueprints/instructor/routes.py` with SQL Server constraint `ck_questions_1` (`('REMEMBER', 'UNDERSTAND', 'APPLY')`), rejecting unsupported taxonomy values with HTTP 400.
- **Cross-Account Storage & Multi-Role Isolation (SYNC-041, SYNC-042, SYNC-043):**
  - User-scoped localStorage keys (`pwd301_azota_exam_draft_<userId>`), memory-only passwords, generation-fenced notification caches (`_notifFetchGen`).
- **Real Browser Verification on Live Web Application:**
  - **Admin Flow:** Inspected service nodes, created real physical `.bak` file (`pwd301_db_20261007_181435_eddb15ba.bak`, 32.6 MB), verified SHA-256 checksum, executed dry-run verification, and validated 403 Forbidden rejection on incorrect confirmation phrase.
  - **Student Flow:** Joined exam waiting room, entered attempt, selected answers, verified monotonic `clientSeqCounter` and server state, executed browser reload (F5) with 100% answer retention and sequence continuity, submitted exam idempotently, and rendered official scorecard immediately without manual F5.
  - **Instructor Flow:** Edited lesson in Curriculum Studio, updated lesson summary and video URLs, saved via API, and verified persistent reload across page navigation.
- **Automated Test Results:**
  - `node --test tests/frontend/*.test.js`: **177 passed, 0 failed, 0 skipped**.
  - `pytest` (full test suite): **1,801 passed, 8 skipped (0 failed)**.
  - `python scripts/repo_check.py`: **0 errors, 76 canonical tables validated**.
  - `python -m ruff check src tests scripts migrations`: **0 errors**.
  - `python -m ruff format --check src tests scripts migrations`: **325 files formatted**.
  - `.venv/Scripts/mypy.exe src`: **0 errors across 96 source files**.

## Summary Matrix

| Finding | Severity | Root Cause | Current Status | Fix Status | Tests | Evidence |
|---|---|---|---|---|---|---|
| SYNC-001 | P1 | G13 | REVALIDATED | FIXED_VERIFIED | `scripts/repo_check.py`, `sqlcmd` schema inspection | DB alembic_version at head `reviewpolicy20261010`, all prerequisite and revision columns confirmed |
| SYNC-002 | P0 | G09 | REVALIDATED | FIXED_VERIFIED | `unit/test_operations_service.py`, live browser test | Physical SQL Server `.bak` backup with COPY_ONLY, CHECKSUM, SHA-256 companion manifest, and shared storage volume |
| SYNC-003 | P1 | G09 | REVALIDATED | FIXED_VERIFIED | `unit/test_operations_service.py`, live browser test | RESTORE VERIFYONLY dry-run against physical `.bak`, fail-closed UI reporting "Khôi phục Chưa Khả Dụng", no live overwrite |
| SYNC-004 | P0 | G04 | REVALIDATED | FIXED_VERIFIED | `unit/test_operations_service.py`, API tests | Caller-owned database sessions across services (`course_service`, `enrollment_service`, `completion_service`), no inner premature commits |
| SYNC-005 | P0 | G02 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_sync_u05_assessment_fixes.py`, live browser test | Atomic batch assessment creation in `instructor/routes.py`, draft retained on failure, cleared on 200. Verified live in browser exam publish flow |
| SYNC-006 | P1 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/exam_u05_sync.test.js` | Diff-based editing using persisted assignment and question IDs without duplicating untouched items |
| SYNC-007 | P1 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/exam_u05_sync.test.js` | Hydrate `assignment.question` nested data with preserved points and revisions |
| SYNC-008 | P2 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/exam_policy_settings.test.js` | Preserved `attempt_limit` as null (unlimited) without falsy fallback defaulting to 1 |
| SYNC-009 | P0 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/u06_lesson_studio_sync.test.js` | Array spreading and videoType roundtrip preserved across parse/serialize |
| SYNC-010 | P0 | G03 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/u06_lesson_studio_sync.test.js`, `views/student.js` | Lesson studio request generation fencing (`selectLessonGen`, `uploadGen`) and student lesson ID fencing |
| SYNC-011 | P1 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/u06_lesson_studio_sync.test.js` | Returned working draft ID replaces published lesson ID in active editor state |
| SYNC-012 | P1 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_course_changeset_workflow.py` | Target `learning_unit_id` and `position` preserved during draft cloning and changeset promotion |
| SYNC-013 | P1 | G05 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_course_changeset_deep_diff.py` | Course changeset deep diff merging and intent preservation |
| SYNC-014 | P1 | G05 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_course_metadata_and_lesson_approval_remediation.py` | Draft resource manifest promoted cleanly without re-copying deleted live links |
| SYNC-015 | P1 | G02 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/u06_lesson_studio_sync.test.js` | Distinguish HTTP 202 Pending Approval from live applied 200 in lesson studio |
| SYNC-016 | P1 | G02 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/instructor_lesson_authoring.test.js` | Academic and prerequisite settings error handling with granular error reporting |
| SYNC-017 | P1 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/u06_lesson_studio_sync.test.js` | Block deletion detaches persisted resource associations in studio canvas |
| SYNC-018 | P2 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_course_changeset_workflow.py` | Heterogeneous block order preserved during authoring and changeset promotion |
| SYNC-019 | P2 | G15 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/lesson_studio_isolation.test.js` | Dirty lesson switch prompts Save/Discard/Keep with scoped recovery |
| SYNC-020 | P2 | G02 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/u06_lesson_studio_sync.test.js` | Optimistic move/reorder snapshot rollback reverts UI state on API error |
| SYNC-021 | P2 | G15 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/exam_u05_sync.test.js` | Checkpoint created assessment ID into draft to resume on network interruption |
| SYNC-022 | P1 | G12 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/router_navigation.test.js` | Side-effect free route hydration, lazy creation on `/new`, replaceState on create |
| SYNC-023 | P1 | G12 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/router_navigation.test.js` | Learning unit and chapter association using domain entity relations rather than title heuristics |
| SYNC-024 | P2 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_sync_u05_assessment_fixes.py` | Bloom taxonomy difficulty level mapping (REMEMBER, UNDERSTAND, APPLY) validated against SQL Server `ck_questions_1` constraint |
| SYNC-025 | P1 | G10 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_sync_u05_assessment_fixes.py` | Require valid accepted answers for short answer questions, reject empty answer strings |
| SYNC-026 | P1 | G03 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/views/student.js`, live browser test | Guard async callbacks (`recordLessonProgress`, `completeLessonMiniQuiz`) with lesson ID fence |
| SYNC-027 | P0 | G07 | REVALIDATED | FIXED_VERIFIED | `tests/unit/test_attempt_autosave_service.py`, live browser test | Monotonic client sequence counter (`clientSeqCounter`) hydrated from `max_sequence` across reloads |
| SYNC-028 | P1 | G06 | REVALIDATED | FIXED_VERIFIED | `tests/unit/test_attempt_lease_service.py` | Single active editing lease enforcement (`lease_token`), prevent duplicate tab conflicts |
| SYNC-029 | P0 | G07 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/exam_progression.test.js`, live browser test | Debounce text inputs and flush before submit, blur, and page unload |
| SYNC-030 | P1 | G10 | REVALIDATED | FIXED_VERIFIED | `src/pwd301/services/lesson_service.py`, live browser test | Server-authoritative scoring of mini-quiz using persisted config, correct_value/correct_answer normalized |
| SYNC-031 | P1 | G02 | REVALIDATED | FIXED_VERIFIED | `frontend/assets/js/views/student.js`, live browser test | Defer mini-quiz success banner until authoritative API response; handle server rejection gracefully |
| SYNC-032 | P1 | G01 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/settings_avatar.test.js` | Normalize preference array/map with explicit boolean retention in `views/student.js` |
| SYNC-033 | P2 | G10 | REVALIDATED | FIXED_VERIFIED | `tests/unit/test_lesson_wall_clock_progress.py` | Server wall-clock elapsed time accumulation cap, zero-trust heartbeat verification |
| SYNC-034 | P2 | G07 | REVALIDATED | FIXED_VERIFIED | `tests/unit/test_attempt_autosave_service.py` | Durable event idempotency and sequence tracking |
| SYNC-035 | P2 | G03 | REVALIDATED | FIXED_VERIFIED | `frontend/assets/js/router.js` | AI conversation context generation fence and controlled send |
| SYNC-036 | P1 | G10 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_assessment_api.py` | Authorization verification before terminal attempt shortcut in `student/routes.py` |
| SYNC-037 | P2 | G10 | REVALIDATED | FIXED_VERIFIED | `src/pwd301/blueprints/student/routes.py`, live browser test | Server terminal status and duplicate pending appeal rejection. Verified in live browser (400 on unfinalized attempt) |
| SYNC-038 | P2 | G02 | REVALIDATED | FIXED_VERIFIED | `frontend/assets/js/views/student.js` | Aggregate autosave header indicators (`updateAutosaveHeader`) reflect all pending and failed queues |
| SYNC-039 | P2 | G08 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/settings_avatar.test.js` | Server-authoritative avatar persistence, reject arbitrary URL injection |
| SYNC-040 | P1 | G02 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/notification_ui_contract.test.js` | Reject notification mutation errors with optimistic rollback and truthful badge counts |
| SYNC-041 | P0 | G03 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/topbar_navigation.test.js` | User + role + generation fenced notification cache (`_notifFetchGen`). Discard cross-user and cross-role responses |
| SYNC-042 | P0 | G08 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/exam_progression.test.js`, live browser test | User-scoped localStorage keys (`pwd301_azota_exam_draft_<userId>`), memory-only password, role-based draft access. Verified in live browser |
| SYNC-043 | P1 | G08 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/exam_progression.test.js` | Truthful storage failure reporting via `ExamStore.storageFailed` and recovery on success |
| SYNC-044 | P1 | G02 | REVALIDATED | FIXED_VERIFIED | `frontend/assets/js/router.js`, live browser test | Local role switch occurs strictly after server HTTP ACK. Verified across Admin, Instructor, Student in live browser |
| SYNC-045 | P1 | G02 | REVALIDATED | FIXED_VERIFIED | `frontend/assets/js/api.js`, `frontend/assets/js/router.js`, live browser test | Truthful logout server revocation tracking and local state cleanup with warnings on network failure |
| SYNC-046 | P2 | G02 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/api_outcome_contract.test.js` | Reject HTTP 200 `success: false` or unexpected HTML doctype responses in `ApiClient.request` |
| SYNC-047 | P1 | G10 | REVALIDATED | FIXED_VERIFIED | `src/pwd301/services/operations_service.py` | Session-sensitive reauth requiring admin password verification before dangerous operations |
| SYNC-048 | P1 | G01 | REVALIDATED | FIXED_VERIFIED | `src/pwd301/services/operations_service.py:1268` | Forward restore reason from UI to DTO to audit validation (minimum 10 characters) |
| SYNC-049 | P2 | G04 | REVALIDATED | FIXED_VERIFIED | `tests/api/test_admin_subroles_and_enhancements.py` | Atomic composite role assignment/removal with rollback on error in `blueprints/admin/routes.py` |
| SYNC-050 | P2 | G14 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/notification_ui_contract.test.js` | Distinguish genuine empty datasets from error / unauthorized / degraded states |
| SYNC-051 | P2 | G03 | REVALIDATED | FIXED_VERIFIED | `frontend/assets/js/router.js` | Search and filter generation fencing discarding outdated async search results |
| SYNC-052 | P2 | G02 | REVALIDATED | FIXED_VERIFIED | `tests/frontend/router_navigation.test.js` | Await actual route refresh Promise, distinguish committed mutation from refresh failure |
| SYNC-053 | P2 | G11 | REVALIDATED | FIXED_VERIFIED | `src/pwd301/services/operations_service.py`, live browser test | Consume verify ACK and reload backup row status. Verified live in browser: `ApiClient.verifyAdminBackup` returned VERIFIED |
| SYNC-054 | P2 | G01 | REVALIDATED | FIXED_VERIFIED | `src/pwd301/services/operations_service.py` | Validate `PRE_MAINTENANCE` enum roundtrip, reject unsupported enum values with 400 |
| SYNC-055 | P2 | G12 | REVALIDATED | FIXED_VERIFIED | `frontend/assets/js/router.js` | Detail fetch by persisted ID and ownership, reject foreign object access |
| SYNC-056 | P1 | G10 | REVALIDATED | FIXED_VERIFIED | `src/pwd301/services/operations_service.py` | Retry CAS state checking, reject overriding RUNNING background jobs |
| SYNC-057 | P2 | G11 | REVALIDATED | FIXED_VERIFIED | `src/pwd301/services/operations_service.py` | Authoritative maintenance mode check with cross-process coherence |

