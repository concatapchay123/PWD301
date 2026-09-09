# CURRENT TASK

## TASK-012 — Assessment Builder, Blueprint Materialization & Publish Rules Engine

**Status:** DONE

### 1. Goal
Xây dựng Động cơ quản lý bài thi (`assessment_service.py`), hệ thống phân đoạn (`AssessmentSection`), gán câu hỏi tĩnh (`AssessmentQuestionAssignment`), cấu hình ma trận đề thi động (`AssessmentBlueprint`), tạo hồ câu hỏi ngẫu nhiên theo luật (Algorithm 05 Question Pool Materialization), cùng cơ chế khóa bất biến khi xuất bản (Publish Rules, Timing Freeze & Structural Freeze Invariants):
1. **Khởi tạo và cấu hình bài thi (Assessment Lifecycle)**:
   - Quản lý vòng đời trạng thái: `DRAFT -> PUBLISHED -> CANCELLED / ARCHIVED -> TRASH`.
   - Hỗ trợ 5 loại bài thi chuẩn hóa: `PRACTICE`, `QUIZ`, `MIDTERM`, `FINAL`, `PLACEMENT`.
   - Cấu hình chính sách tính điểm (`FIRST`, `LATEST`, `HIGHEST`, `AVERAGE`), chính sách công bố điểm (`IMMEDIATE`, `AFTER_CLOSE`, `INSTRUCTOR_RELEASE`), chính sách hiển thị đáp án (`IMMEDIATE`, `AFTER_CLOSE`, `AFTER_ALL_ATTEMPTS`, `NEVER`).
   - Kiểm soát và thẩm định chéo thời gian mở/đóng (`open_at < close_at`), giới hạn thời gian làm bài (`time_limit_minutes > 0`), giới hạn số lượt nộp (`attempt_limit > 0`), tỷ lệ đạt (`passing_percent` trong khoảng `[0, 100]`).
2. **Quản lý phân đoạn bài thi (Section Management)**:
   - Thêm, sửa, xóa các phân đoạn bài thi (`AssessmentSection`) chứa tiêu đề, chỉ dẫn và vị trí (`position`).
   - Tự động chuẩn hóa và dồn vị trí khi xóa phân đoạn.
3. **Gán câu hỏi cố định (Fixed Question Assignments)**:
   - Gán câu hỏi từ ngân hàng câu hỏi vào bài thi / phân đoạn (`AssessmentQuestionAssignment`).
   - Ngăn chặn triệt để gán trùng câu hỏi trong cùng một bài thi (`AssessmentValidationError`).
   - Phòng thủ chéo khóa học (Cross-Course Defense): cấm gán câu hỏi thuộc khóa học khác vào bài thi (`AssessmentValidationError`).
   - Xóa gán câu hỏi và tự động dồn lại thứ tự vị trí (`position`).
4. **Động cơ ma trận đề thi & Algorithm 05 (Blueprint & Question Pool Materialization)**:
   - Cấu hình đề cương ma trận (`AssessmentBlueprint`) và các quy tắc phân bổ (`AssessmentBlueprintRule`) theo độ khó Bloom (`REMEMBER`, `UNDERSTAND`, `APPLY`), loại câu hỏi, bài học liên kết, số lượng câu hỏi và điểm số tương ứng.
   - Triển khai Giải thuật Algorithm 05 (`materialize_blueprint_pool`): truy vấn các câu hỏi hợp lệ (`status == 'ACTIVE'`), loại trừ các câu hỏi đã được gán cố định, phân bổ ngẫu nhiên có hỗ trợ `random_seed` để tái tạo đề thi tất định.
   - Cơ chế phát hiện thiếu hụt câu hỏi (Shortage Handling): nếu số lượng câu hỏi hợp lệ trong ngân hàng không đủ đáp ứng luật đề cương, báo lỗi `BlueprintValidationError` và rollback toàn bộ, không để lại dữ liệu rác hoặc pool không hoàn chỉnh.
5. **Cổng kiểm soát xuất bản (Publish Rules Engine — AC-05)**:
   - Thẩm định điều kiện xuất bản bài thi: yêu cầu phải có ít nhất 1 câu hỏi (hoặc trong fixed assignments hoặc trong question pool), tổng điểm tích lũy phải lớn hơn 0, và thời gian `open_at` phải trước `close_at`.
   - Chuyển trạng thái sang `PUBLISHED`, đóng dấu `published_at`, đồng thời đóng băng tất cả blueprint liên kết (`status = 'FROZEN'`).
   - Bảo đảm tính State-idempotent: gọi xuất bản nhiều lần trên bài thi đã `PUBLISHED` không gây lỗi.
