# Kế hoạch Triển khai: Hệ thống Thẩm định Sửa đổi Toàn diện (Admin Deep Diff), Hiện đại hóa Nút Thao tác & Xuất Bảng điểm PDF Học vụ

> **Tài liệu Kế hoạch:** `docs/superpowers/plans/2026-10-09-admin-review-diff-and-pdf-export.md`  
> **Mục tiêu:** Giải quyết triệt để 4 lỗi hệ thống nghiêm trọng, đồng thời xóa sạch toàn bộ logic, mô tả, bộ nhớ và tàn dư của luồng workflow cũ để thiết lập chuẩn mực mới thống nhất trên toàn hệ thống PWD301.  
> **Trạng thái:** Chờ Chủ dự án phê duyệt (`/plan`) trước khi tiến hành viết mã.  
> **Ngày lập:** 09/10/2026  

---

## 1. Bối cảnh & Mục tiêu Cốt lõi

Qua quá trình kiểm thử thực tế trên cả Backend và Frontend, hệ thống đang gặp phải 4 vấn đề nghiêm trọng:
1. **Lỗi hiển thị Thẩm định Sửa đổi (Admin Diff View)**: Admin không xem được chi tiết giảng viên đã sửa những gì. Cả hai cột Trước vs Sau hiển thị giống hệt nhau hoặc hiển thị nhãn mơ hồ "Thay đổi khác" mà không có đánh dấu thay đổi trực quan (visual diff).
2. **Nút Thao tác Chi tiết & Popup Xác nhận**: 2 nút trong trang thẩm định đang mang tên dài dòng `"Từ chối yêu cầu"` và `"Phê duyệt & Áp dụng thay đổi"`, đồng thời khi ấn nút Duyệt thì hệ thống duyệt thẳng mà không có popup xác nhận.
3. **Nút Thao tác Hàng đợi (Queue Table)**: Tại bảng danh sách yêu cầu thay đổi (`#admin/governance?tab=courses`), các nút đang bị ngược thứ tự và sai tên (`[✓ Duyệt]` trước, `[Xét duyệt]` sau). Cần chuẩn hóa thành: `[Xem]` (xem chi tiết) trước, `[Duyệt]` (duyệt nhanh) sau.
4. **Lỗi Xuất Bảng điểm PDF**:
   - Nút "Xuất bảng điểm (PDF)" của Sinh viên tại `#/student/assessments/results` tải về file lỗi `result.json` hoặc bị trình duyệt Windows báo hỏng do link `<a download>` không bắt lỗi API và thiếu chuẩn mã hóa RFC 5987 / UTF-8.
   - Thiếu tính năng "Xuất bảng điểm PDF lớp học" cho Giảng viên & Admin tại trang `#/instructor/courses/<id>/assessments/<id>/results`.

**Yêu cầu Tiên quyết của Chủ dự án:**
> *"Trước khi bắt tay vào làm hãy xóa sạch toàn bộ logic, bộ nhớ cũ, logic cũ, mô tả cũ,... mọi vấn đề, chức năng cũ của luồng workflow về những chỉnh sửa, thay đổi này toàn hệ thống và thay bằng cái mới để chắc chắn rằng khi làm xong kế hoạch này thì sau này khi mình nhớ bạn thực hiện 1 chức năng khác bạn không vô tình thấy bản thiết kế cũ của workflow này mà làm lại như cũ khiến bao công sức đổ sông đổ biển."*

---

## 2. Giai đoạn 0: Xóa Sạch Logic, Mô Tả & Bộ Nhớ Luồng Cũ (System-Wide Legacy Purge)

Trước khi viết bất kỳ dòng mã tính năng mới nào, tiến hành rà soát, dọn sạch và cập nhật lại toàn bộ tài liệu đặc tả, task list và ghi chú kiến trúc:

