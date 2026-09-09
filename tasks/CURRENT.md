# TASK-017 — Regrading Engine & Score History Implementation

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-010, TASK-011, TASK-014, TASK-015, TASK-016  

---

## 1. Goal & Architectural Purpose
Triển khai hoàn chỉnh toàn diện Động cơ chấm lại (Regrading Engine) và Lịch sử biến động điểm số (Score History) theo đúng Algorithm 11, Business Rules 07 & 10, State Machine `REGRADING_STATE_MACHINE.md`, APIs `07_ASSESSMENT_API.md` & `08_ATTEMPT_API.md`, ADR-002, và hợp đồng vận hành `AGENTS.md`:
1. **Algorithm 11 Regrading Logic**:
   - `ANSWER_ONLY`: Chấm lại tự động theo revision mới của câu hỏi (SINGLE_CHOICE, MULTIPLE_CHOICE, SHORT_ANSWER với chuẩn hóa NFKC / exact matching); chỉ cập nhật điểm của thí sinh đã làm câu hỏi này; ghi nhận `reason_code='AUTO_REGRADE'` vào `AttemptQuestionGradeHistory`.
   - `CONTENT_OR_CHOICES`: Áp dụng Full-Credit Safety Policy; tự động tặng trọn điểm tối đa (`points_assigned`) cho tất cả thí sinh bị ảnh hưởng bởi câu hỏi có nội dung hoặc lựa chọn bị lỗi; ghi nhận `reason_code='FULL_CREDIT'`.
2. **Strict Skip Logic**:
   - Thí sinh có bài làm bị thanh lọc chi tiết (`is_detail_purged=True`) -> đánh dấu `RegradeItem.status='SKIPPED'`, `skip_reason='DETAIL_PURGED'`.
   - Thí sinh có bài làm bị hủy (`status='CANCELLED'`) -> đánh dấu `RegradeItem.status='SKIPPED'`, `skip_reason='CANCELLED'`.
   - Bài thi chưa nộp (`CREATED`, `IN_PROGRESS`) không tham gia job chấm lại.
3. **Audit Trail & Score History**:
   - Mọi thay đổi điểm số từng câu hỏi được ghi nhận vào `AttemptQuestionGradeHistory` (bất biến, append-only).
   - Mọi thay đổi điểm số tổng thể (`raw_score`) được ghi nhận vào `AssessmentResultHistory` với `reason_code='REGRADE'`, liên kết `regrade_job_id`.
   - Cập nhật bộ đếm `changed_results` trên `RegradeJob`.
4. **Course Completion Integration**:
   - Khi bài thi bắt buộc hoàn thành (`is_required_for_completion=True`) thay đổi trạng thái đạt/không đạt (`passed`), tự động kích hoạt `recalculate_course_completion` để cập nhật tiến độ và trạng thái hoàn thành khóa học của học viên.
5. **Resumability, Batching & Idempotency**:
   - Hỗ trợ thực thi theo batch (`batch_size`), cho phép ngắt quãng và tiếp tục từ vị trí dừng.
   - Retry logic: Endpoint `POST /api/regrade-jobs/<job_id>/retry` cho phép reset trạng thái các `RegradeItem` bị `FAILED` (`attempt_count=0`, `last_error=None`) và chạy lại an toàn.
   - Chạy lại nhiều lần trên cùng một job/revision đảm bảo tính Idempotent: không sinh thêm bản ghi lịch sử trùng lặp.
6. **Zero-Trust Security & ADR-002**:
   - Chỉ giảng viên phụ trách khóa học hoặc Admin mới có quyền kích hoạt regrade, đọc chi tiết job, hoặc retry job.
   - Học viên chỉ xem được lịch sử điểm số của chính mình (`GET /api/attempts/<attempt_id>/grade-history`) khi thỏa mãn `score_release_policy`.
   - Che giấu 100% khóa chính nội bộ `BIGINT PK`; toàn bộ API chỉ giao tiếp qua UUIDv4/v5 (`job_id`, `item_id`, `attempt_id`, `question_correction_id`).

---

