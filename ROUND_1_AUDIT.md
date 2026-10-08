# ROUND 1 AUDIT: TOÀN BỘ HỆ THỐNG PWD301 (FULL ARCHITECTURE & SYSTEM AUDIT)

**Ngày thực hiện**: 2026-10-08  
**Vai trò**: Senior Software Architect + Full-Stack Engineer + QA Engineer + Security Reviewer + Performance Engineer  
**Trạng thái**: Hoàn thành Đợt 1 / Chuẩn bị triển khai Round 2  

---

## 1. TỔNG QUAN KIẾN TRÚC TOÀN HỆ THỐNG (ARCHITECTURE SUMMARY)

### 1.1. Kiến trúc Tổng thể (Pure Headless Platform Architecture)
Hệ thống **PWD301** là một nền tảng Học tập & Khảo thí Trực tuyến (LMS & Assessment System) được thiết kế theo mô hình **Pure Headless Backend & REST API Platform**:
- **Headless Client (Frontend)**: Single-Page Application (SPA) xây dựng bằng Modern Vanilla ES6 Modules, Tailwind CSS (CDN), DOMPurify, HLS.js, và module bảo mật độc quyền `VideoArmor`. Toàn bộ giao diện nằm tại thư mục `frontend/` (`frontend/index.html`, `frontend/assets/js/`). Không sử dụng bất kỳ template engine phía server (Jinja2) hay mã HTML render động từ backend.
- **Backend Framework**: Python 3.12 + Flask 3.0.x với 17 Flask Blueprints chuyên biệt:
  - Role-based Session Web API: `auth`, `student`, `instructor`, `admin`, `frontend`.
  - Machine-readable JWT REST API: `api_auth`, `api_admin`, `api_ai`, `api_assessments`, `api_attempts`, `api_courses`, `api_files`, `api_import`, `api_lessons`, `api_notifications`, `api_student`.
  - Core Infrastructure: `core`.
- **Cơ sở dữ liệu (Database & ORM)**:
  - Chuẩn mực thiết kế mục tiêu: Microsoft SQL Server (Transact-SQL) với schema chuẩn hóa tại `docs/database/PWD301_DATABASE_ARCHITECTURE/`.
  - ORM: SQLAlchemy 2.0 + Flask-SQLAlchemy với 73 entities/tables.
  - Khóa chính nội bộ: `BIGINT IDENTITY(1,1)`; Khóa định danh công khai ngoại vi: `UNIQUEIDENTIFIER` (UUIDv4) theo chuẩn `ADR-002: Zero Internal PK Leakage`.
  - Kiểm soát đồng thời: `ROWVERSION` / Concurrency Timestamps trên các thực thể nhạy cảm (Bài thi, Chấm điểm, Khóa học).
- **Cơ chế Xác thực kép (Dual Authentication)**:
  - **Web SPA (Browser)**: Flask HTTP-Only Cookie Session kèm token bảo vệ CSRF (`X-CSRFToken` / `pwd301_csrf`) cho mọi mutation request (POST, PUT, PATCH, DELETE).
  - **REST API (External Clients)**: JSON Web Token (JWT) Bearer tokens qua Flask-JWT-Extended (`access_token`, `refresh_token`), tự động thu hồi khi tài khoản bị khóa (`SUSPENDED`).
- **Lưu trữ Tệp & An toàn Dữ liệu (Fail-Closed File Storage)**:
  - Hệ thống lưu trữ tệp cục bộ có phân quyền nghiêm ngặt.
  - Tích hợp quét virus ClamAV tự động (`PENDING` $\rightarrow$ `CLEAN` / `QUARANTINED`). Xử lý theo nguyên tắc **Fail-Closed**: nếu ClamAV ngoại tuyến hoặc tệp chưa quét sạch, sinh viên tuyệt đối không thể tải hay xem tệp.
