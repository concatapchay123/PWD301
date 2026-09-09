# CURRENT TASK

## TASK-011 — Question Revision Engine & Question Correction Mechanism

**Status:** DONE

### 1. Goal
Xây dựng Động cơ quản lý phiên bản câu hỏi (`QuestionRevision`) và Cơ chế sửa đổi câu hỏi đã sử dụng (`QuestionCorrection`), bảo đảm tính bất biến của lịch sử thi cử và tính toàn vẹn khi chấm điểm:
1. **Kiểm tra trạng thái sử dụng câu hỏi (In-Use Detection)**:
   - Xây dựng hàm `is_question_in_use(question, session)`.
   - Nhận diện câu hỏi đã xuất hiện trong bài thi xuất bản (`Assessment.status == 'PUBLISHED'` qua `AssessmentQuestionAssignment` hoặc `AssessmentQuestionPool`).
   - Nhận diện câu hỏi đã có lượt làm bài (`AttemptQuestion.source_question_id == question.id`).
   - Nhận diện câu hỏi có `usage_count > 0` hoặc `first_used_at is not None`.
   - Nhận diện câu hỏi có phiên bản đã hiển thị cho học viên (`was_student_exposed`) hoặc dùng chấm điểm (`was_used_for_grading`).
2. **Cơ chế phân nhánh chỉnh sửa (Branching Update Strategy)**:
   - *Chưa sử dụng (Unused)*: Cho phép cập nhật tại chỗ (`in-place`) nội dung stem, choices, accepted answers, explanation mà không sinh revision mới (trừ khi yêu cầu rõ ràng).
   - *Đã sử dụng (In-Use)*: Đóng băng revision cũ (`Freeze Revision Invariant`), tự động phân nhánh tạo `QuestionRevision` mới (`revision_no = latest + 1`), cấm đổi loại câu hỏi (`QuestionImmutableError`), yêu cầu bắt buộc có lý do sửa đổi `change_reason` (`QuestionValidationError`), và tự động sinh bản ghi `QuestionCorrection` (status `PENDING`) liên kết `from_revision_id` và `to_revision_id` phục vụ chấm lại sau này.
3. **Chuẩn hóa change_type & correction_type**:
   - `change_type`: `INITIAL`, `EDIT`, `TYPO_FIX`, `ANSWER_CHANGE`, `CONTENT_CHANGE`, `REVOCATION`.
   - `correction_type`: `ANSWER_ONLY` (cho các thay đổi đáp án / key), `CONTENT_OR_CHOICES` (cho thay đổi nội dung, thêm/bớt lựa chọn).
4. **Bảo tồn và sao chép sâu cấu trúc (Deep Cloning)**:
   - Tự động nhân bản các lựa chọn (`QuestionRevisionChoice`) và đáp án được chấp nhận (`QuestionRevisionAcceptedAnswer`) sang revision mới khi không bị ghi đè, cấp phát `choice_key` / `public_id` mới nhằm bảo toàn tính độc lập.
5. **Kiểm soát bảo mật và ủy quyền mức đối tượng (IDOR Prevention)**:
   - Thẩm định quyền qua `require_question_manager`.
   - Giảng viên chỉ được quản lý câu hỏi trong các khóa học do chính mình phụ trách.
   - Học viên bị từ chối truy cập mọi endpoint revision/correction (HTTP 403 Forbidden).
   - Quản trị viên (Admin) có toàn quyền quản lý trên toàn hệ thống.
6. **Bảo toàn nguyên tắc kiến trúc ADR-002 (Internal PK Masking)**:
   - Che giấu toàn bộ khóa chính số nguyên `BIGINT` (`id`, `creator_user_id`, `question_revision_id`, `actor_user_id`) trong mọi payload JSON.
   - Sử dụng UUIDv5 định danh cho `correction_id` để che giấu `BIGINT PK` của bảng `question_corrections` (do canonical schema không có cột public_id) mà vẫn bảo đảm tính đơn nhất và tuân thủ UUID regex.
7. **Kiểm toán bất biến (Append-Only Audit Logging)**:
   - Ghi nhận sự kiện kiểm toán `AuditEvent` (`QUESTION_REVISED`, `QUESTION_CORRECTION_CREATED`) cùng snapshot metadata.
8. **Giao diện Web UI & REST API**:
   - `PATCH /api/questions/<question_id>` & `PATCH /instructor/questions/<question_id>`
   - `GET /api/questions/<question_id>/revisions` & `GET /instructor/questions/<question_id>/revisions`
   - `POST /api/questions/<question_id>/revisions` & `POST /instructor/questions/<question_id>/revisions`
   - `GET /api/questions/<question_id>/revisions/<revision_no>` & `GET /instructor/questions/<question_id>/revisions/<revision_no>`
   - `GET /api/questions/<question_id>/corrections` & `GET /instructor/questions/<question_id>/corrections`