### 2.1. Cập nhật `tasks/CURRENT.md`
- Đưa `TASK-089 — Admin Deep Diff & Unified Change Review Engine, Button Workflow Modernization, and Academic Gradebook PDF System` lên đầu file làm task trọng tâm đang thực hiện.
- Tuyên bố rõ lệnh bãi bỏ vĩnh viễn (Permanent Purge):
  * **Bãi bỏ cơ chế so sánh 3 trường cục bộ**: Xóa bỏ tư duy chỉ so sánh `title`, `category`, `description`. Mọi so sánh khóa học bắt buộc bao phủ 100% thuộc tính.
  * **Bãi bỏ nhãn định danh mơ hồ "Thay đổi khác"**: Mọi yêu cầu thay đổi bắt buộc được phân loại rõ ràng thành 1 trong 3 nhóm chuẩn (Khóa học, Bài học, Khung chương trình) hoặc loại chuyên biệt (Môn tiên quyết).
  * **Bãi bỏ thao tác đơn phương không xác nhận**: Mọi hành vi duyệt (phê duyệt nhanh hoặc phê duyệt chi tiết) và từ chối bắt buộc phải qua popup xác nhận (`UI.confirm` / `UI.prompt`).
  * **Bãi bỏ thẻ `<a download>` trực tiếp không kiểm soát**: Cấm sử dụng thẻ `<a href="..." download>` cho tệp PDF bảo mật; bắt buộc tải qua JavaScript Blob Fetch với xử lý lỗi hiển thị toast trực quan.

### 2.2. Chuẩn hóa Hệ thống Tài liệu Đặc tả (`docs/`)
- Cập nhật `docs/features/admin.md` & `docs/system/PWD301_SYSTEM_SPECIFICATION/frontend/04_ADMIN_UI_FLOWS.md`:
  * Mô tả rõ luồng Thẩm định Sửa đổi 3 Nhóm trực quan (3-Category Diff Architecture).
  * Quy định rõ chuẩn nút thao tác: Hàng đợi `[Xem]` -> `[Duyệt]`; Chi tiết `[Từ chối]` (popup lý do $\ge$ 5 ký tự) & `[Phê duyệt]` (popup xác nhận).
- Cập nhật `docs/features/assessments.md` & `docs/system/PWD301_SYSTEM_SPECIFICATION/business/08_ASSESSMENT_ENGINE.md`:
  * Bổ sung đặc tả động cơ xuất Bảng điểm Khảo thí Học vụ PDF (Academic Gradebook Engine) cho cả Sinh viên (cá nhân) và Giảng viên/Admin (toàn lớp).

---

## 3. Giai đoạn 1: Backend - Động cơ Tuần tự hóa & So sánh Chi tiết (Granular Diff Engine)

### 3.1. Nâng cấp Tuần tự hóa Dữ liệu Yêu cầu Thay đổi (`src/pwd301/blueprints/admin/routes.py`)
- **Vấn đề cũ**: `admin_list_change_requests` chỉ trích xuất sơ sài 3 trường của khóa học. Khi `course_service.py` chỉ lưu các trường có thay đổi vào `proposed_payload_json`, dữ liệu trước và sau bị lệch, dẫn đến frontend gán giá trị mặc định giống hệt nhau.
- **Giải pháp mới**:
  1. Khi serialize `r.change_type == "COURSE_METADATA"` hoặc yêu cầu sửa môn học:
     - Trích xuất toàn bộ trạng thái hiện tại của Course: `title`, `slug`, `course_code`, `category`, `difficulty`, `summary`, `description`, `learning_objectives`, `target_audience`, `completion_requirements`, `capacity`, `storage_quota_bytes`, `thumbnail_file_asset_id`.
     - Phân tích `proposed_payload` so với `original_data`: Tạo sẵn cấu trúc `diff_metadata` gồm danh sách các trường bị thay đổi (`changed_fields`), trường thêm mới (`added_fields`), trường bị xóa (`removed_fields`) và trường giữ nguyên (`unchanged_fields`).
  2. Khi serialize `r.change_type == "LESSON_CONTENT"` hoặc `r.target_type == "LESSON"`:
     - Trích xuất toàn bộ bài học gốc (`orig`) và bài học đề xuất (`staged`): tiêu đề, tóm tắt, nội dung markdown, thời lượng, video URL, danh sách tài liệu đính kèm, mini-quiz và điểm đạt yêu cầu.
  3. Khi serialize `r.change_type == "COURSE_VERSION_CHANGESET"`:
     - Tích hợp kết quả sâu từ `get_course_changeset_diff(actor, r.id)` để trả về đầy đủ cây thay đổi giáo trình (bài học thêm, sửa, xóa, di chuyển).

