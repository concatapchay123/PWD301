# BÁO CÁO TOÀN BỘ LỖI HỆ THỐNG PWD301: BACKEND, FRONTEND & THAO TÁC NGHIỆP VỤ
**Chuyên đề:** Xem trước tài liệu kiểm duyệt, Cơ chế chặn tệp độc hại tại nguồn & Bỏ giới hạn sĩ số khóa học
**Thời gian lập báo cáo:** 03/10/2026, 19:38 (Múi giờ Asia/Ho_Chi_Minh)
**Môi trường kiểm tra thực nghiệm:** Google Chrome qua DevTools Protocol trên hệ thống thật (Docker container `pwd301_web`, `pwd301_db`, `pwd301_clamav`), HEAD hiện hành tại `E:\PWD301`.

---

## 1. TỔNG QUAN TÌNH TRẠNG VÀ PHÁT HIỆN THỰC NGHIỆM

Thông qua quá trình truy cập trực tiếp bằng công cụ Trình duyệt (`chrome-devtools-mcp`), tái hiện lỗi thực tế từ ảnh người dùng cung cấp và rà soát mã nguồn toàn diện giữa Frontend SPA (`frontend/assets/js/`) và Backend REST API (`src/pwd301/`), nhóm kiểm toán xác định **3 cụm lỗi nghiệp vụ nghiêm trọng** cùng chuỗi lỗi phái sinh:

1. **Lỗi 1 (P0 - Security & Usability): Quản trị viên không thể xem trước (Preview) tài liệu đã quét sạch - Trình duyệt báo `127.0.0.1 refused to connect`**
   - **Tái hiện thực tế:** Khi Admin nhấn nút "Xem trước" trên trang Thẩm định yêu cầu thay đổi (`#/admin/change-requests/review?id=40008`) đối với tệp `Chapter 5 – Database and ORM part 2.pdf`, modal mở ra nhưng `iframe` bên trong bị trắng xóa và Chrome báo lỗi kết nối từ chối (`127.0.0.1 refused to connect`).
   - **Bằng chứng Console Chrome:**
     ```text
     [error] Framing 'http://127.0.0.1:5000/' violates the following Content Security Policy directive: "frame-ancestors 'none'". The request has been blocked.
     ```
   - **Bằng chứng Network Header:** Endpoint `/student/files/c34156ce-8751-4c1b-8a07-2cfd66ad4fda/download?disposition=inline` trả về HTTP 200 (674,900 bytes PDF) nhưng mang kèm headers:
     ```http
     X-Frame-Options: DENY
     Content-Security-Policy: default-src 'self'; ... frame-ancestors 'none';
     ```

2. **Lỗi 2 (P0 - Security Architecture): Tệp tin độc hại / chưa an toàn không bị chặn khi Giảng viên tải lên, lọt vào giáo trình và bị gửi cho Admin duyệt**
   - **Tái hiện thực tế:** Trên trang duyệt khóa học `#/admin/courses/review?id=3e3214f9-1e6e-41c4-853d-7bcbc26119ec` (Khóa học "MayLaAI"), Bài 1 chứa 4 tệp đính kèm:
     - `570921738.pdf` · PDF · **Chưa an toàn** (`scan_status: "INFECTED"`, chữ ký `/JS` JavaScript độc hại).
     - `2210.07346v2.pdf` · PDF · **Đã kiểm tra** (`scan_status: "CLEAN"`).
     - `2405.14672v2.pdf` · PDF · **Chưa an toàn** (`scan_status: "INFECTED"`, chữ ký `/JS` JavaScript độc hại).
     - `2405.13080v1.pdf` · PDF · **Đã kiểm tra** (`scan_status: "CLEAN"`).
   - **Hậu quả:** Giảng viên tải tệp nhiễm mã độc lên thành công (nhận HTTP 201), hệ thống tự động gắn tệp độc vào bài học (`LessonResource`), cho phép Giảng viên bấm "Gửi duyệt khóa học" (`SUBMITTED_FOR_REVIEW`) mà không hề có bất kỳ rào chắn nào ngăn chặn hoặc cảnh báo cho giảng viên.
   - **Thiếu sót UI Admin:** Tại trang Duyệt khóa học (`renderCourseReviewPage`), danh sách tài liệu đính kèm chỉ in ra một thẻ `<p>` dạng text thô, hoàn toàn không có nút "Xem trước" hay link tải đối với cả những tệp an toàn.

