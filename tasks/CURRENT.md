# CURRENT TASK

## TASK-010 — Question Bank Management & Question Authoring Engine

**Status:** DONE

### 1. Goal
Xây dựng toàn diện Tầng dịch vụ quản lý Ngân hàng câu hỏi và Động cơ biên soạn câu hỏi (`src/pwd301/services/question_bank_service.py`), bao gồm:
1. **Khởi tạo câu hỏi (Question Creation) & Phiên bản gốc (Initial Revision)**: Tạo đồng thời bản ghi `Question` và `QuestionRevision` (`revision_no=1`, trạng thái `ACTIVE`, `change_type='INITIAL'`), cùng thông tin nguồn gốc câu hỏi (`QuestionProvenance`).
2. **Hỗ trợ đầy đủ 5 loại câu hỏi chuẩn hóa**:
   - `SINGLE_CHOICE`: Tối thiểu 2 lựa chọn, chính xác 1 đáp án đúng (`fraction=1.0`, các đáp án sai `fraction=0.0`).
   - `MULTIPLE_CHOICE`: Tối thiểu 2 lựa chọn, ít nhất 1 đáp án đúng, tổng fraction của các đáp án đúng bằng 1.0 (hoặc 100%).
   - `TRUE_FALSE`: Chính xác 2 lựa chọn ("True" / "False"), chính xác 1 đáp án đúng.
   - `SHORT_ANSWER`: Không dùng choices; lưu danh sách đáp án được chấp nhận (`accepted_answers`) với cơ chế chuẩn hóa chuỗi và tránh trùng lặp; hỗ trợ các chế độ khớp (`EXACT`, `CONTAINS`, `REGEX`, `NORMALIZED`).
   - `ESSAY`: Không dùng choices hay accepted_answers; hỗ trợ stem và hướng dẫn chấm điểm / giải thích (`explanation`).
3. **Phân loại độ khó theo Bloom Taxonomy**: Bắt buộc thuộc tập `{REMEMBER, UNDERSTAND, APPLY}` theo quy chuẩn kỹ thuật hệ thống và ràng buộc cơ sở dữ liệu `ck_questions_1`.
4. **Kiểm soát tính toàn vẹn liên kết bài học (Same-Course Lesson Linkage)**: Câu hỏi thuộc về một Khóa học và có thể liên kết tùy chọn với một Bài học (`primary_lesson_id` / `lesson_id`). Bắt buộc thẩm định bài học phải thuộc cùng khóa học đó, ngăn chặn triệt để liên kết chéo khóa học.
5. **Vòng đời xóa mềm 30 ngày (30-day Retention Trash & Restore Lifecycle)**:
   - Thùng rác (`trash_question`): Chuyển trạng thái `TRASH`, đánh dấu `deleted_at`, ghi nhận `deleted_by_user_id`, thiết lập thời hạn khôi phục `restore_until = now + 30 days`, xử lý idempotent.
   - Khôi phục (`restore_question`): Khôi phục về `ACTIVE`, xóa các mốc thời gian xóa mềm, xử lý idempotent, chặn khôi phục nếu trạng thái không hợp lệ.
6. **Kiểm soát bảo mật và ủy quyền mức đối tượng (IDOR Prevention)**:
   - Xây dựng helper `require_question_manager` trong `authorization_service.py`.
   - Giảng viên chỉ được xem, tạo, xóa, khôi phục câu hỏi trong các khóa học do chính mình phụ trách.
   - Học viên bị từ chối tuyệt đối (HTTP 403 Forbidden).
   - Quản trị viên (Admin) có thẩm quyền giám sát toàn hệ thống.