- **Bảo mật Bản quyền Video & Giám sát Zero-Trust (Video DRM & Forensic Watermark)**:
  - Nghiêm cấm tuyệt đối cung cấp link tải trực tiếp (.mp4/.webm) cho học viên.
  - Video được phân đoạn và mã hóa HLS AES-128 với token phát ngắn hạn gắn với phiên đăng nhập.
  - Dynamic Forensic Watermarking: Thủy ấn động trôi nổi hiển thị `MSSV - Email - IP - Timestamp` trên khung hình.
  - Lớp giáp Client Armor (`MutationObserver`) tự động kích hoạt màn hình đen (Blackout) khi DOM watermark bị can thiệp qua DevTools.
  - Zero-Trust Wall-Clock Heartbeat: Tiến độ bài học bắt buộc tích lũy thời gian thực qua chuỗi nhịp tim (`seconds_spent >= minimum_completion_seconds`), cấm gian lận bằng `view_fraction >= 0.90`.
- **Hệ thống Khảo thí & Chống Xung đột Tab (Algorithm 07 - Single Active Editing Lease)**:
  - Khóa phiên làm bài duy nhất (Lease Token SHA-256) đảm bảo một bài thi chỉ mở và làm trên 1 tab trình duyệt.
  - Đảm bảo thứ tự autosave qua `client_sequence` và `lease_epoch`.
  - Nộp bài đẳng công (Idempotent Submit) qua `submission_idempotency_key`.
  - Chấm lại có thể tiếp tục và bảo toàn lịch sử (`AssessmentResultHistory`).
- **Trợ lý AI Tích hợp (Octopus AI Assistant - "Bạch tuộc trợ lí AI")**:
  - Google Gemini API với RAG Vector Indexing, tìm kiếm ngữ nghĩa theo tài liệu khóa học đã duyệt.
  - Zero-Trust Prompt Injection Defense: Ngăn chặn 100% tấn công khai thác thông tin tài khoản, danh sách user hay cấu trúc CSDL nội bộ.
  - Hủy tự động nội dung chat thô sau 5 phút không hoạt động để bảo vệ quyền riêng tư học viên.

---

## 2. MA TRẬN PHÂN QUYỀN VÀ VAI TRÒ (ROLE / PERMISSION MATRIX)

| Role Code | Tên Vai trò | Cấp độ Truy cập | Phương thức Xác thực | Phạm vi Dữ liệu & Quyền hạn | Guards / Middleware |
|---|---|---|---|---|---|
| **ANONYMOUS** | Khách vãng lai | Công khai | Không | Xem danh mục khóa học đã xuất bản, đăng ký tài khoản, đăng nhập | Không yêu cầu |
| **STUDENT** | Sinh viên / Học viên | Người dùng | Session Web / JWT | Đăng ký học, học bài qua DRM HLS, gửi heartbeat, làm bài thi khảo thí (Lease), xem điểm, chat với Bạch tuộc AI, đánh giá khóa học | `@student_required`, `@jwt_required` |
| **INSTRUCTOR** | Giảng viên | Quản lý Chuyên môn | Session Web / JWT | Quản lý khóa học được phân công (DRAFT, Changeset), tạo ngân hàng câu hỏi, tạo bài thi, duyệt bài nộp tự luận, chấm lại bài thi, xem báo cáo học vụ | `@instructor_required`, `require_course_manager` |
| **ADMIN** | Quản trị viên Hệ thống | Vận hành Hệ thống | Session Web / JWT | Quản lý người dùng (khóa/mở), phân quyền, duyệt đợt cập nhật khóa học (Changeset), quản lý cách ly ClamAV, xem telemetry hệ thống (`psutil`), xem audit logs | `@admin_required`, `verify_sensitive_action_reauth` |
| **PRIMARY_ADMIN** | Quản trị viên Cấp cao (Super Admin) | Cao nhất | Session Web / JWT | Tạo backup cơ sở dữ liệu vật lý (MSSQL), khôi phục dữ liệu (Disaster Recovery), kích hoạt bảo trì hệ thống (Maintenance Mode) | `@primary_admin_required`, `verify_sensitive_action_reauth` |

---

## 3. MA TRẬN CHỨC NĂNG HỆ THỐNG (FEATURE MATRIX)