3. **Lỗi 3 (P1 - Business Constraint): Còn tồn tại ràng buộc Sĩ số tối đa (Capacity) giới hạn số lượng sinh viên đăng ký**
   - **Hiện trạng:**
     - Tại giao diện Giảng viên (`frontend/assets/js/views/instructor.js:3741`): Vẫn còn trường `<input name="capacity">` với nhãn "Giới hạn sĩ số tối đa (Capacity)".
     - Tại backend `enrollment_service.py` (dòng 320 và 612): Vẫn thực hiện kiểm tra `active_count >= locked_course.capacity` và ném lỗi `EnrollmentCapacityExceededError` khiến sinh viên không thể đăng ký khi khóa học đạt sĩ số.
     - Tại `src/pwd301/blueprints/student/routes.py` (dòng 1627): Vẫn tính toán `is_full = True` và khóa nút đăng ký.

---

## 2. BẢNG LIỆT KÊ TOÀN BỘ DANH MỤC LỖI CHI TIẾT (BACKEND & FRONTEND)

| Mã lỗi | Phân vùng | File & Vị trí | Mô tả chi tiết lỗi | Nguyên nhân gốc rễ (Root Cause) | Mức độ |
|---|---|---|---|---|---|
| **BUG-PREV-01** | Backend Header | `src/pwd301/__init__.py:750-785` | Mọi tệp tin khi nhúng xem trước qua `iframe` đều bị trình duyệt chặn với lỗi `127.0.0.1 refused to connect` | `after_request` chỉ đặt `allows_same_origin_frame = True` cho các route `/frontend/` hoặc `admin_download_application_evidence`. Các route xem tài liệu học vụ `/student/files/<id>/download?disposition=inline` bị gán cứng `X-Frame-Options: DENY` và `frame-ancestors 'none'`. | **P0 (Critical)** |
| **BUG-PREV-02** | Backend Admin API | `src/pwd301/blueprints/admin/routes.py:165-174` | Endpoint `GET /admin/courses/<id>` không trả về `file_url`, `asset_id`, `mime_type` cho tài liệu bài học | `admin_course_detail` chỉ trả về dict gồm 3 trường `label`, `resource_type`, `scan_status`, thiếu hoàn toàn siêu dữ liệu để frontend tạo nút xem trước hoặc tải về. | **P0 (Critical)** |
| **BUG-PREV-03** | Frontend Admin UI | `frontend/assets/js/views/admin.js:3004` | Trang xem xét duyệt khóa học không cho Admin xem trước tài liệu đã quét sạch | Mã nguồn chỉ render thẻ `<p class="text-slate-600...">${resource.label} ...</p>` dạng văn bản tĩnh, không có component thẻ file, không có nút "Xem trước" và không kết nối modal `AdminView.openDocumentPreviewModal`. | **P0 (Critical)** |
| **BUG-SCAN-01** | Backend Upload | `src/pwd301/blueprints/instructor/routes.py:1477-1510` & `1680-1715` | Giảng viên tải lên tệp nhiễm mã độc hoặc tệp lỗi quét nhưng backend vẫn gắn vào bài học và trả về HTTP 201 | `attach_lesson_resource_route` và `upload_course_file_route` sau khi gọi `store_file_stream` không kiểm tra `asset.virus_scan_status`. Dù tệp bị scanner gắn cờ `REJECTED`/`INFECTED`, tệp vẫn được gắn vào `LessonResource`. | **P0 (Security)** |
| **BUG-SCAN-02** | Backend Lifecycle | `src/pwd301/services/course_service.py:870-940` | Khóa học chứa tệp mã độc / chưa an toàn vẫn cho phép chuyển trạng thái `SUBMITTED_FOR_REVIEW` | Hàm `change_course_status` không kiểm tra tính an toàn của các tài liệu đính kèm trước khi chuyển sang `SUBMITTED_FOR_REVIEW`, làm lọt mã độc lên cấp Admin thẩm định. | **P0 (Security)** |
| **BUG-SCAN-03** | Backend ChangeReq | `src/pwd301/blueprints/instructor/routes.py:1489-1499` | Tệp nhiễm mã độc tải lên bài học đã xuất bản được đưa thẳng vào Change Request (`queue_lesson_resource_change`) | Không kiểm tra `asset.virus_scan_status == "CLEAN"` trước khi xếp hàng duyệt thay đổi tài liệu. | **P0 (Security)** |
| **BUG-SCAN-04** | Frontend Feedback | `frontend/assets/js/views/instructor.js:6675-6715` | Giảng viên không nhận được cảnh báo trực quan khi tệp tin tải lên bị nhiễm độc / cách ly | Frontend bỏ qua mã lỗi chi tiết khi backend trả về asset ở trạng thái `PENDING`/`INFECTED`, hiển thị thông báo thành công ảo "Đã đính kèm tài liệu". | **P1 (High)** |
| **BUG-CAP-01** | Frontend Instructor | `frontend/assets/js/views/instructor.js:3741-3746` & `3870-3893` | Giao diện thiết lập khóa học vẫn có trường nhập "Giới hạn sỉ số tối đa (Capacity)" | Giao diện chưa được cập nhật theo yêu cầu nghiệp vụ mới: sĩ số tối đa là không giới hạn. | **P1 (High)** |
| **BUG-CAP-02** | Backend Service | `src/pwd301/services/enrollment_service.py:320-333` & `612-625` | Ghi danh sinh viên bị chặn với lỗi `EnrollmentCapacityExceededError` khi đạt sĩ số | Vẫn duy trì logic kiểm tra `active_count >= locked_course.capacity` khi đăng ký mới và đăng ký lại khóa học. | **P1 (High)** |
| **BUG-CAP-03** | Backend Student API | `src/pwd301/blueprints/student/routes.py:1627` | Sinh viên thấy khóa học bị gắn cờ "Đã đầy lớp" (`is_full = True`) | Logic tính toán `is_full` dựa trên `course.capacity` cũ, ngăn sinh viên bấm nút tham gia học. | **P1 (High)** |
| **BUG-CAP-04** | Frontend Student UI | `frontend/assets/js/views/student.js:950-1005` | Trang chi tiết khóa học sinh viên hiển thị số lượng sĩ số giới hạn | Hiển thị chuỗi dạng "X sinh viên" thay vì hiển thị rõ "Không giới hạn". | **P2 (Medium)** |
| **BUG-SEC-FAIL** | Admin UI Safety | `frontend/assets/js/views/admin.js:3004` | Thiếu cơ chế khóa xem trước / tải về Fail-Closed đối với tệp nhiễm độc nếu lọt vào Admin | Không hiển thị nhãn cảnh báo đỏ và không vô hiệu hóa thao tác tải về đối với tệp có `scan_status != 'CLEAN'`. | **P1 (Security)** |