## 2. Source-of-Truth Documents
- `AGENTS.md` (Hợp đồng vận hành & Core Invariants)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/11_REGRADING_ALGORITHM.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/10_GRADING_AND_REGRADING.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/07_QUESTION_VERSIONING_AND_CORRECTION.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/state-machines/REGRADING_STATE_MACHINE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/07_ASSESSMENT_API.md` & `08_ATTEMPT_API.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/08_DATA_DICTIONARY_ATTEMPT_REGRADING.md`
- `docs/decisions/ADR-002-database-identifiers.md`

---

## 3. In Scope & Implemented Components

### Model Enhancements (`src/pwd301/models/attempt_regrade.py`)
- Bổ sung `@property def public_id(self) -> uuid.UUID:` cho `QuestionCorrection`, `RegradeJob`, và `RegradeItem` sử dụng UUIDv5 determinism theo ADR-002, đảm bảo tương thích hoàn toàn với các quy ước định danh công khai.

### Core Domain Services (`src/pwd301/services/regrade_worker.py`)
- `get_regrade_job_detail`: Kiểm tra phân quyền Zero-Trust (`require_course_manager`), serialize danh sách items mà không làm lộ BIGINT PK.
- `retry_regrade_job`: Kiểm tra phân quyền giảng viên, reset `attempt_count=0`, chuyển `FAILED` -> `PENDING`, và tiếp tục xử lý job.
- `_evaluate_attempt_item_regrade`:
  - Thực thi Algorithm 11 chính xác: áp dụng Full-Credit nếu `CONTENT_OR_CHOICES`, chấm lại theo revision mới nếu `ANSWER_ONLY`.
  - Hỗ trợ so khớp lựa chọn linh hoạt (theo UUID `choice_key`, position fallback, hoặc text content fallback) bảo đảm an toàn trước các snapshot phức tạp.
  - Tự động chuyển đổi `attempt.status` sang `GRADED` nếu không còn câu hỏi nào đang chờ chấm (`PENDING_GRADING`).
  - Ghi nhận `AttemptQuestionGradeHistory` và `AssessmentResultHistory`.
  - Tích hợp `recalculate_course_completion` khi `passed != old_passed` và bài thi là bắt buộc.
- `process_regrade_job`: Quản lý batching, xử lý ngoại lệ từng item (đánh dấu `FAILED` thay vì crash job), chuyển trạng thái `QUEUED` -> `RUNNING` -> `COMPLETED` / `PARTIAL`.

### REST API & Web Blueprint Routes
- `src/pwd301/blueprints/api_assessments/routes.py`:
  - `POST /api/assessments/<assessment_id>/regrade`: Endpoint JWT kích hoạt quy trình chấm lại đồng bộ/bất đồng bộ.
- `src/pwd301/blueprints/api_attempts/routes.py`:
  - `GET /api/regrade-jobs/<job_id>`: Endpoint đọc tiến độ và danh sách items của regrade job.
  - `POST /api/regrade-jobs/<job_id>/retry`: Endpoint retry các item bị lỗi.
  - `GET /api/attempts/<attempt_id>/grade-history`: Endpoint đọc lịch sử biến động điểm chi tiết theo ADR-002.
- `src/pwd301/blueprints/instructor/routes.py`:
  - `POST /instructor/assessments/<assessment_id>/regrade`: Giao diện/view giảng viên kích hoạt chấm lại.
  - `GET /instructor/regrade-jobs/<job_id>`: View giảng viên theo dõi tiến độ chấm lại.
  - `POST /instructor/regrade-jobs/<job_id>/retry`: View giảng viên retry các bản ghi lỗi.

---

## 4. Acceptance Criteria Verification

- [x] **Thuật toán Algorithm 11 (ANSWER_ONLY)**: Tính toán lại điểm số dựa trên đáp án đúng mới; sinh `AttemptQuestionGradeHistory` với `reason_code='AUTO_REGRADE'`.
- [x] **Thuật toán Algorithm 11 (CONTENT_OR_CHOICES)**: Áp dụng Full-Credit Safety Policy cho 100% thí sinh bị ảnh hưởng; sinh `reason_code='FULL_CREDIT'`.
- [x] **Quy tắc Skip Logic**: Bỏ qua các attempt bị thanh lọc chi tiết (`DETAIL_PURGED`) hoặc bị hủy (`CANCELLED`) với mã lý do chuẩn hóa.
- [x] **Tích hợp Course Completion**: Tự động tính lại tiến độ và cấp chứng chỉ/hoàn thành khóa học khi điểm regrade giúp thí sinh vượt qua bài kiểm tra bắt buộc.
- [x] **Tính Resumable, Batching & Idempotent**: Hỗ trợ xử lý ngắt quãng theo batch, retry item lỗi, và không sinh lịch sử trùng lặp khi chạy lại.
- [x] **Bảo mật Zero-Trust & IDOR**: Chặn 403 Forbidden đối với học viên và giảng viên không thuộc khóa học; kiểm soát `score_release_policy` trước khi cho phép xem lịch sử điểm.
- [x] **Tuân thủ ADR-002**: Không để lộ bất kỳ khóa chính nội bộ `BIGINT` nào trong payload REST hay Web.

---

## 5. Verification Results

| Gate | Command | Result |
|---|---|---|
| **1. Repo Contract** | `python scripts/repo_check.py` | **PASS** (71 tables canonical DDL, balanced code fences) |
| **2. Python Compile** | `python -m compileall -q src tests scripts` | **PASS** (Clean compilation) |
| **3. Ruff Lint** | `ruff check src tests scripts` | **PASS** (All checks passed!) |
| **4. Ruff Format** | `ruff format --check src tests scripts` | **PASS** (116 files already formatted) |
| **5. Type Check** | `mypy src` | **PASS** (Success: no issues in 58 source files) |
| **6. Task-017 Suites** | `pytest tests/unit/test_regrade_service.py tests/security/test_regrade_idor.py tests/api/test_regrade_api.py -v` | **PASS** (22/22 passed in 17.49s) |
| **7. Full Regression** | `pytest` | **PASS** (471/471 passed in 280.21s) |
| **8. Verify Script** | `./scripts/verify.ps1` | **PASS** (`PWD301 verification PASS`) |

---

## 6. Completion Report

### A. Scope and sources consulted
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/11_REGRADING_ALGORITHM.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/10_GRADING_AND_REGRADING.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/07_QUESTION_VERSIONING_AND_CORRECTION.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/state-machines/REGRADING_STATE_MACHINE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/07_ASSESSMENT_API.md` & `08_ATTEMPT_API.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/08_DATA_DICTIONARY_ATTEMPT_REGRADING.md`
- `docs/decisions/ADR-002-database-identifiers.md`
- `AGENTS.md`