7. **Bảo toàn nguyên tắc kiến trúc ADR-002 (Internal PK Masking)**: Che giấu toàn bộ khóa chính số nguyên `BIGINT` (`id`, `creator_user_id`, `course_id` nội bộ) trong mọi payload JSON phản hồi; chỉ xuất `public_id` (UUIDv4/UUIDv7) và các thuộc tính nghiệp vụ.
8. **Kiểm toán bất biến (Append-Only Audit Logging)**: Ghi nhận sự kiện kiểm toán `AuditEvent` (`QUESTION_CREATED`, `QUESTION_TRASHED`, `QUESTION_RESTORED`) cùng snapshot dữ liệu `before_json` và `after_json`.
9. **Giao diện Web UI & REST API**:
   - Blueprint REST `api_question_bp` (`/api/questions/...`) bảo vệ bằng `@jwt_required`.
   - Bổ sung endpoints quản lý câu hỏi trong `api_course_bp` (`/api/courses/<course_id>/questions`).
   - Bổ sung Web UI endpoints cho Giảng viên trong `instructor_bp` (`/instructor/courses/<course_id>/questions`, `/instructor/questions/...`).
10. **Bộ kiểm thử toàn diện**: 100% test suite đạt chuẩn (270/270 tests pass), không phát sinh bất kỳ lỗi hồi quy nào.

---

### 2. Source-of-truth documents
- `AGENTS.md` (Hợp đồng vận hành kỹ thuật, quy tắc bất biến, phân quyền và Source-of-Truth Hierarchy).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` (Quy tắc nghiệp vụ ngân hàng câu hỏi).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/06_QUESTION_BANK.md` (Đặc tả chi tiết ngân hàng câu hỏi, quy tắc phiên bản và bài học liên kết).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/06_QUESTION_BANK_API.md` (Đặc tả REST API ngân hàng câu hỏi, mã lỗi chuẩn hóa, tính idempotent).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/003_question_bank.sql` (Canonical DDL tham chiếu Microsoft SQL Server cho ngân hàng câu hỏi).
- `docs/decisions/ADR-002-public-id-and-primary-keys.md` (Quy tắc che giấu BIGINT PK và sử dụng UUID công khai).
- `docs/decisions/ADR-003-question-revisions.md` (Chiến lược phiên bản hóa câu hỏi bất biến).
- `src/pwd301/models/question_bank.py` (Domain models: `Question`, `QuestionRevision`, `QuestionRevisionChoice`, `QuestionRevisionAcceptedAnswer`, `QuestionProvenance`).

---

### 3. In scope
1. **Tầng Ngoại lệ (Domain Exceptions) — `src/pwd301/services/exceptions.py`:**
   - `QuestionBankError(ServiceError)`
   - `QuestionNotFoundError(ResourceNotFoundError, QuestionBankError)`
   - `QuestionValidationError(ValidationError, QuestionBankError)`
   - `QuestionStateViolationError(StateViolationError, QuestionBankError)`
2. **Tầng Dịch vụ (Service Layer) — `src/pwd301/services/question_bank_service.py`:**
   - `create_question(actor, course_id, payload, session)`: Khởi tạo Question, Revision 1, Choices / Accepted Answers, Provenance, và AuditEvent.
   - `list_course_questions(actor, course_id, filters, page, per_page, session)`: Truy vấn danh sách câu hỏi hỗ trợ lọc theo loại, độ khó Bloom, bài học, từ khóa tìm kiếm, và phân trang.
   - `get_question_detail(actor, question_id, session)`: Truy vấn chi tiết câu hỏi, cấu trúc phiên bản, lựa chọn và provenance.
   - `trash_question(actor, question_id, reason, session)`: Đưa câu hỏi vào thùng rác với chính sách 30 ngày lưu trữ và tính idempotent.
   - `restore_question(actor, question_id, reason, session)`: Khôi phục câu hỏi từ thùng rác về trạng thái hoạt động với tính idempotent.
   - `_serialize_question(question, revision, include_answers)`: Chuyển đổi entity thành dictionary tuân thủ ADR-002 che giấu BIGINT PK.
3. **Tầng Phân quyền (Authorization Service) — `src/pwd301/services/authorization_service.py`:**
   - `require_question_manager(actor, question_id, session)`: Thẩm định quyền quản lý câu hỏi mức đối tượng.