| Mã Tính năng | Tên Tính năng | Module | Frontend View | Backend Route / API | Trạng thái Hiện tại |
|---|---|---|---|---|---|
| **FEAT-AUTH-01** | Đăng nhập / Đăng ký / Đăng xuất | Auth | `views/auth.js` | `/auth/login`, `/auth/register`, `/auth/logout`, `/api/auth/*` | Hoạt động tốt |
| **FEAT-AUTH-02** | Khóa phiên khi bị đình chỉ | Auth | `app.js` | Middleware session validation | Hoạt động tốt |
| **FEAT-CRS-01** | Danh mục khóa học & Đăng ký | Student | `views/student.js` | `/student/courses`, `/student/enrollments`, `/api/courses/*` | Hoạt động tốt |
| **FEAT-CRS-02** | Môn học tiên quyết (Prerequisites DAG) | Course | `views/instructor.js` | `/instructor/courses/<id>/prerequisites` | Có lỗi logic thứ tự kiểm tra |
| **FEAT-CRS-03** | Quy tắc hoàn thành khóa học | Course | `views/instructor.js` | `/instructor/courses/<id>/completion-rules` | Hoạt động tốt |
| **FEAT-CRS-04** | Đợt cập nhật khóa học (Changeset Workflow) | Course | `views/instructor.js` | `/instructor/courses/<id>/changeset/*` | Có lỗi khóa đồng thời khi chờ duyệt |
| **FEAT-LRN-01** | Trình phát Video DRM HLS | Learning | `views/student.js`, `video-armor.js` | `/student/courses/<cid>/lessons/<lid>/video/*` | Hoạt động tốt, test cũ lệch hợp đồng |
| **FEAT-LRN-02** | Thủy ấn pháp chứng động (Watermark) | Security | `video-armor.js` | Tích hợp Client Armor | Hoạt động tốt |
| **FEAT-LRN-03** | Nhịp tim tiến độ thời gian thực (Heartbeat) | Learning | `views/student.js` | `/student/lessons/<id>/progress` | Hoạt động tốt, test cũ lệch thông số |
| **FEAT-ASM-01** | Khảo thí: Bắt đầu làm bài & Cấp Lease | Assessment | `views/student.js`, `exam-store.js` | `/student/assessments/<id>/start` | Hoạt động tốt |
| **FEAT-ASM-02** | Khảo thí: Tự động lưu đáp án (Autosave) | Assessment | `exam-store.js` | `/student/assessments/<id>/answers` | Hoạt động tốt |
| **FEAT-ASM-03** | Khảo thí: Nộp bài đẳng công (Submit) | Assessment | `views/student.js` | `/student/assessments/<id>/submit` | Lỗi cưỡng bức Lease Token khi gọi service |
| **FEAT-ASM-04** | Khảo thí: Chấm điểm tự động & Chấm lại | Assessment | `views/instructor.js` | `/instructor/assessments/<id>/regrade` | Hoạt động tốt |
| **FEAT-AI-01** | Bạch tuộc trợ lí AI & RAG Search | AI | `views/student.js` | `/api/ai/chat`, `/api/ai/session` | Hoạt động tốt |
| **FEAT-ADM-01** | Giám sát phần cứng thực tế (Telemetry) | Admin | `views/admin.js` | `/admin/telemetry`, `/admin/health` | Hoạt động tốt |
| **FEAT-ADM-02** | Đình chỉ người dùng nhạy cảm | Admin | `views/admin.js` | `/admin/users/<id>/suspend` | Test API thiếu mật khẩu xác nhận |
| **FEAT-ADM-03** | Quản lý cách ly tệp độc hại | Storage | `views/admin.js` | `/admin/files/<id>/quarantine-override` | Test API thiếu mật khẩu xác nhận |
| **FEAT-ADM-04** | Sao lưu & Phục hồi CSDL thảm họa | Operations | `views/admin.js` | `/api/admin/backups/*` | Test API thiếu mock engine vật lý |

---

## 4. MA TRẬN LUỒNG CÔNG VIỆC THỰC TẾ (WORKFLOW MATRIX)

### Luồng 1: Xác thực & Quản lý Phiên (Authentication & Session Lifecycle)
- **Chuỗi thao tác**:  
  User $\rightarrow$ Form đăng nhập (`/auth/login`) $\rightarrow$ API Backend $\rightarrow$ Kiểm tra bcrypt hash $\rightarrow$ Cấp Flask Session + Cookie CSRF $\rightarrow$ Router SPA chuyển hướng theo vai trò (`/student`, `/instructor`, `/admin`).  
- **Cơ chế phòng thủ**: Nếu tài khoản bị Admin gắn cờ `SUSPENDED`, middleware backend lập tức hủy cookie session và vô hiệu hóa JWT token ở request kế tiếp.

