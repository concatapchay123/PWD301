# TASK-019 — File Security, Quarantine Isolation & Malware Scanning Engine

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-001 through TASK-018  

---

## Goal
Xây dựng và hoàn thiện toàn diện Động cơ an toàn tệp tin, cơ chế cách ly thư mục Quarantine và quét mã độc (Malware Scanning Engine) cho hệ sinh thái PWD301:
1. **Kiến trúc cách ly vật lý Quarantine (Fail-Closed Quarantine Isolation)**:
   - Mọi tệp tải lên ban đầu bắt buộc phải được lưu trữ trong thư mục cách ly `quarantine/` (`FILE_QUARANTINE_ROOT`), tuyệt đối không ghi trực tiếp vào `storage/blobs/`.
   - Tạo bản ghi `FileBlob` với trạng thái `status = 'PRESENT'` khi và chỉ khi đã vượt qua các bài kiểm tra bảo mật sạch (`PASS`).
   - Tuyệt đối không cho phép bất kỳ người dùng nào (kể cả tác giả tệp hay học viên) tải về tệp khi trạng thái chưa là `ACTIVE` / `SAFE` / `CLEAN` (trả về 403 `FileSecurityQuarantineError`).
2. **Hạ tầng quét mã độc đa tầng (Pluggable Malware Scanner Architecture)**:
   - Giao diện `BaseScanner` (ABC).
   - `BuiltinHeuristicScanner`:
     - Nhận diện chuỗi thử nghiệm chuẩn `EICAR` (`X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*`) trong plain text, base64 payload, và bên trong các tệp nén ZIP.
     - Quét sâu heuristic cho PDF (ưu tiên longest marker: `/JavaScript`, `/EmbeddedFiles`, `/Launch`, `/JS` tránh shadowing).
     - Quét sâu OOXML/ZIP (phát hiện macro binary parts `vbaProject.bin`, executable headers `MZ`, scripts nhúng).
     - Phát hiện header spoofing (MZ/ELF trong tệp tài liệu/hình ảnh).
   - `ClamAVScanner`:
     - Kết nối TCP socket tới ClamAV daemon (`nINSTREAM` protocol).
     - Fallback fail-closed an toàn (status `ERROR`, chi tiết lỗi, không làm crash ứng dụng).
3. **Quản lý Vòng đời & Thăng cấp tệp (Blob Promotion / Threat Lifecycle)**:
   - Khi quét **CLEAN** (`PASS`): Thăng cấp tệp từ `quarantine/` sang kho lưu trữ vĩnh viễn phân cấp 2 cấp byte (`storage/blobs/ab/cd/<sha256>`). Cập nhật `FileBlob.status = 'PRESENT'`, `FileRevision.status = 'ACTIVE'`, `FileAsset.status = 'ACTIVE'`, ghi nhận bản ghi chi tiết vào `file_scan_results`.
   - Khi quét **INFECTED** (`FAIL`): Chuyển tệp sang `quarantine/infected/<sha256>`, cập nhật `FileRevision.status = 'REJECTED'`, `FileAsset.status = 'PENDING'`, ghi nhận bản ghi chi tiết `FileScanResult(scan_status='FAIL', signature_name=...)`.
   - Khi quét **ERROR**: Giữ nguyên trong quarantine, cập nhật `FileRevision.status = 'QUARANTINED'`, ghi nhận `FileScanResult(scan_status='ERROR')`, chặn tải về.
4. **Bảo vệ Fail-Closed & Chống rò rỉ thông tin (ADR-002)**:
   - `get_file_for_download` lập tức từ chối với HTTP 403 `FileSecurityQuarantineError` nếu revision/blob chưa được phê duyệt an ninh hoặc bị nhiễm mã độc.
   - Tuyệt đối không để lộ đường dẫn ổ cứng vật lý (`storage_path`, `quarantine_path`) hoặc `BIGINT PK` ra REST API / Web view theo chuẩn ADR-002.
5. **REST API & Web Endpoints cho Giám sát, Quét lại và Giải phóng Cách ly**:
   - `GET /api/files/<asset_id>/scans` & `/api/files/<asset_id>/scan-results`: Xem lịch sử quét an ninh của tệp (chỉ Instructor quản lý khóa học hoặc Admin).
   - `POST /api/files/<asset_id>/rescan`: Kích hoạt quét lại theo yêu cầu (Instructor/Admin).
   - `POST /api/files/<asset_id>/quarantine-override`, `POST /api/admin/files/<asset_id>/quarantine-override`, `POST /admin/files/<asset_id>/quarantine-override`: Admin ghi đè giải phóng cách ly thủ công (bắt buộc kèm lý do giải trình, ghi nhận Audit Event).

