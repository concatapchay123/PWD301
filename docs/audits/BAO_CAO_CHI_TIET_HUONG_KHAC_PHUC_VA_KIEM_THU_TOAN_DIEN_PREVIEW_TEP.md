# BÁO CÁO CHI TIẾT HƯỚNG KHẮC PHỤC, XỬ LÝ VÀ QUY TRÌNH KIỂM THỬ TOÀN DIỆN
**Chuyên đề:** Kiến trúc Bảo vệ Tài liệu Học vụ, Xem trước Inline An toàn & Tự do Ghi danh Khóa học
**Mục tiêu:** Khắc phục triệt để lỗi từ chối kết nối Preview, chặn đứng tệp độc hại tại nguồn tải lên, loại bỏ rào cản sĩ số tối đa; bảo đảm tính toàn vẹn hệ thống không gây lỗi hồi quy (zero-regression).

---

## 1. NGUYÊN TẮC THIẾT KẾ & BẤT BIẾN NGHIỆP VỤ BẮT BUỘC (INVARIANTS)

Để đảm bảo việc sửa chữa "không sửa chỗ này làm hư chỗ kia", giải pháp phải tuân thủ nghiêm ngặt các bất biến nền tảng:
1. **Bất biến Headless REST API:** Không sinh mã HTML/Jinja server-side; toàn bộ trao đổi dữ liệu duy trì phong bì JSON chuẩn `{ "success": bool, "data": ..., "error": ... }`.
2. **Bất biến An toàn Kiểu Đóng (Fail-Closed Security):**
   - Mọi tệp tin có trạng thái quét khác `CLEAN` (`PENDING`, `QUARANTINED`, `REJECTED`, `INFECTED`, `BLOCKED`) tuyệt đối không thể xem trước, không thể tải về, và không được phép đưa vào danh sách thẩm định của Admin.
   - Chặn ngay tại thời điểm Giảng viên gửi request tải lên (`POST /courses/.../resources`). Nếu tệp không sạch, từ chối tạo liên kết và phản hồi lỗi HTTP 400/422 ngay lập tức kèm thông báo lý do chi tiết.
3. **Bất biến Xem trước Nội bộ (Same-Origin Inline Preview):**
   - Cho phép hiển thị tài liệu học vụ sạch trong thẻ `iframe` của giao diện quản trị PWD301 bằng cách thiết lập `X-Frame-Options: SAMEORIGIN` và `frame-ancestors 'self'` khi request có `disposition=inline` hoặc tham số `preview=1`.
   - Vẫn duy trì chặn đứng việc nhúng trang từ các tên miền ngoài độc hại.
4. **Bất biến Sĩ số Không giới hạn (Unlimited Capacity):**
   - Không áp đặt bất kỳ ngưỡng trần số lượng sinh viên cho khóa học.
   - Loại bỏ kiểm tra vượt sĩ số trong `enrollment_service.py` để quy trình ghi danh luôn thông suốt.

---

## 2. HƯỚNG ĐI VÀ PHƯƠNG ÁN XỬ LÝ KỸ THUẬT CHI TIẾT

### 2.1. Khắc phục Lỗi Preview Tài liệu (`127.0.0.1 refused to connect`)

#### A. Backend Header Configuration (`src/pwd301/__init__.py`)
- **Vấn đề:** Hàm hook `after_request` chỉ mở `SAMEORIGIN` cho route bắt đầu bằng `/frontend/` hoặc `admin_download_application_evidence`. Khi iframe gọi `/student/files/<id>/download?disposition=inline`, header bị gán `DENY` và `frame-ancestors 'none'`.
- **Giải pháp:** Bổ sung điều kiện nhận diện luồng xem trước tài liệu nội bộ:
  ```python
  is_file_inline_preview = (
      request.args.get("disposition", "").lower() == "inline"
      or request.args.get("preview", "0").lower() in ("1", "true", "yes")
  ) and (
      request.path.startswith(("/student/files/", "/student/courses/", "/api/files/", "/instructor/files/", "/admin/files/"))
  )
  allows_same_origin_frame = is_frontend or is_application_evidence_preview or is_file_inline_preview
  ```
- **Kết quả:** Trình duyệt nhận được `X-Frame-Options: SAMEORIGIN` và `Content-Security-Policy: ... frame-ancestors 'self';`, cho phép hiển thị PDF, ảnh và văn bản trực tiếp trong modal iframe mượt mà.

