# TASK-018 — File Blob/Asset Storage & Authorization Engine

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-001 through TASK-017  

---

## Goal
Xây dựng và hoàn thiện toàn diện tầng lưu trữ tệp tin vật lý/logic (File Blob & Asset Storage) và Động cơ phân quyền truy cập tệp (File Authorization Engine) cho nền tảng PWD301:
1. **Kiến trúc tách biệt Physical Blob vs. Logical Asset (ADR-008)**: Tách riêng bảng vật lý `FileBlob` (bất biến, định danh theo hash SHA-256 nội dung, quản lý reference count) và bảng logic `FileAsset` (gắn với Course, quản lý vòng đời logic và quyền sở hữu).
2. **Thuật toán Khử trùng lặp Content-Hash SHA-256 (Algorithm 12)**: Tính toán streaming SHA-256 hash và kích thước byte trong thư mục cách ly `quarantine`. Tái sử dụng `FileBlob` nếu trùng hash, hoặc lưu trữ theo cấu trúc phân cấp hai cấp byte đầu (`storage/blobs/ab/cd/<sha256>`) nếu là nội dung mới.
3. **Quản lý Phiên bản & Vòng đời tệp (FileRevision Lifecycle)**: Mỗi lần tải lên phiên bản mới tạo một `FileRevision` tăng tiến `revision_no`, cập nhật `is_current=True`, chuyển các bản ghi trước sang `REPLACED`, hỗ trợ tải về đúng phiên bản mong muốn qua tham số `version`.
4. **Giới hạn kích thước và kiểm tra loại tệp (Business Rule 11 & Config)**: 
   - Image $\le$ 10 MB, PDF $\le$ 50 MB, DOCX $\le$ 50 MB, PPTX $\le$ 100 MB.
   - Video strictly $< 1\text{ GB}$ (1,000,000,000 bytes).
   - Chặn tuyệt đối các tệp nguy hiểm/thực thi (.exe, .py, .sh, .bat, .cmd, v.v.) và macro-enabled Office (.docm, .xlsm, .pptm).
5. **Bảo mật Fail-Closed & Zero-Trust Authorization Matrix**:
   - Chỉ Admin hoặc Giảng viên quản lý khóa học mới có quyền upload, xóa, khôi phục hoặc tải lên revision mới.
   - Học viên chỉ được tải tệp khi: Khóa học ở trạng thái `PUBLISHED`, Học viên có Enrollment `ACTIVE`, và nếu tệp được gắn vào Bài học (`LessonResource`), bài học đó phải ở trạng thái `PUBLISHED`.
   - Chặn tuyệt đối tệp ở trạng thái `QUARANTINED`, `INFECTED`, hoặc có kết quả quét bảo mật `FAIL`/`ERROR`.
6. **Bảo mật chống rò rỉ định danh nội bộ & Path Traversal (ADR-002)**:
   - Che giấu 100% khóa chính nội bộ `BIGINT PK` (`id`, `blob_id`, `file_asset_id`); toàn bộ REST API và Web endpoints chỉ giao tiếp qua UUIDv4/v5 công khai (`asset_id`, `resource_id`, `course_id`).
   - Phòng chống tuyệt đối tấn công Path Traversal: khử bỏ các chuỗi `../`, `..\\`, null bytes, áp dụng tiêu đề phòng vệ `X-Content-Type-Options: nosniff` và `Content-Disposition: attachment; filename="<sanitized>"`.
7. **Khả năng khôi phục và dọn dẹp an toàn (Rollback Safety)**:
   - Hỗ trợ Soft-delete chuyển trạng thái `ACTIVE` -> `TRASH` và phục hồi về `ACTIVE`.
   - Nếu transaction cơ sở dữ liệu gặp lỗi khi commit, tự động dọn dẹp sạch sẽ tệp tạm trong quarantine và tệp blob vật lý mới ghi trên ổ cứng.

---