4. **Blueprints & Route Handlers:**
   - **REST API Questions Blueprint (`src/pwd301/blueprints/api_questions/`):**
     - `GET /api/questions/<question_id>`
     - `POST /api/questions/<question_id>/trash`
     - `POST /api/questions/<question_id>/restore`
     - `DELETE /api/questions/<question_id>` (Alias của thao tác trash)
   - **REST API Course Questions Routes (`src/pwd301/blueprints/api_courses/routes.py`):**
     - `POST /api/courses/<course_id>/questions`
     - `GET /api/courses/<course_id>/questions`
   - **Instructor Web UI Blueprint (`src/pwd301/blueprints/instructor/routes.py`):**
     - `GET /instructor/courses/<course_id>/questions`
     - `POST /instructor/courses/<course_id>/questions`
     - `GET /instructor/questions/<question_id>`
     - `POST /instructor/questions/<question_id>/trash`
     - `POST /instructor/questions/<question_id>/restore`
     - `DELETE /instructor/questions/<question_id>`
5. **Đăng ký Error Handlers & Exemptions — `src/pwd301/__init__.py`:**
   - Đăng ký bộ xử lý lỗi cho `QuestionNotFoundError`, `QuestionValidationError`, `QuestionStateViolationError`, `QuestionBankError`.
   - Đăng ký blueprint `api_question_bp` và miễn trừ CSRF (`csrf.exempt`).
6. **Kiểm thử tự động toàn diện:**
   - Unit tests (`tests/unit/test_question_bank_service.py`): 15 test cases.
   - Security / IDOR tests (`tests/security/test_question_bank_idor.py`): 10 test cases.
   - REST API integration tests (`tests/api/test_question_bank_api.py`): 11 test cases.
   - Bảo toàn 100% test suite sẵn có (270/270 tests pass).

---

### 4. Out of scope
- Biên tập câu hỏi đã qua sử dụng với cơ chế tạo phiên bản mới (Question Revisioning & Correction Workflow) -> Đợi **TASK-011**.
- Quản lý bài kiểm tra, cấu hình đề thi tự động và động cơ chấm điểm (`assessment_service.py`) -> Đợi **TASK-011**.
- Tích hợp mô hình AI sinh câu hỏi tự động (AI Question Generation) -> Đợi **TASK-012**.

---

### 5. Security & Invariants
- **Bất biến 1 (ADR-002 Internal PK Masking):** Tuyệt đối không để lộ khóa chính số nguyên `BIGINT` (`id`, `creator_user_id`, `course_id`) ra Web/REST JSON; sử dụng `public_id` (UUID) và các thuộc tính nghiệp vụ.
- **Bất biến 2 (Same-Course Lesson Binding):** Câu hỏi chỉ được gắn với bài học thuộc cùng khóa học đó.
- **Bất biến 3 (Bloom Taxonomy Difficulty):** Độ khó câu hỏi bắt buộc thuộc tập giá trị hợp lệ `{REMEMBER, UNDERSTAND, APPLY}` theo quy chuẩn và ràng buộc cơ sở dữ liệu.
- **Bất biến 4 (Question Type Integrity):** Xác thực cấu trúc chặt chẽ cho từng loại câu hỏi (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `ESSAY`).
- **Bất biến 5 (Object-Level Authorization & IDOR Prevention):** Giảng viên chỉ quản lý câu hỏi trong các khóa học do chính mình phụ trách. Học viên bị từ chối truy cập ngân hàng câu hỏi.
- **Bất biến 6 (Append-Only Audit Log):** Mọi thao tác tạo mới, xóa mềm, khôi phục câu hỏi đều được ghi nhận vào `AuditEvent` với snapshot dữ liệu.
- **Bất biến 7 (30-Day Trash Retention & Idempotency):** Câu hỏi đưa vào thùng rác có thời hạn khôi phục 30 ngày; các thao tác trash/restore có tính chất state-idempotent.

---