---

## 3. TỔNG HỢP NGUYÊN NHÂN GỐC RỄ (ROOT CAUSE SYNTHESIS)

1. **Về lỗi Preview Admin:**
   Chính sách bảo mật HTTP Headers (CSP và X-Frame-Options) được thiết lập theo cơ chế "chặn toàn bộ" (Fail-Closed) nhưng lại thiếu ngoại lệ cho chính các tệp tin học vụ nội bộ khi được tải với tham số `disposition=inline`. Do đó, khi trình duyệt mở thẻ `iframe` nhúng liên kết tải tệp cùng nguồn (Same-Origin), CSP `frame-ancestors 'none'` đã cưỡng chế chặn đứng kết nối.

2. **Về lỗi Tệp độc hại lọt vào thẩm định:**
   Có sự ngắt quãng giữa tầng Dịch vụ lưu trữ (`file_service.py`) và tầng Điều hướng (`routes.py`):
   - `store_file_stream` phát hiện mã độc chính xác qua bộ lọc `BuiltinHeuristicScanner` (nhận diện marker `/JS` trong PDF), cách ly tệp vào `quarantine/infected/` và tạo bản ghi `FileRevision` với trạng thái `REJECTED`.
   - Tuy nhiên, hàm này vẫn trả về đối tượng `FileAsset` (với `status="PENDING"`).
   - Tầng route gọi hàm này lại không kiểm tra trạng thái an toàn của `asset`, tiếp tục gọi `attach_resource_to_lesson` để liên kết tệp độc với bài học và trả về HTTP 201 cho giảng viên.
   - Khi giảng viên nộp khóa học duyệt, tầng `course_service.py` thiếu bước thẩm định chất lượng an toàn tệp (Pre-flight validation) nên khóa học chứa mã độc được chuyển thẳng sang Admin.

3. **Về ràng buộc Sĩ số tối đa:**
   Dự án vẫn duy trì quy tắc nghiệp vụ cũ từ tài liệu ban đầu về quản lý giới hạn sĩ số (ADR-002, CheckConstraint `ck_courses_3`, và kiểm tra dung lượng lớp học). Yêu cầu kinh doanh mới là **"sĩ số tối đa là không giới hạn"** cần được đồng bộ hóa xuyên suốt từ UI nhập liệu của giảng viên, dịch vụ ghi danh sinh viên, đến API thông tin khóa học.
