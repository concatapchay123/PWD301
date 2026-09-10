# TASK-020 — DOCX/PDF Assessment & Question Import Engine

**Status:** DONE  
**Assignee:** Principal Software Architect & Lead Fullstack Python/Flask Engineer  
**Depends on:** TASK-011, TASK-018, TASK-019  

---

## Goal
Xây dựng và hoàn thiện toàn diện **Động cơ phân tích, đối soát trùng lặp và nhập liệu câu hỏi từ tài liệu DOCX/PDF (DOCX/PDF Assessment Import Engine)** cho giảng viên vào Ngân hàng câu hỏi (Question Bank) của Khóa học:
1. **Tích hợp chặt chẽ hạ tầng tệp tin an toàn (Fail-Closed File Pipeline)**:
   - Tệp DOCX/PDF tải lên để nhập câu hỏi bắt buộc phải đi qua quy trình kiểm soát an ninh của `TASK-018` và `TASK-019`: lưu tại thư mục cách ly `quarantine/`, quét sạch mã độc (Heuristic + ClamAV) và chuyển trạng thái `PASS`, `ACTIVE`, `PRESENT`.
   - Nếu tệp đang ở trạng thái cách ly (`QUARANTINED`, `REJECTED`, `INFECTED`), hệ thống lập tức từ chối xử lý và trả về HTTP 403 `FileSecurityQuarantineError`.
2. **Động cơ bóc tách văn bản đa định dạng (Pluggable Document Parser)**:
   - Bóc tách OpenXML DOCX thuần túy bằng thư viện chuẩn `zipfile` và `xml.etree.ElementTree` (không phụ thuộc external service nặng nề).
   - Bóc tách PDF linh hoạt thông qua `pypdf` với cơ chế token stream fallback khi cấu trúc PDF bị phân mảnh hoặc thiếu font map.
3. **Động cơ nhận diện mẫu câu hỏi (Pattern Matcher Engine)**:
   - Nhận diện 5 loại câu hỏi chuẩn: `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `ESSAY`.
   - Bóc tách thân câu hỏi (stem), các phương án lựa chọn (A/B/C/D), đáp án đúng (Answer key), mức độ Bloom (`[REMEMBER|UNDERSTAND|APPLY]`), điểm số và lời giải thích.
   - Tính toán điểm tin cậy (confidence score) và gắn cờ cảnh báo chẩn đoán (`warnings`) khi câu hỏi có tính nhập nhằng hoặc thiếu đáp án.
4. **Động cơ đối soát trùng lặp (Duplicate Detection Engine)**:
   - Chuẩn hóa văn bản câu hỏi: chữ thường, loại bỏ số thứ tự ("Câu 1:", "Question 1."), ký tự đặc biệt và khoảng trắng thừa.
   - Khớp băm chính xác (Exact Hash) qua SHA-256 đối chiếu với Question Bank hiện tại của khóa học và các câu hỏi trong cùng đợt nhập.
   - Đối soát tương đồng mờ (Fuzzy Similarity) qua `difflib.SequenceMatcher` với ngưỡng tương đồng $\ge 0.85$, tự động tạo các bản ghi `ImportDuplicateCandidate`.
5. **Quy trình phê duyệt và xác nhận nguyên tử (Review & Atomic Commit Pipeline)**:
   - Máy trạng thái vòng đời công việc: `QUEUED` -> `PROCESSING` -> `REVIEW_REQUIRED` -> `COMPLETED` / `FAILED` / `CANCELLED`.
   - Giao diện và API cho phép giảng viên xem trước, chỉnh sửa (PATCH), duyệt (`ACCEPTED`) hoặc từ chối (`REJECTED`) từng câu hỏi.
   - Cam kết nguyên tử (Atomic Commit): chỉ ghi nhận các câu hỏi `ACCEPTED` vào các thực thể chuẩn `Question`, `QuestionRevision`, `QuestionRevisionChoice`, và `QuestionProvenance(source_type='IMPORT')`.
6. **Tuân thủ tuyệt đối ADR-002 (Zero PK Leakage)**:
   - Các API và view trả về public UUIDs, không làm rò rỉ `BIGINT PK/FK` nội bộ hay đường dẫn tệp tin vật lý.

---

## Source-of-Truth Documents Consulted
- `AGENTS.md` (Source-of-truth hierarchy, Fail-closed Invariants, ADR-002 Zero PK Leakage)
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/12_DOCX_PDF_IMPORT.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/IMPORT_STATE_MACHINE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/api/09_FILE_IMPORT_API.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/business/10_ASSESSMENT_ENGINE.md`
- `docs/system/PWD301_SYSTEM_SPECIFICATION/algorithms/05_BLUEPRINT_MATERIALIZATION.md`
- `docs/decisions/ADR-002-database-identifiers.md`
- `docs/database/PWD301_DATABASE_ARCHITECTURE/09_DATA_DICTIONARY_FILES_IMPORT.md`