### 6. Acceptance Criteria (Checklist)
- [x] `exceptions.py` bổ sung đầy đủ domain exceptions `QuestionBankError`, `QuestionNotFoundError`, `QuestionValidationError`, `QuestionStateViolationError`.
- [x] `authorization_service.py` bổ sung `require_question_manager` bảo vệ truy cập mức đối tượng.
- [x] `question_bank_service.py` triển khai toàn diện `create_question`, `list_course_questions`, `get_question_detail`, `trash_question`, `restore_question`, `_serialize_question`.
- [x] Hỗ trợ đầy đủ 5 loại câu hỏi với logic kiểm tra dữ liệu chặt chẽ và chuẩn hóa Bloom Taxonomy.
- [x] Kiểm tra tính toàn vẹn bài học cùng khóa học, ngăn chặn liên kết chéo.
- [x] Xử lý vòng đời xóa mềm 30 ngày (TRASH/restore) và đảm bảo tính idempotent.
- [x] Ghi nhận đầy đủ nhật ký kiểm toán Append-only `AuditEvent`.
- [x] REST API endpoints (`/api/courses/<id>/questions`, `/api/questions/...`) và Web UI routes (`/instructor/...`) hoạt động chuẩn xác, tuân thủ ADR-002.
- [x] Bộ kiểm thử bảo mật IDOR ngăn chặn triệt để truy cập chéo giữa các giảng viên, chặn học viên và người dùng chưa xác thực.
- [x] Toàn bộ hệ thống kiểm thử tự động vượt qua 100% không có lỗi hồi quy (270/270 tests passed).

---

### 7. Verification commands
1. `mypy src` -> Success: no issues found in 50 source files.
2. `ruff check src tests scripts` -> All checks passed!
3. `ruff format --check src tests scripts` -> 83 files already formatted.
4. `pytest tests/unit/test_question_bank_service.py tests/security/test_question_bank_idor.py tests/api/test_question_bank_api.py -v` -> 36 passed in 13.63s.
5. `./scripts/verify.ps1` -> 270 passed in 113.24s (100% PASS, 0 failures).

---

## Completion Report

### A. Scope and sources consulted
- Operating contract: `AGENTS.md` (quy tắc bất biến, phân quyền, Source-of-Truth Hierarchy).
- Question bank business rules: `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` & `06_QUESTION_BANK.md`.
- Question bank REST API specifications: `docs/system/PWD301_SYSTEM_SPECIFICATION/api/06_QUESTION_BANK_API.md`.
- Reference database DDL: `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/003_question_bank.sql`.
- Architectural decisions: `docs/decisions/ADR-002-public-id-and-primary-keys.md` & `ADR-003-question-revisions.md`.
- Domain models: `src/pwd301/models/question_bank.py` & `src/pwd301/models/course.py`.
- Authorization helpers: `src/pwd301/services/authorization_service.py`.

### B. Reuse decisions
- Reused `Question`, `QuestionRevision`, `QuestionRevisionChoice`, `QuestionRevisionAcceptedAnswer`, `QuestionProvenance` models from `src/pwd301/models/question_bank.py`.
- Reused `require_course_manager`, `can_manage_course`, `_resolve_course`, `_resolve_lesson`, `_resolve_user` from `src/pwd301/services/authorization_service.py`.
- Reused `AuditEvent` model from `src/pwd301/models/notification_audit.py` for append-only audit logging with before/after state snapshots.
- Reused `_format_error_response` and centralized error handling architecture in `src/pwd301/__init__.py`.
- Reused `instructor_required`, `jwt_required`, `get_authenticated_actor` decorators for route protection across session web and JWT REST environments.