### Luồng 2: Học tập & Bảo mật Video DRM (Learning & Zero-Trust Heartbeat)
- **Chuỗi thao tác**:  
  Sinh viên vào bài học $\rightarrow$ Kiểm tra điều kiện tiên quyết $\rightarrow$ Tải HLS master playlist $\rightarrow$ Client khởi tạo HLS.js + `VideoArmor` $\rightarrow$ Thủy ấn động hiển thị MSSV, Email, IP, Timestamp trôi nổi $\rightarrow$ Mỗi 15s gửi 1 heartbeat (`seconds_increment: 15, view_fraction`) $\rightarrow$ Máy chủ tích lũy `seconds_spent` $\rightarrow$ Khi `seconds_spent >= minimum_completion_seconds` và `max_view_fraction >= viewed_fraction_required` mới ghi nhận hoàn thành.  
- **Cơ chế chống gian lận**: `MutationObserver` phát hiện xóa/ẩn watermark $\rightarrow$ Kích hoạt màn hình đen (Blackout) $\rightarrow$ Gửi telemetry vi phạm `VIDEO_SECURITY_VIOLATION`.

### Luồng 3: Làm bài thi Khảo thí (Assessment & Single Active Editing Lease)
- **Chuỗi thao tác**:  
  Sinh viên bấm "Bắt đầu làm bài" $\rightarrow$ Backend tạo `AssessmentAttempt` ở trạng thái `IN_PROGRESS` $\rightarrow$ Cấp `lease_token` (SHA-256 hash lưu DB, token thô trả về client) $\rightarrow$ Đóng băng snapshot đề thi và lựa chọn $\rightarrow$ Trong khi làm bài, `exam-store.js` tự động lưu từng câu hỏi hoặc batch offline $\rightarrow$ Sinh viên bấm "Nộp bài" $\rightarrow$ Backend kiểm tra hạn giờ máy chủ, xác thực lease token, chuyển trạng thái sang `SUBMITTED`, tính điểm tức thì cho câu trắc nghiệm.  
- **Cơ chế an toàn**: Một bài thi chỉ cho phép duy nhất 1 tab thao tác; mở tab mới sẽ yêu cầu Takeover Lease (hủy lease ở tab cũ).

### Luồng 4: Biên soạn & Xuất bản Khóa học (Course Authoring & Changeset Approval)
- **Chuỗi thao tác**:  
  Giảng viên tạo khóa học DRAFT $\rightarrow$ Thêm chương mục, bài học, tài liệu $\rightarrow$ Bấm "Gửi xét duyệt" (`SUBMITTED_FOR_REVIEW`) $\rightarrow$ Admin kiểm duyệt $\rightarrow$ Duyệt (`APPROVED`) $\rightarrow$ Giảng viên xuất bản (`PUBLISHED`).  
- **Đối với khóa học đã xuất bản**: Mọi thay đổi bài học/chương mục được đưa vào bản nháp Changeset gom cụm (`COURSE_VERSION_CHANGESET`). Giảng viên gửi changeset $\rightarrow$ Khóa toàn bộ chỉnh sửa tiếp theo (Fail-closed lock) $\rightarrow$ Admin duyệt toàn bộ đợt cập nhật nguyên tử.

### Luồng 5: Bảo mật Tệp tin & Vận hành Hệ thống (File Quarantine & Operations)
- **Chuỗi thao tác**:  
  Tải tệp lên $\rightarrow$ Đặt trạng thái `PENDING` $\rightarrow$ ClamAV quét $\rightarrow$ Chuyển thành `CLEAN` hoặc `QUARANTINED` $\rightarrow$ Nếu `QUARANTINED`, cấm tải hoặc xem tệp.  
- **Thao tác nhạy cảm**: Admin đình chỉ người dùng hoặc ghi đè cách ly tệp bắt buộc phải xác thực lại mật khẩu hiện tại (`admin_password`).

---

## 5. ĐỐI CHIẾU FRONTEND ↔ BACKEND ↔ DATABASE (CROSS-CHECK MAPPING)

