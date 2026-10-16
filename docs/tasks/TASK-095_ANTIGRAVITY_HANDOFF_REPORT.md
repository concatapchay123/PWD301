# BÁO CÁO BÀN GIAO THỰC THI VÀ NGHIỆM THU TASK-095 (ANTIGRAVITY -> CODEX)

> **Mã công việc:** TASK-095 — Thay thế và hoàn thiện triệt để Unified Course Approval Workflow, Question COW Blueprint, Admin Categorized Diff, DRM Video Playback, SQL Target Concurrency & Result Disclosure Matrix.  
> **Thời điểm chốt báo cáo:** 16/10/2026, Asia/Bangkok.  
> **Trạng thái:** HOÀN TẤT THỰC THI VÀ XÁC MINH THỰC NGHIỆM TẠI CHECKPOINT — SẴN SÀNG BÀN GIAO ĐỂ CODEX KIỂM CHỨNG ĐỘC LẬP.  
> **Văn bản căn cứ pháp lý & kỹ thuật:**  
> - [WORKFLOW_SUPERSESSION.md](file:///e:/PWD301/docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md)  
> - [2026-10-16-task095-antigravity-handoff.md](file:///e:/PWD301/docs/superpowers/plans/2026-10-16-task095-antigravity-handoff.md)  
> - [AGENTS.md](file:///e:/PWD301/AGENTS.md)  

---

## A. PHẠM VI CÔNG VIỆC VÀ TÀI LIỆU NGUỒN SỰ THẬT (SCOPE & SOURCES)

### 1. Nguồn sự thật đã tuân thủ tuyệt đối
1. `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md` (Hợp đồng tối cao thay thế hoàn toàn workflow duyệt bài lẻ và staging tùy chọn).
2. `docs/database/PWD301_DATABASE_ARCHITECTURE/` (ERD, DDL SQL Server canonical, trigger bất biến `trg_file_revisions_current_active`, `trg_knowledge_versions_current_active`).
3. `docs/superpowers/plans/2026-10-16-task095-antigravity-handoff.md` (Kế hoạch 10 vòng, 5 kịch bản trình duyệt B01–B05, runner SQL target độc quyền).
4. `AGENTS.md` (Quy tắc bất biến: Headless REST API thuần túy, không chạm DB live, không nới lỏng bảo mật, trung thực 100% về kết quả kiểm thử).

### 2. Snapshot bàn giao và tính toàn vẹn mã nguồn
- **Git Branch:** `codex/workflow-remediation-20261015`
- **Git HEAD Commit:** `838e8b5eee09f8c485102d6d2eba0a325765951d`
- **Tình trạng working tree:** 117 tệp tin thay đổi và tệp untracked được bảo toàn 100%, không commit, không stash, không reset, không push, không đụng chạm DB live.
- **Manifest SHA256 Baseline P0:** [P0_BASELINE_MANIFEST.json](file:///e:/PWD301/output/task095-antigravity/P0_BASELINE_MANIFEST.json)
- **Manifest SHA256 Final Verification:** [FINAL_VERIFICATION_MANIFEST.json](file:///e:/PWD301/output/task095-antigravity/FINAL_VERIFICATION_MANIFEST.json)

### 3. Phạm vi loại trừ (Out of Scope / Non-Goals)
- Không commit, push, deploy lên staging/production hoặc chạy migration trên DB live.
- Không phục hồi giao diện Jinja template hoặc mock static frontend.

---

## B. QUYẾT ĐỊNH TÁI SỬ DỤNG (REUSE DECISIONS)

1. **Khung duyệt nháp tổng hợp (Unified Staging Draft):** Tái sử dụng `CourseChangeRequest` với `change_type='COURSE_VERSION_CHANGESET'` và `status='DRAFT'`. Không tạo bảng duyệt hay hệ thống state machine thứ hai.
2. **Khóa giao dịch đồng thời (Pessimistic Concurrency):** Tái sử dụng `SELECT ... WITH (UPDLOCK, ROWLOCK)` trên SQL Server để đảm bảo chỉ DUY NHẤT một aggregate `DRAFT` hoạt động và chỉ DUY NHẤT một Admin phê duyệt thành công một snapshot niêm phong.
3. **Bộ kết xuất toán học ngoại tuyến (Offline Math Rendering):** Tái sử dụng `tools/mathjax-tex2svg.js` (MathJax Node CLI ngoại tuyến) kết hợp `svglib` và `ReportLab` chuẩn Linux/Alpine, không phụ thuộc font hệ thống Windows và không gọi external network CDN.
4. **Kiểm tra Fail-Closed cho File & Ảnh bìa:** Tái sử dụng pipeline kiểm tra quét virus ClamAV (`has_passed_malware_scan`, `virus_scan_status == 'CLEAN'`). Không cho phép xem/tải trước khi duyệt.

---

## C. CHI TIẾT THAY ĐỔI THEO TỪNG TỆP TIN (PER-FILE CHANGES)

### 1. Khắc phục P1 Blocker 1: Lesson Marker vòng duyệt thứ 2 (`src/pwd301/services/lesson_service.py`)
- **Vấn đề gốc:** Trong hàm `_apply_sealed_course_changeset`, các bài học `PUBLISHED` sau khi được Admin duyệt vẫn giữ `lesson.change_request_id` trỏ về request cũ đã kết thúc (`APPROVED`). Khi giảng viên tiếp tục chỉnh sửa bài học ở vòng duyệt tiếp theo, hệ thống hiểu nhầm bài học đã được duyệt là bài nháp thuộc changeset cũ, làm sai lệch baseline fingerprint và gãy chu trình detach/clone lần 2.
- **Giải pháp:** Bổ sung `lesson.change_request_id = None` tại line 2813 của `lesson_service.py` khi apply promotion thành công bài học sang `PUBLISHED`.
- **Kiểm chứng:** 32/32 tests trong `test_unified_course_workflow.py` và 9/9 tests trong `test_file_api.py` đạt 100%.

### 2. Khắc phục P1 Blocker 2: COW Question Blueprint Shortage (`src/pwd301/services/course_assessment_workflow.py` & `assessment_service.py`)
- **Vấn đề gốc:** `publish_assessment` và `materialize_blueprint_pool` lọc câu hỏi bằng điều kiện thô `Question.status == 'ACTIVE'`, chỉ tìm trong ngân hàng câu hỏi live. Khi câu hỏi mới được tạo trong draft changeset (`Question.change_request_id == draft.id`), chúng bị bỏ qua, dẫn đến lỗi blueprint thiếu câu hỏi khả dụng (`available 0 < required 1`).
- **Giải pháp:** Sử dụng `effective_question_query` và `question_status_expression(assessment.course_id, sess) == 'ACTIVE'`, cho phép projection nhận diện câu hỏi nháp thuộc chính draft của khóa học khi preflight và materialize.
- **Kiểm chứng:** 21/21 tests trong `test_course_question_workflow.py` đạt 100%.

### 3. Khắc phục P1 Blocker 3: Admin Categorized Deep Diff & Zero Changes Bug (`src/pwd301/services/lesson_service.py` & `frontend/assets/js/ui.js`)
- **Vấn đề gốc:** Hàm `get_course_changeset_diff` không trích xuất `question_changes`, `file_changes`, `prerequisite_changes` (chỉ hiển thị mảng UUID trần không rõ tên môn), và `metadata_changes`. Biến `total_changes_count` không cộng các danh mục này. Khi giảng viên chỉ đổi câu hỏi, chỉ đính kèm file, hoặc chỉ đổi môn tiên quyết, Admin review modal báo `0 thay đổi` và hiển thị thông báo giả: *"Chưa phát hiện thay đổi nào so với giáo trình hiện tại"*.
- **Giải pháp:**
  - **Backend (`lesson_service.py`):** Cập nhật `submit_course_changeset` lưu `questions`, `new_file_assets`, `course_metadata`, `prerequisites`, `completion_rules` vào `submitted_snapshot`. Cập nhật `get_course_changeset_diff` trích xuất đầy đủ 4 danh mục trên, tra cứu tên môn `[course_code] title` cho môn tiên quyết, và cộng dồn vào `total_changes_count`.
  - **Frontend (`frontend/assets/js/ui.js`):** Mở rộng `UI.renderCategorizedDiffHtml(diff)` bổ sung 4 khối giao diện tương ứng với đầy đủ nhãn tiếng Việt chuẩn mực, badge thêm/xóa/sửa và cảnh báo an toàn.
- **Kiểm chứng:** 4/4 tests trong `tests/api/test_course_changeset_deep_diff.py`, 11/11 tests trong `tests/frontend/admin_review_identity_and_covers.test.js`, và 318/318 frontend Node tests đạt 100%.

### 4. Khắc phục SQL Server Invariant Trigger Error 51010 (`tests/api/test_course_cover_media_authorization.py`)
- **Vấn đề gốc:** Khi chạy test `test_public_resource_cover_remains_fail_closed_after_unsafe_scan[QUARANTINED]` trên SQL Server target, cơ sở dữ liệu kích hoạt trigger `trg_file_revisions_current_active` và ném lỗi `THROW 51010, 'Current file revision must have status ACTIVE.'`. Lý do là fixture test chỉ gán `image.current_revision.status = 'QUARANTINED'` mà không gán `is_current = False`, vi phạm bất biến SQL Server rằng phiên bản current bắt buộc phải có trạng thái `ACTIVE`.
- **Giải pháp:** Cập nhật fixture gán đồng thời `image.current_revision.is_current = False` và `image.current_revision.status = 'QUARANTINED'` đúng theo logic sản xuất trong `src/pwd301/services/file_service.py:1964`.
- **Kiểm chứng:** 6/6 tests trong `tests/api/test_course_cover_media_authorization.py` và toàn bộ 45 tests trong `tests/unit/test_file_unified_authoring.py` đạt 100% trên SQL Server target.

### 5. Dọn dẹp Linting & Type Safety (`src/` và `tests/`)
- Khắc phục các cảnh báo unused import, unused variable, và unformatted imports theo chuẩn `ruff check`, `ruff format` và `mypy` (101 source files no issues).

---

## D. DANH MỤC THU DỌN VÀ ĐƠN GIẢN HÓA (DELETION & SIMPLIFICATION)

1. **Gỡ bỏ cơ chế xét duyệt tiên quyết phân mảnh:** Hàm `enrollment_service.approve_or_reject_prerequisite_request` và endpoint `handle_prerequisite_request_api` chính thức nâng lên ném `ConflictError` hướng dẫn chuyển toàn bộ môn tiên quyết vào bản nháp tổng hợp `COURSE_VERSION_CHANGESET`.
2. **Loại bỏ nhầm lẫn marker giữa các vòng duyệt:** Triệt tiêu hoàn toàn mã rác giữ lại `change_request_id` trên bài học live.
3. **Loại bỏ hiển thị ID kỹ thuật:** Mọi ID môn tiên quyết dạng UUID trần trên giao diện Admin Review đều được thay thế bằng chuỗi tường minh `[MÃ_MÔN] Tên môn học`.

---

## E. NỢ KỸ THUẬT VÀ GIỚI HẠN GHI NHẬN (PONYTAIL / DEFERRED DEBT)

| ID | Vấn đề / Giới hạn | Lý do tạm hoãn | Biện pháp bảo vệ hiện có | Thời điểm xem xét lại |
|---|---|---|---|---|
| **DEBT-01** | Trình duyệt chỉ ngăn chặn sao chép/tải xuống ở mức hợp lý (DevTools / Screen recorder không thể chặn 100% về mặt vật lý) | Giới hạn nền tảng Web tiêu chuẩn | Watermark động hiển thị email/IP, DRM AES-128 HLS phân mảnh, token thời hạn ngắn | Khi tích hợp giải pháp Widevine / PlayReady DRM native |
| **DEBT-02** | YouTube Video pacing yêu cầu heartbeat thời gian thực | YouTube iframe API chạy client-side | Pacing trên server clock ghi nhận nhịp tim tích lũy, từ chối nhảy cóc | Khi có nhu cầu chuyển 100% video sang self-hosted HLS |

---

## F. KẾT QUẢ KIỂM CHỨNG THỰC TẾ (VERIFICATION ACTUALLY RUN & RESULTS)

Tất cả các lệnh dưới đây đã được chạy thực tế trong phiên làm việc trên môi trường Windows PowerShell, Python 3.12.10, Node v22.18.0, Microsoft Edge headless và SQL Server 2022 Express:

### 1. Gate Hợp đồng & Kiểm tra Tĩnh (Static Gates)
```powershell
# 1.1 Repo contract check
.venv/Scripts/python.exe scripts/repo_check.py
# Kết quả: EXIT 0 (Tất cả 7 gates PASS)

# 1.2 Python compileall
.venv/Scripts/python.exe -m compileall -q src tests scripts migrations
# Kết quả: EXIT 0

# 1.3 Ruff lint & format check
.venv/Scripts/ruff.exe check src tests scripts migrations
.venv/Scripts/ruff.exe format --check src tests scripts migrations
# Kết quả: EXIT 0 (All checks passed, 364 files already formatted)

# 1.4 Mypy Type Checking
.venv/Scripts/mypy.exe src
# Kết quả: EXIT 0 (Success: no issues found in 101 source files)
```

### 2. Gate Frontend Node Test Suite (Toàn bộ 100%)
```powershell
$FrontendTests = @(Get-ChildItem tests/frontend -Filter '*.test.js' -File | Sort-Object FullName | Select-Object -ExpandProperty FullName)
node --test --test-concurrency=2 --test-reporter=junit --test-reporter-destination=output/task095-antigravity/frontend-final.xml $FrontendTests
# Kết quả: EXIT 0
# Tổng số test: 318 passed, 0 failed, 0 errors (100% PASS)
# Artifact: output/task095-antigravity/frontend-final.xml
```

### 3. Gate SQL Server Target Riêng Cô Lập (`pwd301_test_task095_20261016`)
```powershell
# 3.1 Migration Roundtrip (Upgrade Head -> Downgrade Base -> Upgrade Head)
$env:PYTHONPATH = 'src;.'
.venv/Scripts/python.exe .superpowers/task095/sql_target.py -m pytest tests/integration/test_sqlserver_migration_roundtrip.py::test_sqlserver_migrations_upgrade_downgrade_upgrade_roundtrip -q
# Kết quả: EXIT 0 (1 passed in 3.03s)

# 3.2 SQL Server Concurrency & Transaction Workflow
.venv/Scripts/python.exe .superpowers/task095/sql_target.py -m pytest tests/integration/test_sqlserver_unified_course_workflow.py -v
# Kết quả: EXIT 0 (5 passed in 18.37s)
# - test_concurrent_authors_share_one_draft_without_losing_fields: PASSED
# - test_stale_author_session_observes_pending_freeze: PASSED
# - test_concurrent_opposite_prerequisites_cannot_create_projected_cycle: PASSED
# - test_concurrent_approval_has_one_atomic_winner: PASSED
# - test_filtered_unique_index_rejects_duplicate_active_aggregate: PASSED

# 3.3 SQL Server File Authoring & Cover Authorization
.venv/Scripts/python.exe .superpowers/task095/sql_target.py -m pytest tests/unit/test_file_unified_authoring.py tests/api/test_course_cover_media_authorization.py -q
# Kết quả: EXIT 0 (51 passed in 196.30s: 45 file authoring + 6 cover media)
```
**Tổng số test SQL Server thực tế:** 57 passed, 0 failed, 0 errors (100% PASS).

### 4. Gate Core Backend Python Suites
```powershell
.venv/Scripts/python.exe -m pytest tests/unit/test_unified_course_workflow.py tests/unit/test_course_question_workflow.py tests/unit/test_course_review_assets.py tests/unit/test_course_assessment_review_lock.py tests/unit/test_file_unified_authoring.py tests/api/test_course_changeset_deep_diff.py tests/api/test_course_changeset_workflow.py tests/api/test_prerequisite_approval_workflow.py tests/api/test_prerequisite_cross_instructor.py tests/test_result_pdf_formatting.py tests/api/test_assessment_review_policy.py tests/test_6_categories_verification.py tests/unit/test_workflow_document_contract.py tests/unit/test_course_staging_draft.py tests/api/test_file_api.py --junitxml=output/task095-antigravity/backend-core.xml -q
# Kết quả: EXIT 0
# Tổng số test: 178 passed in 162.39s, 0 failed, 0 errors, 0 skipped
# Artifact: output/task095-antigravity/backend-core.xml
```

### 5. Gate Trình Duyệt Thực Tế B01–B05 (Playwright + Microsoft Edge Headless)
Môi trường chạy: Port 51095 trên server fixture cô lập `pwd301_test_browser.sqlite`.
- **Kịch bản B01 & B02 (`browser_root.cjs`):**
  - Mở modal Cài đặt học vụ, kiểm tra dropdown môn tiên quyết (>1 options), kiểm tra không bị tràn màn hình mobile (viewport 390x844).
  - Kết quả: `login: 200`, `prerequisiteOptions: 5`, `mobileOverflow: false`, `pageErrors: []`.
  - Ảnh minh chứng: [instructor-academic-desktop.png](file:///e:/PWD301/output/task095-antigravity/instructor-academic-desktop.png), [instructor-academic-mobile.png](file:///e:/PWD301/output/task095-antigravity/instructor-academic-mobile.png).
- **Kịch bản B04 Matching Exam (`browser_matching.cjs`):**
  - Học viên nối 2 cặp khái niệm, đường nối màu trung tính `#38bdf8` (không rò đáp án đúng/sai khi đang làm bài), xóa cặp nối, nối bằng bàn phím (phím Enter), chuyển đổi responsive sang mobile 390x844.
  - Kết quả: `unverifiedStudentLogin: 200`, `matchingPairs: 2`, `neutralLines: ["#38bdf8", "#38bdf8"]`, `clear: true`, `keyboard: true`, `pageErrors: []`.
  - Ảnh minh chứng: [student-matching-desktop.png](file:///e:/PWD301/output/task095-antigravity/student-matching-desktop.png), [student-matching-mobile.png](file:///e:/PWD301/output/task095-antigravity/student-matching-mobile.png).
- **Kịch bản B03 & B04 Video & Exam Waiting Room (`browser_learning.cjs`):**
  - Kiểm tra waiting room: Chính sách `HIGHEST` hiển thị 3/3 lượt, điểm 10/10; Chính sách `LATEST` hiển thị 2/2 lượt (hết lượt), điểm 0/10; cả 2 đều không bị khóa điều kiện tiên quyết giả.
  - Kiểm tra phát Video HLS Native thật: video kích thước 320x180, phát liên tục `currentTime > 1` (1.017671s), `readyState: 4`, `media.error: null`.
  - Kết quả: PASS 100%, 0 page errors.
  - Dữ liệu minh chứng: [browser-learning-proof.json](file:///e:/PWD301/output/task095-antigravity/browser-learning-proof.json).
  - Ảnh minh chứng: [exam-highest-desktop.png](file:///e:/PWD301/output/task095-antigravity/exam-highest-desktop.png), [exam-latest-desktop.png](file:///e:/PWD301/output/task095-antigravity/exam-latest-desktop.png), [native-hls-desktop.png](file:///e:/PWD301/output/task095-antigravity/native-hls-desktop.png).
- **Kịch bản Quyền File & HLS AES-128 (`browser_media_proof.py`):**
  - Kiểm tra 25 trường hợp ma trận quyền của 5 vai trò (`student`, `verified`, `instructor`, `admin`, `outsider`).
  - Học viên bị chặn tải raw video (403), nhưng Range 206 hoạt động đối với giảng viên và quản trị viên.
  - HLS AES-128 phục vụ thành công: `playlist.m3u8` (200), `key` (200, 16 bytes), `segment` (200, >188 bytes).
  - Kết quả: `checks: 25, all_passed: true`.
  - Dữ liệu minh chứng: [browser_media_proof.json](file:///e:/PWD301/output/task095-antigravity/browser_media_proof.json).

### 6. Gate PDF Production & Toán Học Ngoại Tuyến
- 14/14 tests trong `tests/test_result_pdf_formatting.py` đạt 100%.
- Bảng chi tiết kết quả khi tắt công tắc xem chi tiết (`allow_student_view_results=False`): Ba cột `Đáp án đã chọn`, `Kết quả`, `Điểm` thực sự rỗng hoàn toàn, không có ký tự gạch nối, không rò nội dung; tổng điểm/đạt-trượt đã công bố vẫn bảo toàn chính xác.

---

## G. RỦI RO CÒN LẠI VÀ BƯỚC TIẾP THEO CHO CODEX (REMAINING RISKS & NEXT STEPS)

1. **Khuyến nghị cho Codex:**
   - Codex có thể tự chọn chạy lại bất kỳ bộ kiểm thử nào trong số các tệp trên để kiểm chứng độc lập.
   - Thẩm tra chi tiết diff giữa baseline và mã nguồn hiện tại thông qua [FINAL_VERIFICATION_MANIFEST.json](file:///e:/PWD301/output/task095-antigravity/FINAL_VERIFICATION_MANIFEST.json).
   - Xác nhận mọi thay đổi mã nguồn đã được giữ nguyên vẹn trên branch `codex/workflow-remediation-20261015`.
2. **Kế hoạch tiếp theo:**
   - Sau khi Codex hoàn tất nghiệm thu độc lập trên môi trường phát triển, tiến hành lập kế hoạch staging release theo quy trình đóng băng và kiểm định chuẩn mực của dự án.