### 3.2. Endpoint Diff Thống nhất: `GET /admin/change-requests/<id>/diff`
- Xây dựng endpoint chuẩn trả về JSON đồng nhất cho mọi loại yêu cầu:
  ```json
  {
    "success": true,
    "data": {
      "request_id": 12,
      "category": "COURSE_METADATA",
      "course_title": "Lập trình Web nâng cao",
      "original": { ... },
      "proposed": { ... },
      "changes": [
        {
          "field": "description",
          "label": "Mô tả khóa học",
          "old_value": "Mô tả cũ...",
          "new_value": "Mô tả mới...",
          "change_type": "MODIFIED"
        }
      ],
      "unchanged_count": 8
    }
  }
  ```

---

## 4. Giai đoạn 2: Frontend - Giao diện Thẩm định Sửa đổi 3 Phân loại (Visual Diff Viewer)

Thực hiện tại `frontend/assets/js/views/admin.js`:

### 4.1. Phân loại & Gắn huy hiệu Đúng chuẩn (Bãi bỏ "Thay đổi khác")
Thay thế toàn bộ logic phân loại cũ bằng bảng nhận diện chuẩn xác:
- `COURSE_METADATA` hoặc sửa thông tin môn $\rightarrow$ Huy hiệu Chàm: **Khóa học** (`bg-indigo-50 text-indigo-700`).
- `LESSON_CONTENT` hoặc sửa bài học $\rightarrow$ Huy hiệu Lam: **Bài học** (`bg-blue-50 text-blue-700`).
- `COURSE_VERSION_CHANGESET` $\rightarrow$ Huy hiệu Tím: **Khung giáo trình** (`bg-purple-50 text-purple-700`).
- `LESSON_STRUCTURE` & `action: DELETE` $\rightarrow$ Huy hiệu Đỏ: **Xóa bài học** (`bg-rose-50 text-rose-700`).
- `PREREQUISITE` $\rightarrow$ Huy hiệu Hổ phách: **Môn tiên quyết** (`bg-amber-50 text-amber-700`).
*Tuyệt đối không để rơi vào nhãn mơ hồ "Thay đổi khác".*

### 4.2. Giao diện So sánh Trực quan (Visual Diff Panel)
Trong trang chi tiết thẩm định `#admin/change-requests/review?id=...`:
1. **Phân loại 1: Thông tin Khóa học (Course Metadata)**:
   - Hiển thị danh sách các trường có thay đổi trước.
   - Trường thay đổi được gắn huy hiệu xanh lá `[ĐÃ SỬA]`.
   - Cột TRƯỚC (Hiện tại): Hiển thị giá trị cũ bằng chữ màu đỏ, gạch ngang nhẹ nhàng (`line-through text-rose-700 dark:text-rose-400 bg-rose-50/60 p-2 rounded-lg`).
   - Cột SAU (Đề xuất): Hiển thị giá trị mới bằng chữ màu xanh lục (`text-emerald-700 dark:text-emerald-400 bg-emerald-50/60 p-2 rounded-lg font-medium`).
   - Các trường không thay đổi: Mặc định được gập gọn trong khu vực `<details>` kèm dòng thông báo: *"8 trường giữ nguyên không thay đổi (Bấm để xem)"*, giúp Admin tập trung ngay vào những điểm khác biệt cốt lõi.
2. **Phân loại 2: Nội dung & Phương tiện Bài học (Lesson Content & Media)**:
   - So sánh Tiêu đề và Tóm tắt bài học với visual badge.
   - So sánh Nội dung Bài học (Markdown Diff): Thuật toán so khớp từng dòng/từ, đánh dấu nền xanh cho đoạn văn bản mới thêm vào và nền đỏ cho đoạn bị xóa bỏ.
   - So sánh Video bài giảng: Hiển thị URL cũ vs URL mới, thời lượng cũ vs thời lượng mới.
   - So sánh Tài liệu & Trắc nghiệm mini: Liệt kê rõ các tệp được đính kèm thêm hoặc bị gỡ bỏ.
3. **Phân loại 3: Khung giáo trình (Changeset Structure)**:
   - Render cây giáo trình với các huy hiệu nổi bật: Bài học mới tạo `[+] Mới`, Bài học sửa đổi `[~] Sửa`, Bài học đánh dấu xóa `[-] Xóa`.

---