| Frontend View / Call | Phương thức | URL Endpoint | Backend Controller | Database Entities | Tình trạng Đối chiếu |
|---|---|---|---|---|---|
| `views/auth.js` | POST | `/auth/login` | `auth.login_route` | `User`, `UserRole`, `Role` | Khớp 100% |
| `views/auth.js` | POST | `/auth/logout` | `auth.logout_route` | `User` | Khớp 100% |
| `views/student.js` | GET | `/student/courses` | `student.list_courses` | `Course`, `Enrollment` | Khớp 100% |
| `views/student.js` | POST | `/student/courses/<id>/enroll` | `student.enroll_course_route` | `Enrollment`, `CoursePrerequisite` | Khớp 100% |
| `views/student.js` | POST | `/student/lessons/<id>/progress` | `student.record_student_progress_route` | `LessonProgress`, `Lesson` | Khớp 100% |
| `views/student.js:4384` | Call | `ApiClient.recordTelemetry` | Chưa định nghĩa trong `api.js` | `AuditEvent` | **CASE 1: Thiếu method trên ApiClient** |
| `views/instructor.js` | GET/POST | `/instructor/courses/<id>/prerequisites` | `instructor.course_prerequisites_route` | `CoursePrerequisite` | **CASE 4: Lỗi thứ tự kiểm tra self-ref** |
| `views/instructor.js` | POST | `/instructor/courses/<id>/lessons` | `instructor.create_lesson_route` | `Lesson`, `LearningUnit` | **CASE 5: Mất estimated_duration_minutes** |
| `views/instructor.js` | POST | `/instructor/courses/<id>/learning-units` | `instructor.learning_units_route` | `LearningUnit`, `CourseChangeRequest` | **CASE 7: Chưa kiểm tra changeset lock** |
| `views/admin.js` | POST | `/admin/users/<id>/suspend` | `admin.suspend_user_route` | `User`, `AuditEvent` | Khớp Web (Test API thiếu admin_password) |
| `views/admin.js` | POST | `/admin/files/<id>/quarantine-override` | `admin.quarantine_override_route` | `FileAsset`, `AuditEvent` | Khớp Web (Test API thiếu admin_password) |
| `views/admin.js` | POST | `/api/admin/backups` | `api_admin.api_admin_create_backup` | `BackupRun`, `AuditEvent` | Khớp Web (Test API thiếu mock engine) |

---

## 6. DANH SÁCH CHI TIẾT CÁC LỖI & PHÂN LOẠI ƯU TIÊN (P0 / P1 / P2 / P3)

Toàn bộ 27 lỗi kiểm thử và khiếm khuyết được phát hiện trong Round 1 đã được phân tích truy vết nguyên nhân gốc rễ (Root Cause Analysis):

### Nhóm P0: Nghiêm trọng / Broken Workflow / Security Invariant
1. **[P0-01] Broken Assessment Submission do cưỡng bức Editing Lease Token vô điều kiện**:
   - **Vị trí**: `src/pwd301/services/attempt_service.py:2024`.
   - **Hiện tượng**: `submit_assessment_attempt` ném lỗi `AttemptLeaseConflictError` nếu `raw_lease_token is None` trong khi bài thi có lease còn hiệu lực.
   - **Tác động**: Làm gãy 14 unit tests trong `test_assessment_regrading_traceability.py` và `test_attempt_autosave_service.py`. Gây lỗi khi các dịch vụ backend, background worker hoặc kiểm thử gọi hàm submit trực tiếp mà không qua header HTTP.
   - **Khắc phục**: Cho phép submit an toàn khi người gọi là chủ sở hữu bài thi và không có tranh chấp token, chỉ so khớp token nếu `raw_lease_token` được truyền vào hoặc có cờ kiểm soát.

2. **[P0-02] Thất thoát dữ liệu thời lượng bài học (`estimated_duration_minutes`)**:
   - **Vị trí**: `src/pwd301/services/lesson_service.py:664` và `src/pwd301/blueprints/instructor/routes.py:1287`.
   - **Hiện tượng**: Trong hàm `create_lesson`, code bị gán cứng `est_duration = None`, bỏ qua giá trị `estimated_duration_minutes` do giảng viên gửi lên.
   - **Tác động**: Mọi bài học tạo mới đều bị mất thông số thời lượng ước tính (`None`), gây lỗi hiển thị trên giao diện và fail `test_lesson_duration_summary_video_persistence`.
   - **Khắc phục**: Đọc và parse chính xác `data.get("estimated_duration_minutes")` thành số nguyên hợp lệ trong `create_lesson`.