---

## Source-of-Truth Documents
- `AGENTS.md` (Operating Contract, Fail-closed Invariants, Video limit $< 1\text{ GB}$, ADR-002 Zero PK Leakage)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/11_FILE_MANAGEMENT.md` & `17_MAJOR_FEATURE_SPECIFICATIONS.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/security/05_FILE_UPLOAD_SECURITY.md` & `09_SECURITY_TEST_PLAN.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/12_FILE_DEDUPLICATION.md`
- `docs/decisions/ADR-008-file-physical-logical.md` & `ADR-002-database-identifiers.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/09_DATA_DICTIONARY_FILES_IMPORT.md` & `006_files_import.sql`

---

## Preconditions
- Hoàn thành trọn vẹn TASK-001 đến TASK-018 với 500/500 tests PASS tuyệt đối.
- Bảng `file_scan_results`, `file_blobs`, `file_revisions`, `file_assets` đã định nghĩa đầy đủ trong reference DDL.

---

## In Scope
1. **Malware Scanning Engine (`src/pwd301/services/scanner_service.py`)**:
   - `ScanVerdict` dataclass với serialization JSON hợp lệ cho ISJSON constraint.
   - `BaseScanner` interface.
   - `BuiltinHeuristicScanner` phát hiện EICAR (plain, base64, zip), PDF dangerous markers (/JavaScript, /EmbeddedFiles, /Launch, /JS), OOXML macros, embedded binaries, and header spoofing.
   - `ClamAVScanner` kết nối daemon clamd TCP socket qua nINSTREAM protocol fail-closed.
   - `scan_file_all_engines` và `scan_blob_file` điều phối quét đa tầng.
2. **File Service Integration (`src/pwd301/services/file_service.py`)**:
   - Tích hợp quét tự động vào quy trình tải lên (`store_file_stream`, `add_file_revision`).
   - Thăng cấp tệp sạch (`quarantine/` -> `storage/blobs/ab/cd/<sha256>`).
   - Cách ly tệp nhiễm mã độc (`quarantine/infected/<sha256>`).
   - Fail-closed download blocking trong `get_file_for_download`.
   - `rescan_file_asset`, `get_file_scan_history`, `quarantine_override` với ghi nhận `AuditEvent`.
3. **Application Routing & Endpoints**:
   - Đăng ký alias `/api/admin` cho `admin_bp` với CSRF exemption trong `src/pwd301/__init__.py`.
   - Endpoints REST API trong `src/pwd301/blueprints/api_files/routes.py`:
     - `GET /api/files/<asset_id>/scans` & `/api/files/<asset_id>/scan-results`
     - `POST /api/files/<asset_id>/rescan`
     - `POST /api/files/<asset_id>/quarantine-override`
   - Endpoints Admin trong `src/pwd301/blueprints/admin/routes.py`:
     - `POST /admin/files/<asset_id>/quarantine-override`
     - `POST /api/admin/files/<asset_id>/quarantine-override`
4. **Test Suites**:
   - `tests/unit/test_malware_scan_service.py` (11 unit tests)
   - `tests/security/test_quarantine_fail_closed.py` (11 security tests)
   - `tests/api/test_scan_api.py` (13 REST API integration tests)

---

## Out of Scope
- Tích hợp ClamAV cloud microservices hoặc daemon bên thứ ba qua internet (sử dụng local TCP socket and heuristic scanner).
- Asynchronous task worker queue (sẽ được tích hợp trong hạ tầng background worker theo roadmap).

---

## Reuse / Existing-Code Inspection
- Tái sử dụng `require_course_manager` và `require_authenticated_actor` từ `src/pwd301/services/authorization_service.py`.
- Tái sử dụng `FileBlob`, `FileAsset`, `FileRevision`, `FileScanResult` từ `src/pwd301/models/file_import.py`.
- Tái sử dụng `AuditEvent` từ `src/pwd301/models/notification_audit.py`.
- Tái sử dụng các exceptions: `FileSecurityQuarantineError`, `FileInfectedError`, `FileAccessDeniedError`, `ValidationError` từ `src/pwd301/services/exceptions.py`.
- Tái sử dụng helper `create_token_pair` và `login_web_user` cho testing.

---

## Planned Changes
- [x] Sửa thứ tự ưu tiên `PDF_DANGEROUS_MARKERS` trong `src/pwd301/services/scanner_service.py` theo thứ tự longest-first để tránh prefix shadowing.
- [x] Đăng ký `api_admin` blueprint alias tại `/api/admin` và miễn trừ CSRF trong `src/pwd301/__init__.py`.
- [x] Hoàn thiện bộ kiểm thử unit `tests/unit/test_malware_scan_service.py` (11 tests).
- [x] Hoàn thiện bộ kiểm thử security `tests/security/test_quarantine_fail_closed.py` (11 tests).
- [x] Xây dựng mới hoàn chỉnh bộ kiểm thử REST API `tests/api/test_scan_api.py` (13 tests).
- [x] Chạy toàn bộ 8 cổng xác minh chất lượng mã nguồn: repo_check, compileall, ruff check, ruff format, mypy src, task test suites, full regression pytest, và verify.ps1.

---

## Security / Authorization Impact
- Bảo mật Fail-Closed: Tuyệt đối không cho phép tải về tệp chưa sạch hoặc có nghi vấn mã độc.
- Chống rò rỉ định danh (ADR-002): Không lộ `BIGINT PK` hay đường dẫn vật lý cục bộ trong bất kỳ phản hồi nào.
- Chống Path Traversal: Khử bỏ ký tự điều hướng thư mục và null byte.
- Kiểm soát can thiệp Admin: Quarantine override bắt buộc có lý do giải trình và lưu AuditEvent bất biến.

---

## Database / Migration Impact
- Tuân thủ tuyệt đối schema 71 bảng hiện hữu, không sửa đổi hay thêm bảng ngoài canonical DDL.
- Dữ liệu `file_scan_results` tuân thủ check constraint `scan_type`, `status IN ('PASS','FAIL','ERROR')`, và `ISJSON(details_json)=1`.

---

## Acceptance Criteria
- [x] **Quarantine Isolation**: Tệp tải lên ban đầu luôn nằm trong `quarantine/`, chỉ thăng cấp sang `storage/blobs/` khi verdict là `PASS`.
- [x] **Infection Isolation**: Tệp nhiễm mã độc bị chuyển vào `quarantine/infected/`, revision bị đánh dấu `REJECTED`.
- [x] **Fail-Closed Download**: Tệp `QUARANTINED` hoặc `INFECTED` bị từ chối 403 khi học viên/người dùng tải về.
- [x] **Multi-tier Scanning**: Nhận diện thành công EICAR (plain/b64/zip), macro OOXML, executable headers MZ/ELF, và stream PDF độc hại.
- [x] **ClamAV Resilience**: Không crash ứng dụng khi daemon clamd không khả dụng, trả về verdict `ERROR` an toàn.
- [x] **Admin Override**: Chỉ Admin mới có thể override với lý do bắt buộc, tạo `AuditEvent` và giải phóng tệp thành `ACTIVE`.
- [x] **REST API**: Các endpoints scans, scan-results, rescan, quarantine-override hoạt động chuẩn xác với ma trận phân quyền Zero-Trust.

---

## Verification Actually Run & Results

| Gate | Command | Result |
|---|---|---|
| **1. Repo Contract** | `python scripts/repo_check.py` | **PASS** (71 tables canonical DDL, balanced code fences) |
| **2. Python Compile** | `python -m compileall -q src tests scripts` | **PASS** (Clean bytecode compilation) |
| **3. Ruff Lint** | `ruff check src tests scripts` | **PASS** (All checks passed!) |
| **4. Ruff Format** | `ruff format --check src tests scripts` | **PASS** (126 files already formatted) |
| **5. Type Check** | `mypy src` | **PASS** (Success: no issues found in 62 source files) |
| **6. TASK-019 Suites** | `pytest tests/unit/test_malware_scan_service.py tests/security/test_quarantine_fail_closed.py tests/api/test_scan_api.py -v` | **PASS** (35/35 passed in 13.53s) |
| **7. Full Regression** | `pytest` | **PASS** (535/535 passed in 324.76s) |
| **8. Verify Script** | `./scripts/verify.ps1` | **PASS** (`PWD301 verification PASS`, 535 passed in 299.47s) |

---

## Ponytails / Deferred Debt
- **External ClamAV Production Cluster**:
  - Trigger: Triển khai lên cụm máy chủ Production với dịch vụ ClamAV daemon chạy nền liên tục.
  - Owner: DevOps & SecOps Team.
  - Temporary Safeguard: `BuiltinHeuristicScanner` (static signatures, deep PDF/OOXML inspection, header spoofing guard) cùng fallback `ERROR` fail-closed an toàn của `ClamAVScanner`.
  - Review Point: Production deployment readiness review.