## 5. Giai đoạn 3: Hiện đại hóa Nút Thao tác & Popup Xác nhận

### 5.1. Bảng Hàng đợi Xét duyệt (`#admin/governance?tab=courses`)
Tại cột `XÉT DUYỆT` của từng dòng yêu cầu:
- **Nút 1: `[Xem]`** (Đứng đầu):
  * Màu xanh dương / viền xám mềm mại (`bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-950/40 dark:text-blue-300`).
  * Icon kính lúp hoặc icon mở rộng (`visibility`).
  * Hành động: Điều hướng đến trang chi tiết `#/admin/change-requests/review?id=${r.id}`.
- **Nút 2: `[Duyệt]`** (Đứng sau):
  * Màu xanh lục (`bg-emerald-600 hover:bg-emerald-700 text-white`).
  * Icon tích hợp (`check`).
  * Hành động: Bấm vào lập tức bật **Popup xác nhận (`UI.confirm`)**:
    > *"Phê duyệt yêu cầu thay đổi? Bạn có chắc chắn muốn phê duyệt nhanh yêu cầu #[id] của khóa học [Tên khóa học] không?"*
  * Chỉ khi Admin ấn "Xác nhận" mới thực thi API gọi duyệt và cập nhật giao diện.

### 5.2. Trang Chi tiết Thẩm định (`#admin/change-requests/review?id=...`)
Tại thanh công cụ footer:
- **Đổi nút `"Từ chối yêu cầu"` $\rightarrow$ `[Từ chối]`**:
  * Nút đỏ viền nổi (`bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100`).
  * Khi bấm: Mở popup yêu cầu nhập lý do từ chối (tối thiểu 5 ký tự) qua `UI.prompt`.
  * Sau khi nhập xong lý do, hiển thị popup xác nhận cuối cùng (`UI.confirm`): *"Bạn có chắc chắn muốn từ chối yêu cầu #[id] với lý do đã nhập không?"*.
- **Đổi nút `"Phê duyệt & Áp dụng thay đổi"` $\rightarrow$ `[Phê duyệt]`**:
  * Nút xanh lục nổi bật (`bg-emerald-600 hover:bg-emerald-700 text-white`).
  * Khi bấm: Mở **Popup xác nhận (`UI.confirm`)**:
    > *"Xác nhận phê duyệt? Toàn bộ các thay đổi trong bản sửa đổi #[id] sẽ được áp dụng trực tiếp vào hệ thống đào tạo. Bạn có chắc chắn muốn tiếp tục?"*
  * Admin xác nhận $\rightarrow$ gửi API duyệt $\rightarrow$ toast thông báo thành công $\rightarrow$ điều hướng về lại hàng đợi.

---

## 6. Giai đoạn 4: Sửa Lỗi Tải PDF Bảng điểm Sinh viên & Chuẩn hóa Header

### 6.1. Backend (`src/pwd301/blueprints/student/routes.py`)
- Sửa hàm `attempt_result_pdf(attempt_id)`:
  * Khắc phục vấn đề mã hóa tên tệp Unicode trên Windows.
  * Thiết lập song song 2 định dạng `Content-Disposition`:
    - `filename="bang-diem.pdf"` (Fallback an toàn cho các trình duyệt hoặc proxy cũ).
    - `filename*=UTF-8''...` (Chuẩn RFC 5987 / RFC 6266 hỗ trợ đầy đủ tiếng Việt có dấu).
  * Kiểm soát quyền truy cập: Cho phép Sinh viên chính chủ, Giảng viên phụ trách môn và Admin đều có thể tải tệp mà không bị chặn 403.

### 6.2. Frontend (`frontend/assets/js/views/student.js`)
- Loại bỏ hành vi click trực tiếp của `<a href="..." download>`:
- Bổ sung trình xử lý JavaScript tải Blob an toàn (`downloadStudentResultPdf`):
  1. Khi người dùng bấm nút: Hiển thị trạng thái đang tải (spinner / disabled).
  2. Gửi request `fetch(resultPdfHref)` kèm Cookie / Authorization Header.
  3. Nếu server trả về lỗi (400, 403, 500): Đọc thông báo lỗi từ JSON và hiển thị `UI.showToast(errorMsg, 'error')`. Trình duyệt **hoàn toàn không tải về file `result.json` rác**.
  4. Nếu server trả về 200 OK: Chuyển dữ liệu sang `Blob`, tạo Object URL ảo, trích xuất tên file chính xác từ header và kích hoạt tải về máy.
  5. Hiển thị toast thông báo: *"Đã tải bảng điểm PDF thành công!"*.