#### B. Bổ sung Siêu dữ liệu API Thẩm định Khóa học (`src/pwd301/blueprints/admin/routes.py`)
- **Vấn đề:** Hàm `admin_course_detail` (`GET /admin/courses/<id>`) không cung cấp `file_url`, `asset_id`, `filename`, `mime_type` của tài liệu đính kèm.
- **Giải pháp:** Cập nhật serialization của danh sách tài liệu trong từng bài học:
  ```python
  "resources": [
      {
          "resource_id": resource.id,
          "asset_id": str(resource.file_asset.public_id),
          "label": resource.label or resource.file_asset.display_name,
          "filename": resource.file_asset.original_filename or resource.file_asset.display_name,
          "mime_type": resource.file_asset.mime_type or "application/octet-stream",
          "file_url": f"/student/files/{resource.file_asset.public_id}/download?disposition=inline",
          "download_url": f"/student/files/{resource.file_asset.public_id}/download",
          "resource_type": resource.resource_type,
          "scan_status": resource.file_asset.virus_scan_status,
          "is_clean": resource.file_asset.virus_scan_status == "CLEAN",
          "is_video": resource.file_asset.is_video,
      }
      for resource in item.resources
      if resource.file_asset is not None
  ]
  ```

#### C. Thiết kế Giao diện Thẩm định Tài liệu trong Course Review (`frontend/assets/js/views/admin.js`)
- **Vấn đề:** Giao diện chỉ in dòng text mộc `<p>` ghi trạng thái `Chưa an toàn` hoặc `Đã kiểm tra`, không có tương tác.
- **Giải pháp:** Xây dựng thẻ tài liệu tiêu chuẩn:
  - Nếu tệp **Đã kiểm tra an toàn** (`is_clean == true`):
    - Huy hiệu xanh lá `Đã kiểm tra an toàn`.
    - Nút `Xem trước` (Icon mắt) kích hoạt `AdminView.openDocumentPreviewModal(resource.filename, resource.file_url, resource.mime_type)`.
    - Nút `Tải về` tải trực tiếp tệp tin gốc.
  - Nếu tệp **Chưa an toàn / Đã cách ly** (`is_clean == false`):
    - Huy hiệu đỏ `Chưa an toàn / Đã cách ly`.
    - Nút xem trước bị vô hiệu hóa kèm nhãn cảnh báo: *"Tệp không an toàn - Bị khóa theo nguyên tắc Fail-Closed"*.

---

### 2.2. Chặn Tệp Độc hại Tại Nguồn & Cảnh báo Giảng viên Ngay Lập Tức

#### A. Chặn Tải lên tại Backend Endpoint (`src/pwd301/blueprints/instructor/routes.py`)
- **Vị trí sửa:** `attach_lesson_resource_route` và `upload_course_file_route`.
- **Cơ chế xử lý:**
  Sau khi gọi `asset = store_file_stream(...)`, kiểm tra ngay lập tức:
  ```python
  if asset.virus_scan_status != "CLEAN":
      clean_name = asset.original_filename or asset.display_name or "Tệp tin"
      # Hủy bỏ liên kết nếu có và xóa phiên làm việc nháp
      if asset.virus_scan_status == "INFECTED":
          raise FileInfectedError(
              f"Tệp '{clean_name}' bị từ chối do phát hiện mã độc hoặc cấu trúc không an toàn. "
              "Hệ thống đã cách ly tệp để bảo vệ an toàn hệ thống."
          )
      else:
          raise FileSecurityQuarantineError(
              f"Tệp '{clean_name}' chưa vượt qua kiểm tra an ninh (trạng thái: {asset.virus_scan_status}). "
              "Không thể đính kèm vào bài giảng."
          )
  ```
- **Kết quả:** Không bao giờ tạo `LessonResource` cho tệp không an toàn. Giảng viên nhận ngay phản hồi lỗi HTTP 400/422 với thông báo tiếng Việt rõ ràng.

#### B. Van an toàn khi Giảng viên Gửi duyệt Khóa học (`src/pwd301/services/course_service.py`)
- **Vị trí sửa:** Hàm `change_course_status` khi `target_status == "SUBMITTED_FOR_REVIEW"`.
- **Cơ chế Pre-flight Check:**
  Duyệt toàn bộ các bài học thuộc khóa học:
  ```python
  if target_status == "SUBMITTED_FOR_REVIEW":
      for les in course.lessons:
          if getattr(les, "deleted_at", None) is None:
              for res in les.resources:
                  if res.file_asset and res.file_asset.virus_scan_status != "CLEAN":
                      raise CourseValidationError(
                          f"Không thể gửi duyệt khóa học. Bài học '{les.title}' chứa tệp đính kèm "
                          f"chưa an toàn hoặc đã bị cách ly ('{res.label or res.file_asset.display_name}'). "
                          "Vui lòng gỡ bỏ tệp này trước khi gửi duyệt."
                      )
  ```