9. **Bộ kiểm thử tự động toàn diện**:
   - Unit tests (`tests/unit/test_question_revision_service.py`): 18 tests.
   - Security IDOR tests (`tests/security/test_question_revision_idor.py`): 10 tests.
   - REST API integration tests (`tests/api/test_question_revision_api.py`): 9 tests.
   - 100% test suite đạt chuẩn, không hồi quy (307/307 tests pass).

---

### 2. Source-of-truth documents
- `AGENTS.md` (Hợp đồng vận hành kỹ thuật, quy tắc bất biến, phân quyền và Source-of-Truth Hierarchy).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` (Quy tắc nghiệp vụ ngân hàng câu hỏi và chấm thi).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/06_QUESTION_BANK.md` (Đặc tả chi tiết Question Bank, Question Revisioning và Freeze Invariant).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md` (Quy tắc bất biến: Historical QuestionRevision data retained, locked after publish/first attempt).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/06_QUESTION_BANK_API.md` (Đặc tả REST API cho Question Revisions & Corrections).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/003_question_bank.sql` (Canonical DDL tham chiếu Microsoft SQL Server cho `question_revisions`).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/005_attempt_regrade.sql` (Canonical DDL tham chiếu Microsoft SQL Server cho `question_corrections` và `attempt_questions`).
- `docs/decisions/ADR-002-public-id-and-primary-keys.md` (Quy tắc che giấu BIGINT PK và sử dụng UUID công khai).
- `docs/decisions/ADR-003-question-revisions.md` (Chiến lược phiên bản hóa câu hỏi bất biến).

---

### 3. In scope
1. **Tầng Ngoại lệ (Domain Exceptions) — `src/pwd301/services/exceptions.py`:**
   - `StateViolationError(ServiceError)`
   - `QuestionRevisionNotFoundError(ResourceNotFoundError)`
   - `QuestionRevisionConflictError(ConflictError)`
   - `QuestionImmutableError(ConflictError)`
   - `QuestionCorrectionError(QuestionBankError)`
2. **Mô hình Dữ liệu & DDL (Domain Models & DDL) — `src/pwd301/models/question_bank.py` & `sql/003_question_bank.sql`:**
   - Cập nhật ràng buộc `ck_question_revisions_4` mở rộng hỗ trợ: `INITIAL`, `EDIT`, `ANSWER_ONLY`, `CONTENT_OR_CHOICES`, `TYPO_FIX`, `ANSWER_CHANGE`, `CONTENT_CHANGE`, `REVOCATION`.
3. **Tầng Dịch vụ (Service Layer) — `src/pwd301/services/question_bank_service.py`:**
   - `is_question_in_use(question, session)`
   - `create_question_revision(actor, question_id, payload, session)`
   - `update_question(actor, question_id, payload, session)`
   - `list_question_revisions(actor, question_id, page, per_page, session)`
   - `get_question_revision_detail(actor, question_id, revision_no, session)`
   - `list_question_corrections(actor, question_id, session)`
   - `_serialize_question_revision(rev, is_current, include_answers)`
   - `_serialize_question_correction(correction)`
4. **Blueprints & Route Handlers:**
   - **REST API Questions Blueprint (`src/pwd301/blueprints/api_questions/routes.py`):**
     - `PATCH /api/questions/<question_id>`
     - `GET /api/questions/<question_id>/revisions`
     - `POST /api/questions/<question_id>/revisions`
     - `GET /api/questions/<question_id>/revisions/<int:revision_no>`
     - `GET /api/questions/<question_id>/corrections`
   - **Instructor Web UI Blueprint (`src/pwd301/blueprints/instructor/routes.py`):**
     - `PATCH /instructor/questions/<question_id>`
     - `GET /instructor/questions/<question_id>/revisions`
     - `POST /instructor/questions/<question_id>/revisions`
     - `GET /instructor/questions/<question_id>/revisions/<int:revision_no>`
     - `GET /instructor/questions/<question_id>/corrections`
5. **Đăng ký Error Handlers — `src/pwd301/__init__.py`:**
   - Đăng ký bộ xử lý lỗi cho `QuestionRevisionNotFoundError` (404), `QuestionRevisionConflictError` (409), `QuestionImmutableError` (409), `QuestionCorrectionError` (400).
6. **Kiểm thử tự động:**
   - Unit tests (`tests/unit/test_question_revision_service.py`): 18 tests.
   - Security IDOR tests (`tests/security/test_question_revision_idor.py`): 10 tests.
   - REST API integration tests (`tests/api/test_question_revision_api.py`): 9 tests.
   - Bảo đảm 100% test suite sẵn có không hồi quy.

---

### 4. Out of scope
- Quản lý bài thi, phòng thi và động cơ chấm bài thi tự động (`assessment_service.py`) -> Thuộc về **TASK-012**.
- Động cơ chấm lại tự động theo đợt (Batch Regrading Engine) dựa trên `QuestionCorrection` -> Thuộc về **TASK-013**.
- Tích hợp AI sinh câu hỏi tự động (AI Question Generation) -> Thuộc về giai đoạn sau.