6. **Quy tắc khóa bất biến khi thi (Timing & Structural Freeze Invariants)**:
   - **Timing Freeze Invariant (ASSESS-001)**: Khi bài thi đã xuất bản (`PUBLISHED`), các trường `open_at`, `time_limit_minutes`, `attempt_limit` bị khóa hoàn toàn (báo lỗi `AssessmentLockedError`). Trường `close_at` chỉ được phép gia hạn tịnh tiến về tương lai (nếu rút ngắn hoặc đẩy lùi sẽ bị từ chối bằng `AssessmentLockedError`).
   - **Structural Freeze Invariant (ASSESS-002, AC-06)**: Khi học viên đầu tiên bắt đầu làm bài (`first_attempt_started_at is not None`), toàn bộ cấu trúc bài thi bị đóng băng vĩnh viễn. Mọi hành vi thêm/sửa/xóa section, gán/xóa câu hỏi, sửa đổi blueprint hoặc tạo lại question pool đều bị chặn với mã lỗi HTTP 409 Conflict (`AssessmentLockedError`).
7. **Chính sách xóa mềm và khôi phục 30 ngày (Soft-Delete & 30-Day Restore Window)**:
   - Chuyển trạng thái sang `TRASH`, thiết lập `deleted_at = utc_now()` và `restore_until = utc_now() + 30 days`.
   - Cho phép khôi phục về `DRAFT` trong vòng 30 ngày. Quá hạn 30 ngày, hệ thống từ chối khôi phục (`AssessmentValidationError`).
8. **Bảo toàn nguyên tắc kiến trúc ADR-002 (Internal PK Masking)**:
   - Che giấu toàn bộ khóa chính số nguyên `BIGINT` (`id`, `creator_user_id`, `course_id`, `section_id`, `assignment_id`, `blueprint_id`, `rule_id`) trong toàn bộ REST API và Web UI JSON payload.
   - Sử dụng UUIDv5 tất định cho các bảng con chỉ có `BIGINT PK` (`assessment_sections`, `assessment_question_assignments`, `assessment_blueprints`, `assessment_blueprint_rules`, `assessment_question_pool`) để bảo đảm 100% tuân thủ RFC 4122 UUID.
9. **Kiểm toán bất biến (Append-Only Audit Logging)**:
   - Ghi nhận `AuditEvent` cho mọi hành vi quan trọng: `ASSESSMENT_CREATED`, `ASSESSMENT_UPDATED`, `ASSESSMENT_PUBLISHED`, `ASSESSMENT_CANCELLED`, `ASSESSMENT_TRASHED`, `ASSESSMENT_RESTORED`.
10. **Toàn diện REST API & Web UI Route Handlers**:
    - Course-scoped routes (`/api/courses/<course_id>/assessments`).
    - Assessment management routes (`/api/assessments`, `/api/assessments/<id>`, `/api/assessments/<id>/sections`, `/api/assessments/<id>/questions`, `/api/assessments/<id>/blueprint`, `/api/assessments/<id>/blueprint/materialize`, `/api/assessments/<id>/publish`, `/api/assessments/<id>/cancel`, `/api/assessments/<id>/trash`, `/api/assessments/<id>/restore`).
    - Instructor Web UI routes (`/instructor/courses/<course_id>/assessments`, `/instructor/assessments/<id>`, etc.).

---