---

## Deliverables & Changes
1. **Domain Exceptions (`src/pwd301/services/exceptions.py`)**:
   - `DocumentImportError`, `DocumentParsingError`, `DocumentImportJobNotFoundError`, `DocumentImportStateViolationError`, `ImportQuestionNotFoundError`.
2. **Central Application Registration (`src/pwd301/__init__.py`)**:
   - Centralized exception handlers registered in `DOMAIN_EXCEPTION_HANDLERS`.
   - Registered `api_import_bp` at `/api/imports` with CSRF exemption for JWT API requests.
3. **Database Model Synthetic UUIDs (`src/pwd301/models/file_import.py`)**:
   - Added `public_id` properties with deterministic UUIDv5 mapping for `ImportQuestion` and `ImportDuplicateCandidate` conforming to ADR-002.
4. **Import Engine Core Service (`src/pwd301/services/import_service.py`)**:
   - `extract_text_from_docx`: OpenXML DOCX paragraph extraction via stdlib.
   - `extract_text_from_pdf`: Resilient PDF text extraction with content stream token fallback.
   - `parse_question_blocks`: Robust pattern matcher supporting 5 question types, Bloom levels, points, explanation, and confidence scoring.
   - `detect_duplicates`: SHA-256 exact hash + SequenceMatcher fuzzy similarity ($\ge 0.85$).
   - `create_import_job`: Fail-closed security validation (ACTIVE, PRESENT, PASS scans).
   - `process_import_job`: Orchestration of parsing, duplicate detection, and transition to `REVIEW_REQUIRED`.
   - `update_import_question` & `set_import_question_decision`: In-flight review and curation.
   - `commit_import_job`: Atomic transaction creating canonical `Question`, `QuestionRevision`, and `QuestionProvenance`.
   - `cancel_import_job`: Cancellation transition.
5. **REST API & Course Endpoints (`src/pwd301/blueprints/api_import/` & `src/pwd301/blueprints/api_courses/`)**:
   - `POST /api/imports` & `POST /api/courses/<course_id>/imports`: Create import job.
   - `GET /api/courses/<course_id>/imports`: List course imports.
   - `GET /api/imports/<job_id>`: Job details and extracted questions.
   - `POST /api/imports/<job_id>/process`: Trigger processing.
   - `PATCH /api/imports/<job_id>/questions/<temp_id>`: Edit question draft.
   - `POST /api/imports/<job_id>/questions/<temp_id>/decision`: Accept/Reject draft.
   - `POST /api/imports/<job_id>/commit`: Atomic commit.
   - `POST /api/imports/<job_id>/cancel`: Cancel job.
6. **Instructor Web Routes (`src/pwd301/blueprints/instructor/routes.py`)**:
   - Connected Web session endpoints with CSRF protection under `/instructor/courses/<id>/imports` and `/instructor/imports/<id>/...`.
7. **Comprehensive Test Suites**:
   - `tests/unit/test_import_service.py` (8 unit tests)
   - `tests/security/test_import_idor.py` (8 security and IDOR tests)
   - `tests/api/test_import_api.py` (9 REST API and web integration tests)

---

## Verification Results
- Gate 1: `python scripts/repo_check.py` — **PASS**
- Gate 2: `python -m compileall -q src tests scripts` — **PASS**
- Gate 3: `ruff check src tests scripts` — **PASS** (0 errors)
- Gate 4: `ruff format --check src tests scripts` — **PASS** (132 files already formatted)
- Gate 5: `mypy src` — **PASS** (0 issues across 65 source files)
- Gate 6: TASK-020 test suites — **PASS** (25/25 passed)
- Gate 7: Full regression pytest — **PASS** (560/560 passed)
- Gate 8: `./scripts/verify.ps1` — **PASS**