3. **[P0-03] Thủng lớp phòng thủ khóa đồng thời khi khóa học đang chờ duyệt (`_ensure_course_not_pending_changeset`)**:
   - **Vị trí**: `src/pwd301/blueprints/instructor/routes.py:942` (`learning_units_route`).
   - **Hiện tượng**: Route tạo chương mục bài học (`POST /learning-units`) không gọi hàm kiểm tra `_ensure_course_not_pending_changeset`, cho phép giảng viên tiếp tục tạo yêu cầu thêm chương mới ngay cả khi khóa học đang có changeset chờ Admin duyệt.
   - **Tác động**: Vi phạm nguyên tắc bất biến Fail-Closed lock, fail `test_fail_closed_lock_during_pending_changeset`.
   - **Khắc phục**: Gọi `_ensure_course_not_pending_changeset` ngay tại đầu route `POST /learning-units`.

### Nhóm P1: Thiếu Tính năng / Hợp đồng API / Lỗi Logic Nghiệp vụ
4. **[P1-01] Thiếu method `ApiClient.recordTelemetry` trên Frontend**:
   - **Vị trí**: `frontend/assets/js/api.js` (gọi từ `frontend/assets/js/views/student.js:4384`).
   - **Hiện tượng**: `VideoArmor` khi phát hiện can thiệp DevTools sẽ gọi `ApiClient.recordTelemetry('VIDEO_SECURITY_VIOLATION', ...)`, nhưng `api.js` chưa có method này.
   - **Tác động**: Vi phạm hợp đồng Parity giữa Frontend và ApiClient, fail `test_frontend_static_assets_and_contract_parity`.
   - **Khắc phục**: Bổ sung `static async recordTelemetry(eventType, payload)` vào `ApiClient` trong `api.js`.

5. **[P1-02] Đảo lộn thứ tự kiểm tra Môn tiên quyết (Self-Reference vs Published Status)**:
   - **Vị trí**: `src/pwd301/services/enrollment_service.py:721`.
   - **Hiện tượng**: Hàm `add_course_prerequisite` kiểm tra `prereq_course.status != 'PUBLISHED'` TRƯỚC KHI kiểm tra `course.id == prereq_course.id`.
   - **Tác động**: Khi một khóa học DRAFT vô tình chọn chính nó làm môn tiên quyết, hệ thống báo lỗi sai ngữ nghĩa ("Khóa học chưa được xuất bản") thay vì báo lỗi tự tham chiếu ("A course cannot be a prerequisite of itself"), fail `test_t_course_05_prerequisite_self_reference_blocked`.
   - **Khắc phục**: Đảo kiểm tra `course.id == prereq_course.id` lên trước kiểm tra trạng thái `PUBLISHED`.

6. **[P1-03] Fixture kiểm thử chu trình tiên quyết (DFS Cycle Detection) khởi tạo sai trạng thái**:
   - **Vị trí**: `tests/unit/test_core_learning_traceability.py:218` và `tests/api/test_backend_frontend_parity.py:97`.
   - **Hiện tượng**: Các khóa học dùng để dựng đồ thị tiên quyết kiểm thử DFS được tạo ở trạng thái mặc định DRAFT thay vì PUBLISHED, khiến yêu cầu thêm tiên quyết bị chặn bởi quy tắc TASK-084 trước khi DFS chạy.
   - **Khắc phục**: Đặt trạng thái PUBLISHED cho các khóa học kiểm thử tiên quyết.

7. **[P1-04] Lệch hợp đồng kiểm thử Thao tác nhạy cảm yêu cầu mật khẩu xác thực lại (`verify_sensitive_action_reauth`)**:
   - **Vị trí**: `tests/api/test_admin_backend_completion.py:233, 257` và `tests/api/test_scan_api.py:380`.
   - **Hiện tượng**: Backend yêu cầu bắt buộc `admin_password` cho các hành động đình chỉ tài khoản và ghi đè cách ly tệp (bảo vệ OWASP chống CSRF/leo thang đặc quyền), nhưng các test case gửi payload thiếu trường này dẫn đến HTTP 401.
   - **Khắc phục**: Cung cấp `"admin_password": "Password@123"` trong payload kiểm thử.