### 2. Source-of-truth documents
- `AGENTS.md` (Hợp đồng vận hành kỹ thuật, quy tắc bất biến, phân quyền và Source-of-Truth Hierarchy).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md` (Quy tắc nghiệp vụ bài thi, quản lý phân đoạn và ma trận đề).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/07_ASSESSMENT_SYSTEM.md` (Đặc tả chi tiết Assessment Lifecycle, Blueprint & Materialization Algorithm 05).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md` (Quy tắc bất biến: Assessment timing locked after publish, Question structure locked after first attempt started).
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/07_ASSESSMENT_API.md` (Đặc tả chuẩn REST API cho Assessments, Sections, Questions & Blueprints).
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/004_assessment.sql` (Canonical DDL tham chiếu Microsoft SQL Server cho `assessments`, `assessment_sections`, `assessment_question_assignments`, `assessment_blueprints`, `assessment_blueprint_rules`, `assessment_question_pool`).
- `docs/decisions/ADR-002-public-id-and-primary-keys.md` (Quy tắc che giấu BIGINT PK và sử dụng UUID công khai).

---

### 3. In scope
1. **Tầng Ngoại lệ (Domain Exceptions) — `src/pwd301/services/exceptions.py`:**
   - `AssessmentError(ServiceError)`
   - `AssessmentNotFoundError(ResourceNotFoundError)`
   - `AssessmentValidationError(ValidationError)`
   - `AssessmentStateViolationError(StateViolationError)`
   - `AssessmentLockedError(ConflictError)`
   - `AssessmentSectionNotFoundError(ResourceNotFoundError)`
   - `BlueprintValidationError(ValidationError)`
2. **Tầng Dịch vụ (Service Layer) — `src/pwd301/services/assessment_service.py`:**
   - Quản lý Lifecycle: `create_assessment`, `get_assessment_detail`, `update_assessment`, `publish_assessment`, `cancel_assessment`, `trash_assessment`, `restore_assessment`, `list_course_assessments`.
   - Quản lý Section: `create_section`, `delete_section`.
   - Quản lý Gán câu hỏi: `assign_question`, `remove_question_assignment`.
   - Quản lý Ma trận & Algorithm 05: `configure_blueprint`, `materialize_blueprint_pool`.
   - Serializers che giấu PK: `_serialize_assessment`, `_serialize_section`, `_serialize_assignment`, `_serialize_blueprint`, `_serialize_blueprint_rule`.
   - Timezone normalization helper: `_normalize_dt`.
   - Audit logging helper: `_record_assessment_audit`.
3. **Re-export Tầng Dịch vụ — `src/pwd301/services/__init__.py`:**
   - Export đầy đủ tất cả các hàm và ngoại lệ mới trong `__all__`.
4. **Blueprints & Route Handlers:**
   - **REST API Assessment Blueprint (`src/pwd301/blueprints/api_assessments/`):**
     - Đăng ký blueprint `api_assessment_bp` với url_prefix `/api/assessments`.
     - Triển khai 13 endpoints REST API theo đặc tả `07_ASSESSMENT_API.md`.
   - **Course-Scoped Assessment Routes (`src/pwd301/blueprints/api_courses/routes.py`):**
     - `POST /api/courses/<course_id>/assessments`
     - `GET /api/courses/<course_id>/assessments`
   - **Instructor Web UI Blueprint (`src/pwd301/blueprints/instructor/routes.py`):**
     - Triển khai 14 instructor assessment view & action routes.
5. **Đăng ký Error Handlers & CSRF Exemption — `src/pwd301/__init__.py`:**
   - Đăng ký `api_assessment_bp`.
   - Cấu hình `csrf.exempt(api_assessment_bp)`.
   - Đăng ký các HTTP error handler cho `AssessmentNotFoundError` (404), `AssessmentSectionNotFoundError` (404), `AssessmentLockedError` (409), `AssessmentStateViolationError` (409), `AssessmentValidationError` (400), `BlueprintValidationError` (400).
6. **Kiểm thử tự động:**
   - Unit tests (`tests/unit/test_assessment_service.py`): 13 tests.
   - Security & IDOR negative tests (`tests/security/test_assessment_idor.py`): 4 tests.
   - REST API integration tests (`tests/api/test_assessment_api.py`): 7 tests.
   - Bảo đảm 100% test suite sẵn có không hồi quy (331/331 tests pass).

---

### 4. Out of scope
- Quản lý phiên làm bài của học viên và động cơ nộp bài / tính điểm tức thời (`AttemptService`, `AssessmentAttempt`) -> Thuộc về **TASK-013**.
- Động cơ chấm lại tự động theo đợt (Batch Regrading Engine) dựa trên `QuestionCorrection` -> Thuộc về **TASK-014**.
- Chống gian lận thời gian thực qua WebRTC / AI Proctoring -> Thuộc về giai đoạn sau.

---

### 5. Completion Report

#### A. Scope & Source-of-Truth Files Consulted
- `AGENTS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/01_BUSINESS_RULE_CATALOG.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/07_ASSESSMENT_SYSTEM.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/06_NON_NEGOTIABLE_INVARIANTS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/07_ASSESSMENT_API.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/sql/004_assessment.sql`
- `docs/decisions/ADR-002-public-id-and-primary-keys.md`

#### B. Reuse Decisions
- Tái sử dụng `require_course_manager` và `can_manage_course` từ `authorization_service.py` để bảo đảm tính thống nhất trong kiểm tra quyền sở hữu khóa học giữa giảng viên và quản trị viên.
- Tái sử dụng `_resolve_course` từ `course_service.py` cho các tham số đầu vào `course_id` đa hình (hỗ trợ `Course`, `public_id`, chuỗi số nguyên hoặc integer).
- Tái sử dụng `_serialize_question` từ `question_bank_service.py` để đính kèm thông tin tóm tắt câu hỏi vào danh sách câu hỏi gán cố định mà không làm lộ đáp án đúng.
- Tái sử dụng `jwt_required` và `get_authenticated_actor` cho toàn bộ các endpoint REST API trong `api_assessment_bp`.
- Che giấu các khóa chính số nguyên `BIGINT PK` của các bảng con (`assessment_sections`, `assessment_question_assignments`, `assessment_blueprints`, `assessment_blueprint_rules`, `assessment_question_pool`) bằng UUIDv5 có namespace DNS `pwd301.<entity>.{id}`, thỏa mãn ADR-002 mà không cần sửa đổi canonical SQL schema.

#### C. Per-File Changes
- `src/pwd301/services/exceptions.py`: Bổ sung 7 ngoại lệ miền nghiệp vụ chuyên biệt: `AssessmentError`, `AssessmentNotFoundError`, `AssessmentValidationError`, `AssessmentStateViolationError`, `AssessmentLockedError`, `AssessmentSectionNotFoundError`, `BlueprintValidationError`.
- `src/pwd301/services/assessment_service.py`: Triển khai toàn bộ logic nghiệp vụ đánh giá, quản lý phân đoạn, gán câu hỏi tĩnh, thuật toán Algorithm 05 sinh đề từ blueprint, cổng kiểm soát xuất bản, quy tắc đóng băng thời gian và cấu trúc, chuẩn hóa timezone UTC, xóa mềm 30 ngày và ghi kiểm toán bất biến.
- `src/pwd301/services/__init__.py`: Re-export toàn bộ ngoại lệ và hàm nghiệp vụ của assessment service.
- `src/pwd301/__init__.py`: Đăng ký `api_assessment_bp`, miễn trừ CSRF cho blueprint REST API, và đăng ký các HTTP error handler (400, 404, 409).
- `src/pwd301/blueprints/api_assessments/__init__.py`: Khởi tạo blueprint `api_assessment_bp`.
- `src/pwd301/blueprints/api_assessments/routes.py`: Triển khai 13 endpoint REST API quản lý bài thi, phân đoạn, câu hỏi, blueprint và materialization.
- `src/pwd301/blueprints/api_courses/routes.py`: Bổ sung route `POST` và `GET` `/api/courses/<course_id>/assessments`.
- `src/pwd301/blueprints/instructor/routes.py`: Bổ sung 14 route điều khiển Web UI cho giảng viên quản lý bài thi.
- `tests/unit/test_assessment_service.py`: 13 unit tests bao phủ toàn bộ lifecycle, publish gate, timing freeze, structural freeze, fixed assignments, Algorithm 05 và 30-day restore.
- `tests/security/test_assessment_idor.py`: 4 security tests ngăn chặn IDOR giữa các giảng viên, ngăn chặn học viên truy cập, và xác nhận quyền superuser của Admin.
- `tests/api/test_assessment_api.py`: 7 integration tests kiểm thử toàn diện REST API, xác thực JWT, phân trang, và kiểm định ADR-002 không rò rỉ BIGINT PK.

#### D. Deletion / Simplification List
- Đơn giản hóa việc tính toán tổng điểm và tổng số câu hỏi bằng cách truy vấn trực tiếp cơ sở dữ liệu qua session trong `_calculate_assessment_aggregates`, loại bỏ nguy cơ mất đồng bộ bộ nhớ đệm quan hệ SQLAlchemy.
- Chuẩn hóa toàn bộ việc so sánh datetime qua helper `_normalize_dt`, giải quyết triệt để lỗi TypeError so sánh giữa naive datetime (từ SQLite) và aware datetime (từ payload ISO-8601).

#### E. Ponytails / Deferred Technical Debt
- None. Toàn bộ các quy tắc bất biến, kiểm tra quyền hạn, che giấu khóa chính, và giải thuật materialization đều được hiện thực hóa và kiểm thử tự động 100%.

#### F. Verification Actually Run & Results
1. `scripts/repo_check.py`: PASS (71 canonical SQL tables verified, balanced code fences, required files present).
2. `ruff check src tests scripts`: PASS (All checks passed across 92 files).
3. `ruff format --check src tests scripts`: PASS (92 files already formatted).
4. `mypy src`: PASS (Success: no issues found in 53 source files).
5. Pytest suite: 331 passed (24 new tests + 307 baseline tests, 0 failures, 0 regressions).
6. `scripts/verify.ps1`: PASS (All repository contract checks, compile checks, lint/format/type checks, and unit/integration/security tests passed).

#### G. Remaining Risks / Next Step
- Sẵn sàng chuyển tiếp sang **TASK-013 — Student Assessment Delivery, Active Editing Lease & Idempotent Submission Engine (`attempt_service.py`)**.

---

## Historical Tasks

### TASK-011 — Question Revisioning, In-Use Freeze & Correction Mechanism
**Status:** DONE  
*Xây dựng Động cơ quản lý phiên bản câu hỏi (`QuestionRevision`) và Cơ chế sửa đổi câu hỏi đã sử dụng (`QuestionCorrection`), bảo đảm tính bất biến của lịch sử thi cử và tính toàn vẹn khi chấm điểm, kiểm tra in-use tự động, phân nhánh chỉnh sửa, bảo tồn cấu trúc choices/answers, phòng chống IDOR, che giấu BIGINT PK theo ADR-002, và ghi nhận kiểm toán bất biến.*

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