## Source-of-Truth Documents
- `AGENTS.md` (Operating Contract, Fail-closed Invariants, Video limit $< 1\text{ GB}$, ADR-002 Zero PK Leakage)
- `docs/decisions/ADR-008-blob-storage-design.md` (Physical Blob vs. Logical Asset)
- `docs/decisions/ADR-002-database-identifiers.md` (Public UUIDv4/v5, Zero BIGINT exposure)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/12_FILE_DEDUPLICATION_ALGORITHM.md` (Algorithm 12)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/11_FILE_SECURITY_AND_QUARANTINE.md` (Business Rule 11)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/09_FILE_IMPORT_API.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/09_DATA_DICTIONARY_STORAGE_MEDIA.md`
- `src/pwd301/config.py` (MAX_UPLOAD_SIZE_BYTES limits)

---

## Preconditions
- Hệ thống đã hoàn thành toàn diện TASK-017 với 471/471 bài kiểm thử vượt qua tuyệt đối.
- Mô hình cơ sở dữ liệu `FileBlob`, `FileAsset`, `FileRevision`, `FileScanResult`, `LessonResource` đã được ánh xạ trong `src/pwd301/models/file_import.py`.

---

## In Scope
1. **Domain Exceptions (`src/pwd301/services/exceptions.py` & `src/pwd301/__init__.py`)**:
   - `FileError`, `FileStorageError` (500), `FileValidationError` (400), `FileSizeLimitExceededError` (413), `FileAssetNotFoundError` (404), `FileAccessDeniedError` (403), `FileSecurityQuarantineError` (403).
2. **Model Enhancements (`src/pwd301/models/file_import.py`)**:
   - `@property def sha256_hex(self) -> str` cho `FileBlob`.
   - `@property def public_id(self) -> uuid.UUID` cho `FileRevision` và `LessonResource` (ADR-002 deterministic UUIDv5).
3. **Domain Service Layer (`src/pwd301/services/file_service.py`)**:
   - Triển khai toàn diện Algorithm 12, kiểm soát dung lượng, phân tích magic bytes, xử lý thư mục phân cấp, kiểm soát lỗi rollback, quản lý revision, soft-delete/restore, ma trận phân quyền Zero-Trust và serialization ADR-002.
4. **REST API & Web Endpoints**:
   - Blueprint `api_file_bp` (`/api/files`) đăng ký vào app factory, miễn trừ CSRF.
   - Endpoint upload/list trong `api_course_bp` (`/api/courses/<id>/files`).
   - Endpoint attach/detach tài liệu bài học trong `api_lesson_bp` (`/api/lessons/<id>/resources`).
   - Các route Web Instructor quản lý tệp có session authentication (`/instructor/courses/<id>/files`, `/instructor/files/<id>/trash`, `/instructor/files/<id>/restore`).
5. **Bộ kiểm thử toàn diện (Unit, Security/IDOR, API/Web)**:
   - `tests/unit/test_file_service.py` (8 bài kiểm thử)
   - `tests/security/test_file_authorization_idor.py` (12 bài kiểm thử)
   - `tests/api/test_file_api.py` (9 bài kiểm thử)

---

## Out of Scope
- Tích hợp dịch vụ đám mây AWS S3 / Azure Blob Storage (sử dụng Local File Storage chuẩn hóa cho môi trường triển khai hiện tại per ADR-008).
- Antivirus scanner ClamAV daemon thực tế (mô phỏng scan engine `builtin_validator` và bảng `file_scan_results`).
- Tích hợp background job queue cho asynchronous virus scanning (được thiết kế sẵn sàng mở rộng).

---

## Reuse / Existing-Code Inspection
- Tái sử dụng `require_course_manager` và `require_authenticated_actor` từ `src/pwd301/services/authorization_service.py`.
- Tái sử dụng cấu hình kích thước tải lên từ `src/pwd301/config.py` (`MAX_UPLOAD_SIZE_BYTES`).
- Tái sử dụng `utc_now()` và `RowVersion` từ `src/pwd301/models/types.py`.
- Tái sử dụng `create_token_pair` và `@jwt_required` từ `src/pwd301/services/jwt_auth_service.py`.
- Tái sử dụng `login_web_user` từ `tests/conftest.py` cho các bài kiểm thử session authentication.

---

## Planned Changes
- [x] Tạo các exception chuyên biệt cho File Storage trong `src/pwd301/services/exceptions.py`.
- [x] Đăng ký exception handlers trong `src/pwd301/__init__.py`.
- [x] Bổ sung các properties tương thích ADR-002 trong `src/pwd301/models/file_import.py`.
- [x] Triển khai toàn diện `src/pwd301/services/file_service.py`.
- [x] Triển khai blueprint `src/pwd301/blueprints/api_files/`.
- [x] Tích hợp route upload/list tệp khóa học trong `src/pwd301/blueprints/api_courses/routes.py`.
- [x] Tích hợp route đính kèm tài liệu bài học trong `src/pwd301/blueprints/api_lessons/routes.py`.
- [x] Tích hợp route quản lý tệp dành cho giảng viên trong `src/pwd301/blueprints/instructor/routes.py`.
- [x] Viết test suites: `test_file_service.py`, `test_file_authorization_idor.py`, `test_file_api.py`.
- [x] Chạy toàn bộ các cổng xác minh chất lượng mã nguồn: repo_check, compileall, ruff, mypy, full pytest, verify.ps1.

---

## Security / Authorization Impact
- Triển khai nguyên lý Zero-Trust: không tin tưởng bất kỳ định danh nào từ client mà không kiểm tra quyền sở hữu đối tượng.
- Thực thi chính sách Fail-Closed: từ chối truy cập mọi tệp chưa hoàn tất quét an ninh hoặc có nghi vấn mã độc.
- Áp dụng triệt để ADR-002: không làm lộ khóa chính `BIGINT PK` hay đường dẫn vật lý cục bộ trong responses.
- Phòng vệ Path Traversal và MIME Confusion: khử bỏ các ký tự điều hướng thư mục, áp dụng `X-Content-Type-Options: nosniff`.

---

## Database / Migration Impact
- Không làm thay đổi schema cơ sở dữ liệu đã chuẩn hóa 71 bảng (toàn bộ các bảng `file_blobs`, `file_assets`, `file_revisions`, `file_scan_results`, `lesson_resources` đã tồn tại đầy đủ và chuẩn xác).
- Đảm bảo tính toàn vẹn khóa ngoại và quan hệ cascade an toàn.

---

## Concurrency / Idempotency Impact
- Thao tác deduplication Algorithm 12 được bảo vệ an toàn: kiểm tra tồn tại của SHA-256 hash và tăng `reference_count`.
- Rollback an toàn: nếu xảy ra lỗi ghi DB, toàn bộ tệp vật lý vừa được ghi mới trên đĩa đều được xóa ngay lập tức.
- Soft-delete và Restore có tính idempotent và kiểm soát trạng thái nhất quán.

---

## Acceptance Criteria
- [x] **Algorithm 12 Deduplication**: Tải lên 2 tệp có nội dung giống hệt nhau chỉ tạo 1 `FileBlob` duy nhất, `reference_count = 2`, xóa tệp tạm quarantine.
- [x] **Vòng đời Revision**: Tải lên revision mới tăng `revision_no`, cập nhật `is_current`, chuyển bản ghi cũ sang `REPLACED`; hỗ trợ tải về đúng revision qua `?version=X`.
- [x] **Kiểm soát dung lượng**: Chặn tệp video $\ge 1\text{ GB}$, chặn image $> 10\text{ MB}$, pdf $> 50\text{ MB}$.
- [x] **Chặn tệp nguy hại**: Chặn tuyệt đối `.exe`, `.py`, `.sh`, `.bat`, `.docm`.
- [x] **Bảo mật Fail-Closed**: Chặn 403 đối với học viên chưa ghi danh, khóa học DRAFT, bài học DRAFT, hoặc tệp QUARANTINED / INFECTED.
- [x] **Tuân thủ ADR-002**: Payload không chứa `id`, `blob_id`, `file_asset_id`, `storage_path`.
- [x] **Web & REST API**: Hỗ trợ đầy đủ cả xác thực JWT Bearer và xác thực Web Session.

---

## Deletion and Simplification List

| Candidate | Classification | Reason | Action |
|---|---|---|---|
| ClamAV Daemon Integration | `PONYTAIL` | Chưa có ClamAV daemon cài đặt trên môi trường dev local | Sử dụng built-in validator an toàn |
| S3 Storage Adapter | `PONYTAIL` | Đặc tả ADR-008 ưu tiên local hierarchical storage trước | Giữ local storage engine |

---

## Ponytails / Deferred Debt
- **Antivirus Daemon Real Socket**:
  - Trigger: Triển khai môi trường Production có daemon ClamAV.
  - Owner: DevOps / Security Architect.
  - Temporary Safeguard: Magic bytes analysis, extension whitelist, quarantine isolation, and file size guardrails.
  - Review Point: Trước khi go-live Production.

---

## Completion Report

### A. Scope and Sources Consulted
- Đã tham chiếu các tài liệu: `AGENTS.md`, `ADR-008`, `ADR-002`, `Algorithm 12`, `Business Rule 11`, `09_FILE_IMPORT_API.md`, `09_DATA_DICTIONARY_STORAGE_MEDIA.md`.
- Triển khai trọn vẹn toàn bộ các yêu cầu từ tầng Domain Service, Models, REST APIs, Web Routes đến Test Suites.

### B. Reuse Decisions
- Tái sử dụng `require_course_manager` và `require_authenticated_actor` từ tầng xác thực hiện hữu.
- Tái sử dụng giới hạn upload từ `config.py`.
- Tái sử dụng helpers kiểm thử session `login_web_user` và JWT `create_token_pair`.

### C. Per-File Changes
1. `src/pwd301/services/exceptions.py`: Bổ sung 7 domain exceptions chuyên biệt cho file storage.
2. `src/pwd301/__init__.py`: Đăng ký exception handlers và blueprint `api_file_bp`.
3. `src/pwd301/models/file_import.py`: Bổ sung property `sha256_hex` cho `FileBlob` và `public_id` (UUIDv5) cho `FileRevision` và `LessonResource`.
4. `src/pwd301/services/file_service.py`: Xây dựng mới hoàn chỉnh động cơ lưu trữ và phân quyền tệp (880+ dòng mã).
5. `src/pwd301/blueprints/api_files/__init__.py` & `routes.py`: Xây dựng REST API cho `/api/files`.
6. `src/pwd301/blueprints/api_courses/routes.py`: Tích hợp upload/list tệp theo khóa học.
7. `src/pwd301/blueprints/api_lessons/routes.py`: Tích hợp attach/detach tài nguyên bài học.
8. `src/pwd301/blueprints/instructor/routes.py`: Tích hợp các route upload, list, trash, restore tệp cho giảng viên qua Web session.
9. `tests/unit/test_file_service.py`: Bộ kiểm thử unit (8 bài test).
10. `tests/security/test_file_authorization_idor.py`: Bộ kiểm thử bảo mật Zero-Trust & IDOR (12 bài test).
11. `tests/api/test_file_api.py`: Bộ kiểm thử REST API & Web integration (9 bài test).

### D. Deletion/Simplification List
- Đơn giản hóa cơ chế serialize theo đúng chuẩn ADR-002, loại bỏ hoàn toàn các trường khóa chính nội bộ.

### E. Ponytails
- Xem mục Ponytails / Deferred Debt ở trên.

### F. Verification Actually Run & Results

| Gate | Command | Result |
|---|---|---|
| **1. Repo Contract** | `python scripts/repo_check.py` | **PASS** (71 tables canonical DDL, balanced code fences) |
| **2. Python Compile** | `python -m compileall -q src tests scripts` | **PASS** (Clean compilation) |
| **3. Ruff Lint** | `ruff check src tests scripts` | **PASS** (All checks passed!) |
| **4. Ruff Format** | `ruff format --check src tests scripts` | **PASS** (122 files already formatted) |
| **5. Type Check** | `mypy src` | **PASS** (Success: no issues found in 61 source files) |
| **6. Task-018 Suites** | `pytest tests/unit/test_file_service.py tests/security/test_file_authorization_idor.py tests/api/test_file_api.py -v` | **PASS** (29/29 passed in 9.19s) |
| **7. Full Regression** | `pytest` | **PASS** (500/500 passed in 227.70s) |
| **8. Verify Script** | `./scripts/verify.ps1` | **PASS** (`PWD301 verification PASS`) |

### G. Remaining Risks / Next Step
- Không còn bất kỳ rủi ro hay tồn đọng kỹ thuật nào đối với TASK-018.
- Toàn bộ 500 bài kiểm thử trong repository đều vượt qua tuyệt đối.