- **Kết quả:** Đảm bảo 100% không một khóa học nào có thể lọt sang tay Admin nếu còn chứa tệp tin nghi ngờ độc hại.

#### C. Cảnh báo Thời gian Thực trên Frontend Giảng viên (`frontend/assets/js/views/instructor.js`)
- Khi hàm `uploadDocuments` hoặc `attachLessonResource` bắt được lỗi từ server (mã `FILE_INFECTED` hoặc `FILE_QUARANTINED`):
  - Hiển thị Toast cảnh báo màu đỏ đậm.
  - Loại bỏ ngay placeholder đang tải, không đưa tệp hỏng vào danh sách tài liệu hiển thị của Studio.

---

### 2.3. Loại Bỏ Sĩ Số Tối Đa Khóa Học (Unlimited Capacity)

#### A. Frontend Giảng viên (`frontend/assets/js/views/instructor.js`)
- Xóa bỏ ô nhập `<input name="capacity">`.
- Thay thế bằng thẻ thông tin trực quan:
  ```html
  <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex items-center justify-between">
    <div>
      <div class="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Sĩ số học viên</div>
      <div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Sĩ số tối đa: <strong>Không giới hạn</strong> (học viên được tự do ghi danh).</div>
    </div>
    <span class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300">Không giới hạn</span>
  </div>
  ```
- Khi submit form tạo/sửa khóa học: luôn gán `capacity: null`.

#### B. Backend Enrollment Service (`src/pwd301/services/enrollment_service.py`)
- Tại hàm `enroll_student_in_course` (dòng 320) và `reenroll_student_in_course` (dòng 612):
  - Xóa bỏ/vô hiệu hóa logic kiểm tra `active_count >= locked_course.capacity`.
  - Không ném `EnrollmentCapacityExceededError`.

#### C. Backend Student Route & View (`src/pwd301/blueprints/student/routes.py` & `student.js`)
- Gán cố định `is_full = False`.
- Trang chi tiết khóa học của học viên luôn hiển thị: *"Sĩ số: Không giới hạn"*.

---

## 3. KẾ HOẠCH KIỂM THỬ TOÀN DIỆN (COMPREHENSIVE VERIFICATION MATRIX)

| STT | Kịch bản kiểm thử (Test Scenario) | Phương thức thực hiện | Kết quả kỳ vọng |
|---|---|---|---|
| **TC-01** | Xem trước PDF trên trang duyệt yêu cầu thay đổi (`#/admin/change-requests/review?id=40008`) | Mở Chrome thật, click nút "Xem trước" tệp `Chapter 5 – Database and ORM part 2.pdf` | Modal mở ra, PDF hiển thị hoàn hảo trong iframe, console 0 lỗi CSP, không bị từ chối kết nối. |
| **TC-02** | Xem trước tài liệu trên trang duyệt khóa học (`#/admin/courses/review?id=...`) | Mở Chrome thật, duyệt bài học có tệp sạch, bấm nút "Xem trước" | Modal xem trước mở mượt mà, nội dung PDF tải trọn vẹn, có nút tải tệp về máy. |
| **TC-03** | Giảng viên tải lên tệp EICAR hoặc tệp PDF chứa script `/JS` độc hại | Gửi request tải lên tệp độc hại qua Studio Giảng viên | Backend chặn với mã lỗi `FILE_INFECTED`, tệp bị đưa vào `quarantine/infected/`, không gắn vào Lesson, giao diện hiện thông báo cảnh báo đỏ. |
| **TC-04** | Giảng viên cố tình gửi duyệt khóa học có tệp độc hại | Gọi `POST /courses/<id>/submit-review` khi còn tệp `status != CLEAN` | Backend chặn với lỗi `CourseValidationError` kèm thông báo bài học và tệp vi phạm. |
| **TC-05** | Kiểm tra thiết lập khóa học của Giảng viên | Mở tab Cài đặt khóa học trong Studio | Không còn trường nhập số sĩ số; hiển thị huy hiệu "Không giới hạn". Khóa học lưu với `capacity = None`. |
| **TC-06** | Sinh viên ghi danh vào khóa học | Gọi ghi danh sinh viên qua API và UI | Ghi danh thành công 100%, không bị lỗi `CAPACITY_EXCEEDED` bất kể số lượng sinh viên hiện tại. |
| **TC-07** | Kiểm tra hồi quy toàn bộ hệ sinh thái (Regression Test) | Chạy test suite `pytest` và script xác minh | Toàn bộ các bài kiểm tra bảo mật, phân quyền RBAC và tải file đều vượt qua. |