### C. Per-file changes
- `src/pwd301/services/exceptions.py` (MODIFY): Added domain exceptions `QuestionBankError`, `QuestionNotFoundError`, `QuestionValidationError`, `QuestionStateViolationError`.
- `src/pwd301/services/authorization_service.py` (MODIFY): Implemented `require_question_manager(actor, question_id, session)`.
- `src/pwd301/services/question_bank_service.py` (NEW): Implemented authoring engine, 5 question types, Bloom taxonomy validation, same-course lesson binding check, 30-day TRASH/restore lifecycle with idempotency, append-only `AuditEvent` logging, and ADR-002 BIGINT masking serialization.
- `src/pwd301/services/__init__.py` (MODIFY): Exported question bank service functions and domain exceptions.
- `src/pwd301/blueprints/api_questions/__init__.py` (NEW): Created question bank REST API blueprint package.
- `src/pwd301/blueprints/api_questions/routes.py` (NEW): Implemented REST routes for `GET /api/questions/<id>`, `POST /api/questions/<id>/trash`, `POST /api/questions/<id>/restore`, and `DELETE /api/questions/<id>`.
- `src/pwd301/blueprints/api_courses/routes.py` (MODIFY): Added `POST` & `GET /api/courses/<course_id>/questions` with pagination and multi-criteria filtering.
- `src/pwd301/blueprints/instructor/routes.py` (MODIFY): Implemented instructor Web UI routes for course question list, creation, detail, trash, and restore.
- `src/pwd301/__init__.py` (MODIFY): Registered error handlers for question bank exceptions, registered `api_question_bp`, and marked it `csrf.exempt`.
- `tests/unit/test_question_bank_service.py` (NEW): Implemented 15 unit tests covering all 5 question types, validation errors, lesson binding check, 30-day lifecycle, and Web UI routes.
- `tests/security/test_question_bank_idor.py` (NEW): Implemented 10 security tests covering cross-instructor IDOR denial, foreign lesson binding denial, student blocking, unauthenticated blocking, and admin oversight.
- `tests/api/test_question_bank_api.py` (NEW): Implemented 11 REST API tests for question creation across types, filtering/pagination, detail, lifecycle, delete alias, and ADR-002 verification.
- `tasks/CURRENT.md` (MODIFY): Updated with TASK-010 completion report and promoted TASK-009 to Historical Tasks.

### D. Deletion and simplification list
| Candidate | Classification | Reason | Action |
|---|---|---|---|
| Redundant duplicate accepted answers in short answer questions | REMOVE NOW | SQLite/SQL Server unique constraint `(question_revision_id, answer_normalized)` | Normalized and deduplicated answers during `create_question` |
| Internal `BIGINT PK` in API responses | REMOVE NOW | ADR-002: no internal database BIGINT IDs in public payloads | Serialized all entity IDs as public UUID strings |
| Duplicate error on repeated trash or restore | REMOVE NOW | Specification `06_QUESTION_BANK_API.md`: state-idempotent operations | Return existing entity on idempotent re-trash or re-restore |

### E. Ponytails / deferred debt
- None. Full Question Bank service, authorization helper, Web/REST routes, IDOR protection, and 100% regression testing are completely implemented and verified.

### F. Verification actually run and results
1. `mypy src`:
   ```
   Success: no issues found in 50 source files
   ```
2. `ruff check src tests scripts`:
   ```
   All checks passed!
   ```
3. `ruff format --check src tests scripts`:
   ```
   83 files already formatted
   ```
4. `pytest tests/unit/test_question_bank_service.py tests/security/test_question_bank_idor.py tests/api/test_question_bank_api.py -v`:
   ```
   ============================= 36 passed in 13.63s =============================
   ```
5. `./scripts/verify.ps1`:
   ```
   == Repository contract ==
   PWD301 repository check: E:\PWD301
   [PASS] Required repository contract files exist
   [PASS] No duplicate database architecture/SQL copy under System Specification
   [PASS] Canonical SQL Server DDL contains 71 CREATE TABLE statements
   [PASS] Markdown code fences are balanced
   [NOTE] .env exists locally; ensure it remains ignored by Git
   [PASS] Environment template exists
   [PASS] Repository contract check complete
   == Python compile ==
   == Lint / format / types ==
   All checks passed!
   83 files already formatted
   Success: no issues found in 50 source files
   == Tests ==
   ======================= 270 passed in 113.24s (0:01:53) =======================
   PWD301 verification PASS
   ```

### G. Remaining risks / next step
- Next scheduled task on roadmap: **TASK-011 — Assessment Lifecycle, Test Delivery Engine & Automated Grading (`assessment_service.py`)**.

---

## Historical Tasks