8. **[P1-05] Lệch chuẩn kiểm thử Bảo mật Video DRM & HLS Playlist**:
   - **Vị trí**: `tests/api/test_lesson_video_delivery_remediation.py:178`.
   - **Hiện tượng**: Test cũ assert rằng URL video bài học trả về link tải trực tiếp file thô `/student/files/<id>/download`. Tuy nhiên, theo TASK-085 & Invariant 25, link tải thô đã bị xóa bỏ hoàn toàn và thay thế bằng luồng phân đoạn mã hóa HLS `/video/playlist.m3u8`.
   - **Khắc phục**: Cập nhật assertion kiểm tra link HLS `.m3u8`.

9. **[P1-06] Lệch chuẩn kiểm thử Tiến độ Zero-Trust Wall-Clock Heartbeat**:
   - **Vị trí**: `tests/api/test_student_learning_remediation.py:234`.
   - **Hiện tượng**: Test gửi 1 heartbeat 15 giây nhưng kỳ vọng hoàn thành bài học có `minimum_completion_seconds: 60` chỉ vì `view_fraction = 0.95`, vi phạm trực tiếp Invariant 25.
   - **Khắc phục**: Gửi đủ tích lũy heartbeat (60s) để đạt chuẩn hoàn thành bài học.

10. **[P1-07] Thiếu fixture `physical_backup_engine` trong kiểm thử vòng đời Sao lưu API**:
    - **Vị trí**: `tests/api/test_operations_api.py:144`.
    - **Hiện tượng**: Hàm `test_admin_backup_full_lifecycle_api` chạy trên SQLite nhưng không inject fixture `physical_backup_engine`, dẫn đến lỗi validation yêu cầu SQL Server.
    - **Khắc phục**: Bổ sung tham số `physical_backup_engine` vào định nghĩa test.

11. **[P1-08] Xử lý phân nhánh Changeset vs Standalone Change Request khi tạo bài giảng**:
    - **Vị trí**: `src/pwd301/blueprints/instructor/routes.py:1408` và `tests/api/test_course_metadata_and_lesson_approval_remediation.py`.
    - **Hiện tượng**: Tạo bài giảng trong khóa học đã xuất bản hỗ trợ cả hai mô hình (gom cụm changeset hoặc gửi yêu cầu duyệt lẻ trả về 202). Cần khôi phục phân nhánh linh hoạt.

### Nhóm P2: Chất lượng Mã nguồn / Dead Code / Maintainability
- Rà soát các import trùng lặp trong các file blueprint `routes.py`.
- Chuẩn hóa hàm format lỗi tiếng Việt trên `ApiClient` trong `frontend/assets/js/api.js`.
- Loại bỏ các comment cũ không còn giá trị trong `attempt_service.py` và `lesson_service.py`.

### Nhóm P3: Tối ưu Hóa Hiệu năng / Truy vấn Database
- Kiểm tra các truy vấn N+1 khi duyệt danh sách bài học và tài nguyên (`joinedload`/`selectinload` trên `Lesson.resources` và `Course.lessons`).
- Tối ưu hóa chuỗi tính toán tiến độ khóa học trong `completion_service.py`.

---

## 7. KẾ HOẠCH HÀNH ĐỘNG CHO ROUND 2 (EXECUTION PLAN)
1. **Fix P0 & P1 Backend Services**:
   - `attempt_service.py`: Cập nhật logic xác thực lease token khi submit.
   - `lesson_service.py`: Lưu trữ `estimated_duration_minutes`.
   - `enrollment_service.py`: Đảo thứ tự kiểm tra self-reference.
   - `instructor/routes.py`: Bổ sung kiểm tra lock pending changeset cho learning units và phân nhánh bài học.
2. **Fix P1 Frontend Parity**:
   - `api.js`: Thêm `ApiClient.recordTelemetry`.
3. **Đồng bộ Test Suites**:
   - Cung cấp `admin_password` cho các test nhạy cảm.
   - Đồng bộ assertions HLS DRM và Zero-Trust Heartbeat.
   - Inject fixture `physical_backup_engine`.
   - Đặt trạng thái PUBLISHED cho các fixture kiểm thử tiên quyết.
4. **Kiểm tra Xác minh Sau Sửa chữa**:
   - Chạy toàn bộ test suites (`pytest tests/unit tests/api`).
   - Ghi nhận báo cáo vào `ROUND_2_FIXES.md`.