---

### 5. Completion Report

#### A. Scope & Source-of-Truth Files Consulted
- `AGENTS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/06_QUESTION_BANK.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/06_QUESTION_BANK_API.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/003_question_bank.sql`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/005_attempt_regrade.sql`
- `docs/decisions/ADR-002-public-id-and-primary-keys.md`
- `docs/decisions/ADR-003-question-revisions.md`

#### B. Reuse Decisions
- Tái sử dụng `require_question_manager` từ `authorization_service.py` cho toàn bộ các thao tác kiểm tra quyền truy cập trên revisions và corrections.
- Tái sử dụng `_record_question_audit` từ `question_bank_service.py` để ghi nhận `QUESTION_REVISED` và `QUESTION_CORRECTION_CREATED`.
- Tái sử dụng cấu trúc `_serialize_question_revision` đồng bộ giữa chi tiết câu hỏi (`_serialize_question`), danh sách revision, và chi tiết revision.
- Sử dụng UUIDv5 xuất phát từ `correction.id` và namespace DNS `pwd301.question_correction.{id}` để che giấu `BIGINT PK` mà không cần thay đổi cấu trúc bảng cơ sở dữ liệu đã chốt.

#### C. Per-File Changes
- `src/pwd301/services/exceptions.py`: Bổ sung `StateViolationError`, `QuestionRevisionNotFoundError`, `QuestionRevisionConflictError`, `QuestionImmutableError`, `QuestionCorrectionError`.
- `src/pwd301/models/question_bank.py`: Cập nhật ràng buộc `ck_question_revisions_4` mở rộng danh sách `change_type`.
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/003_question_bank.sql`: Cập nhật check constraint `ck_question_revisions_4` trong canonical SQL Server DDL.
- `src/pwd301/services/question_bank_service.py`: Triển khai các hàm nghiệp vụ `is_question_in_use`, `create_question_revision`, `update_question`, `list_question_revisions`, `get_question_revision_detail`, `list_question_corrections`, `_serialize_question_correction`.
- `src/pwd301/services/__init__.py`: Re-export các ngoại lệ và hàm nghiệp vụ mới.
- `src/pwd301/__init__.py`: Đăng ký các HTTP error handler (400, 404, 409).
- `src/pwd301/blueprints/api_questions/routes.py`: Triển khai các endpoints REST API revisions, corrections và update.
- `src/pwd301/blueprints/instructor/routes.py`: Triển khai các Web UI endpoints revisions, corrections và update.
- `tests/unit/test_question_revision_service.py`: 18 unit tests cho logic nghiệp vụ.
- `tests/security/test_question_revision_idor.py`: 10 security & IDOR negative tests.
- `tests/api/test_question_revision_api.py`: 9 integration & ADR-002 REST API tests.

#### D. Deletion / Simplification List
- Loại bỏ các câu lệnh if/else thủ công lặp lại trong route handlers; chuyển toàn bộ thẩm định quyền vào `require_question_manager`.
- Đơn giản hóa việc tính toán `correction_type` tự động dựa trên `change_type` (`ANSWER_CHANGE` -> `ANSWER_ONLY`, `TYPO_FIX`/`CONTENT_CHANGE` -> `CONTENT_OR_CHOICES`).

#### E. Ponytails / Deferred Technical Debt
- None. Toàn bộ yêu cầu bất biến, che giấu khóa chính, phân quyền IDOR và kiểm thử tự động đều được giải quyết triệt để.

#### F. Verification Actually Run & Results
1. `scripts/repo_check.py`: PASS (71 canonical SQL tables verified, required files exist).
2. `ruff check src tests scripts`: PASS (All checks passed).
3. `ruff format --check src tests scripts`: PASS (86 files already formatted).
4. `mypy src`: PASS (Success: no issues found in 50 source files).
5. Pytest suite: 307 passed (37 new tests + 270 baseline tests, 0 failures, 0 regressions).

#### G. Remaining Risks / Next Step
- Tiếp tục theo lộ trình sang **TASK-012 — Assessment Lifecycle, Test Delivery Engine & Automated Grading (`assessment_service.py`)**.

---

## Historical Tasks

### TASK-010 — Question Bank Management & Question Authoring Engine
**Status:** DONE  
*Xây dựng toàn diện Tầng dịch vụ quản lý Ngân hàng câu hỏi và Động cơ biên soạn câu hỏi (`question_bank_service.py`), hỗ trợ 5 loại câu hỏi chuẩn hóa (`SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `ESSAY`), phân loại Bloom Taxonomy, kiểm soát bài học liên kết, vòng đời xóa mềm 30 ngày, phòng chống IDOR, che giấu BIGINT PK theo ADR-002, và kiểm toán bất biến.*

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