### B. Reuse decisions
- Tái sử dụng `recalculate_course_completion` trong `completion_service.py` để cập nhật trạng thái hoàn thành khóa học khi kết quả regrade thay đổi.
- Tái sử dụng `require_course_manager` trong `authorization_service.py` để bảo vệ tài nguyên regrade job và trigger endpoint.
- Tái sử dụng `_serialize_regrade_job` và `_serialize_regrade_item` cho cả REST API và Web view để đảm bảo định dạng UUIDv5 đồng nhất theo ADR-002.

### C. Per-file changes
- `src/pwd301/models/attempt_regrade.py`: Bổ sung `@property def public_id` cho `QuestionCorrection`, `RegradeJob`, `RegradeItem`.
- `src/pwd301/services/regrade_worker.py`: Bổ sung Zero-Trust authorization, hoàn thiện choice matching fallback, retry counter reset, và cập nhật attempt transition.
- `src/pwd301/blueprints/instructor/routes.py`: Thêm route `POST /instructor/regrade-jobs/<job_id>/retry`.
- `tests/unit/test_regrade_service.py`: 7 unit tests kiểm tra Algorithm 11 (ANSWER_ONLY, CONTENT_OR_CHOICES), skip logic (DETAIL_PURGED, CANCELLED), course completion, idempotency, batching & retry.
- `tests/security/test_regrade_idor.py`: 11 security/IDOR tests kiểm tra phân quyền học viên, giảng viên ngoại lai, score release policy và ADR-002 zero PK leakage.
- `tests/api/test_regrade_api.py`: 4 API integration tests kiểm tra toàn bộ luồng REST API và Instructor Web view.
- `tasks/CURRENT.md`: Hoàn thiện báo cáo nghiệm thu TASK-017.
- `tasks/DONE.md`: Cập nhật mốc hoàn thành TASK-017.

### D. Deletion and simplification list
- Không có abstraction thừa thãi nào được đưa vào; tái sử dụng các model và service sẵn có; worker chạy đồng bộ/resumable không cần phụ thuộc bên ngoài.

### E. Ponytails / Deferred debt
- Không có nợ kỹ thuật tồn đọng.

### F. Verification actually run and results
- Đã chạy đầy đủ và vượt qua 100% các cổng kiểm thử: repo check, ruff check, ruff format check, mypy type check, bộ test TASK-017 (22/22 passed), và toàn bộ regression suite (471/471 passed).