### TASK-009 — Course Progress Engine, Completion Rules & Durable Completion Summaries
**Status:** DONE  
*Triển khai toàn diện Tầng dịch vụ tính toán tiến độ khóa học và động cơ thẩm định hoàn thành (`completion_service.py`), thuật toán Algorithm 01, cấu hình tiêu chí hoàn thành (`CourseCompletionRule`), thẩm định và cấp chứng nhận bền vững (`CourseCompletionSummary`), bảo toàn điều kiện tiên quyết vĩnh viễn (`prerequisite_eligible`), tích hợp hook tự động khi bài học hoàn thành, cùng toàn bộ route Web UI, REST API và bộ test tự động.*

### TASK-008 — Student Enrollment Lifecycle, Capacity, Prerequisites & Re-Enrollment
**Status:** DONE  
*Triển khai toàn diện tầng nghiệp vụ quản lý đăng ký khóa học (`enrollment_service.py`), quản lý chu kỳ học tập (`EnrollmentPeriod`), kiểm soát sĩ số chống race condition (`capacity`), thẩm định điều kiện tiên quyết và phát hiện chu trình đồ thị (Algorithm 03 DFS), xử lý rút lui (`LEFT`) với chính sách lưu trữ chi tiết 30 ngày, tái ghi danh (`re_enroll_student`), tự động chuyển đổi tái ghi danh (Seamless Re-enrollment), bảo đảm tính idempotent, che giấu `BIGINT PK` theo ADR-002, ghi nhận `EnrollmentEvent` và `AuditEvent` append-only, cùng toàn bộ route Web UI, REST API và bộ test tự động.*

### TASK-007 — Lesson Management, Reordering & Completion Tracking
**Status:** DONE  
*Triển khai toàn diện tầng nghiệp vụ (`lesson_service.py`), các ngoại lệ miền (`exceptions.py`), bộ điều khiển route (Web UI & REST API), giải thuật ghi nhận tiến độ (`02_LESSON_COMPLETION_ALGORITHM.md`) và cơ chế tái sắp xếp thứ tự bài học (Lesson Reordering) an toàn với kỹ thuật temporary positive offset `+ 1_000_000`. Tuân thủ nghiêm ngặt ma trận phân quyền (RBAC), phòng chống lỗ hổng IDOR, và ghi nhận Append-only Audit Log.*

### TASK-006 — Course Management, Lifecycle & Ownership/Reassignment
**Status:** DONE  
*Triển khai tầng nghiệp vụ (`course_service.py`), Course State Machine (`DRAFT -> SUBMITTED_FOR_REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED -> TRASH`), soft-delete an toàn với dependency checks, chuyển nhượng quyền sở hữu bởi Admin với Append-only AuditEvent, và hệ thống test toàn diện.*

### TASK-005 — Authorization & Role-Based Access Control (RBAC & Resource Ownership)
**Status:** DONE  
*Xây dựng hệ thống phân quyền (Authorization) toàn diện kết hợp RBAC và Resource/Object-level Authorization ngăn chặn IDOR, decorators `@require_roles`, `@instructor_required`, `@admin_required`, và context resolvers cho cả Web session và JWT.*

### TASK-004 — Authentication & Identity Workflows (Web Session + JWT REST)
**Status:** DONE  
*Xây dựng hệ thống xác thực kép (Dual Authentication): Web UI session cookies với HttpOnly/CSRF protection và REST API JWT Bearer token theo RFC 7519, cùng cơ chế thu hồi phiên và Refresh Token Rotation.*

### TASK-003 — User / Account / Email Verification Foundation
**Status:** DONE  
*Core user account management, password hashing, and secure token lifecycle for email verification and password reset.*

### TASK-002 — Domain Models & Initial SQL Server Migrations
**Status:** DONE  
*Translated canonical database architecture into SQLAlchemy domain models in Flask. Generated baseline Alembic migration script compatible with Microsoft SQL Server, provided idempotent baseline seed script (`flask seed-baseline`), and verified all invariants.*

### TASK-001 — Project Foundation & Flask Bootstrap
**Status:** DONE  
*Completed foundation bootstrap including Flask application factory, configuration classes, extension shells, `/health` and `/` routes, error handlers, and smoke test suite.*