---

## 7. Giai đoạn 5: Xây dựng Động cơ Xuất Bảng điểm Khảo thí Toàn lớp (Class Gradebook PDF)

### 7.1. Động cơ ReportLab Học vụ (`src/pwd301/services/result_pdf_service.py`)
Phát triển hàm `build_assessment_gradebook_pdf(gradebook_data: dict[str, Any]) -> bytes`:
- **Tiêu đề Học vụ Chuẩn mực (Official Academic Header)**:
  * Quốc hiệu / Bộ Giáo dục & Đào tạo / Học viện Trực tuyến PWD301.
  * Tên Khóa học, Mã khóa học, Tên bài thi / khảo thí, Ngày khảo thí.
  * Tên Giảng viên phụ trách môn.
- **Bảng Thống kê Tổng quan (Executive Summary)**:
  * Tổng số thí sinh dự thi | Số bài đã nộp hoàn tất.
  * Điểm trung bình môn | Điểm cao nhất | Điểm thấp nhất.
  * Tỷ lệ đạt (%) | Số lượng đạt / hỏng.
- **Bảng Danh sách Thí sinh & Điểm số Toàn diện**:
  * Các cột: `STT`, `Mã SV`, `Họ và tên`, `Thời gian nộp bài`, `Vi phạm giám sát` (số lần chuyển tab/blur cửa sổ), `Điểm số / 100`, `Kết quả` (ĐẠT / HỎNG).
  * Viền bảng thanh lịch, dòng xen kẽ (striped rows) dễ đọc.
- **Khu vực Chữ ký & Phê duyệt Học vụ (Committee Signatures)**:
  * Ngày tháng năm lập bảng điểm.
  * Chữ ký Cán bộ Chấm thi / Giảng viên.
  * Chữ ký Trưởng ban Khảo thí / Quản trị viên.

### 7.2. Endpoints Backend Cho Giảng viên & Admin
- Giảng viên: `GET /instructor/assessments/<assessment_id>/gradebook.pdf` (`src/pwd301/blueprints/instructor/routes.py`).
  * Xác thực quyền quản lý môn học của Giảng viên.
  * Tổng hợp toàn bộ danh sách thí sinh nộp bài và gọi `build_assessment_gradebook_pdf`.
- Quản trị viên: `GET /admin/assessments/<assessment_id>/gradebook.pdf` (`src/pwd301/blueprints/admin/routes.py`).
  * Xác thực quyền Admin (`COURSE_REVIEW` hoặc `ADMIN_PRIMARY`).

### 7.3. Giao diện Giảng viên & Admin (`frontend/assets/js/views/instructor.js`)
- Tại trang `#/instructor/courses/<cid>/assessments/<aid>/results` ("Bảng điểm & Kết quả Khảo thí Trắc nghiệm"):
  * Thêm nút hành động nổi bật ở thanh tiêu đề trang:
    `<button id="btn-export-gradebook-pdf" class="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-bold hover:bg-slate-50 flex items-center gap-1.5 shadow-2xs">`
    `<span class="material-symbols-outlined text-[16px] text-primary">picture_as_pdf</span>`
    `<span>Xuất bảng điểm PDF</span>`
    `</button>`
  * Bắt sự kiện click: Gọi `ApiClient.downloadAssessmentGradebookPdf(assessmentId)` với cơ chế tải Blob và toast tương tự bảng điểm sinh viên.

---

## 8. Kế hoạch Kiểm thử & Xác minh Thực nghiệm (Verification Matrix)

Tuân thủ Luật Sắt Xác minh Thực nghiệm (Anti-Hallucination Contract):
1. **Kiểm thử Đơn vị & Tích hợp (Pytest)**:
   - `tests/unit/test_result_pdf_service.py`: Kiểm thử tạo PDF bảng điểm sinh viên và PDF bảng điểm toàn lớp; xác minh font Unicode tiếng Việt không lỗi font; kiểm tra render bảng biểu và thống kê.
   - `tests/api/test_admin_change_requests_diff.py`: Kiểm thử serialization đầy đủ trước/sau của các loại yêu cầu thay đổi; kiểm thử endpoint `/admin/change-requests/<id>/diff`.
   - `tests/api/test_gradebook_pdf_endpoints.py`: Kiểm thử phân quyền truy cập endpoint PDF cho Giảng viên, Sinh viên và Admin; xác minh trả về HTTP 200 kèm đúng Content-Type `application/pdf`.
2. **Kiểm thử Giao diện & Trình duyệt Thực tế (DevTools / Live Test)**:
   - Truy cập `#admin/governance?tab=courses`: Xác nhận các nút trong bảng hiển thị đúng `[Xem]` (xanh dương, đứng trước) và `[Duyệt]` (xanh lục, đứng sau); bấm `[Duyệt]` hiện popup xác nhận.
   - Truy cập `#admin/change-requests/review?id=...`: Xác nhận các nút hiển thị `[Từ chối]` và `[Phê duyệt]`; bấm `[Phê duyệt]` hiện popup xác nhận; bấm `[Từ chối]` hiện popup nhập lý do $\ge$ 5 ký tự.
   - Xác nhận bảng so sánh Diff hiển thị rõ ràng các trường bị sửa, gạch đỏ giá trị cũ và bôi xanh giá trị mới; gập gọn các trường không đổi.
   - Kiểm tra nút "Xuất bảng điểm (PDF)" của Sinh viên: Tải về thành công file PDF chuẩn xác, không bị lỗi `result.json`.
   - Kiểm tra nút "Xuất bảng điểm PDF" của Giảng viên: Tải về thành công bảng điểm toàn lớp chuẩn học vụ.
3. **Kiểm tra Toàn vẹn Hệ thống**:
   - Chạy kiểm tra tĩnh và định dạng: `ruff check src tests`, `python -m py_compile ...`.
   - Chạy lệnh tổng kiểm tra xác minh dự án: `./scripts/verify.ps1`.

---

## 9. Danh mục Tệp tin Tác động Dự kiến

| Tệp tin | Phạm vi Thay đổi |
|---|---|
| `tasks/CURRENT.md` | Đăng ký TASK-089, xóa sạch logic cũ, tuyên bố bãi bỏ vĩnh viễn quy trình cũ |
| `docs/features/admin.md` | Cập nhật tài liệu đặc tả luồng duyệt và diff mới |
| `docs/features/courses.md` | Cập nhật tài liệu đặc tả quy trình sửa đổi khóa học |
| `docs/features/assessments.md` | Cập nhật đặc tả xuất bảng điểm PDF học vụ |
| `src/pwd301/services/result_pdf_service.py` | Bổ sung hàm xuất bảng điểm toàn lớp `build_assessment_gradebook_pdf` |
| `src/pwd301/blueprints/admin/routes.py` | Tuần tự hóa đầy đủ diff metadata, endpoint `/change-requests/<id>/diff`, endpoint gradebook PDF admin |
| `src/pwd301/blueprints/instructor/routes.py` | Endpoint xuất bảng điểm toàn lớp cho giảng viên |
| `src/pwd301/blueprints/student/routes.py` | Cập nhật headers tải PDF RFC 5987 / UTF-8 an toàn |
| `frontend/assets/js/api.js` | Thêm các phương thức tải PDF dạng Blob cho Sinh viên và Giảng viên |
| `frontend/assets/js/views/admin.js` | Đổi tên & thứ tự nút hàng đợi (`[Xem]`, `[Duyệt]`), đổi tên nút chi tiết (`[Từ chối]`, `[Phê duyệt]`), popup xác nhận, bảng diff 3 phân loại trực quan |
| `frontend/assets/js/views/instructor.js` | Thêm nút "Xuất bảng điểm PDF" và xử lý tải Blob trong trang kết quả bài thi |
| `frontend/assets/js/views/student.js` | Thay thế thẻ `<a>` tải PDF bằng trình xử lý JS Blob an toàn kèm bắt lỗi toast |
| `tests/unit/test_result_pdf_service.py` | Unit tests cho bảng điểm PDF cá nhân và toàn lớp |
| `tests/api/test_admin_change_requests_diff.py` | Integration tests cho hệ thống diff và nút thao tác |
