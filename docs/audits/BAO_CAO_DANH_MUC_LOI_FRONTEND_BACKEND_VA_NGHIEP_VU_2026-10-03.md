# BÁO CÁO TOÀN DIỆN DANH MỤC LỖI HỆ THỐNG PWD301: BACKEND, FRONTEND VÀ THAO TÁC NGHIỆP VỤ

**Thời điểm kiểm tra & ghi nhận:** 03/10/2026  
**Môi trường:** Docker (Flask Web `pwd301_web`, Microsoft SQL Server `pwd301_db`, ClamAV `pwd301_clamav`)  
**Công cụ xác minh thực nghiệm:** `/browser` (`chrome-devtools-mcp`), SQL Server `sqlcmd`, Node.js Test Runner  
**Phạm vi:** 11 lỗi và yêu cầu nghiệp vụ do Chủ dự án chỉ đạo  

---

## 1. TỔNG QUAN PHÂN TÍCH HỆ THỐNG

Hệ thống PWD301 hoạt động theo kiến trúc **Pure Headless Backend & REST API**, toàn bộ dữ liệu phản hồi được đóng gói chuẩn JSON envelope `{"success": true/false, "data": ..., "error": ...}`. Phía Client là Single Page Application (SPA) viết bằng Vanilla JavaScript, điều hướng qua HashRouter và đồng bộ dữ liệu bằng `ApiClient`.

Qua khảo sát và kiểm thử thực nghiệm trên giao diện trình duyệt trực tiếp, 11 vấn đề được phân thành 4 nhóm nghiệp vụ chính:
1. **Soạn thảo giáo trình & Quản lý bài giảng Giảng viên (Instructor)**: Lỗi 1, 2, 6.
2. **Vòng đời Khóa học, Kiểm soát Thay đổi & Đóng băng Phê duyệt (Course Lifecycle & Changeset)**: Lỗi 3, 4, 5.
3. **Không gian Học tập & Ghi nhận Tiến trình Sinh viên (Student Console)**: Lỗi 7.
4. **Quản trị Thông báo & Phê duyệt Yêu cầu Thay đổi (Admin & Notifications)**: Lỗi 8, 9, 10, 11.

---

## 2. BẢNG TỔNG HỢP CHI TIẾT 11 LỖI (BACKEND & FRONTEND)

| Mã lỗi | Mô tả Hiện tượng | Phân loại | Tệp tin liên quan | Nguyên nhân kỹ thuật gốc rễ (Root Cause) |
|---|---|---|---|---|
| **BUG-01** | Tạo chương ("Tạo chương") thành công nhưng không hiển thị ngay trên web, bắt buộc phải tải lại trang (F5). | Frontend | `frontend/assets/js/views/instructor.js` | Hàm `InstructorView.renderCourseManage` gọi hàm vẽ lại không truyền đúng viewport cha khiến DOM không được gắn lại tự động. Trong Studio (`handleAddNewLesson`), tạo chương xong không gọi `renderChildNavigator()` và `updateHeaderUnitTitle()`. |
| **BUG-02** | Tạo bài học/chương: Nhập tên xong ấn phím "Enter" thì bị xuống hàng thay vì tạo ngay; Thiếu giới hạn độ dài 200 ký tự. | Frontend | `frontend/assets/js/ui.js` | `UI.prompt` ban đầu render thẻ `<textarea rows="3">`, không lắng nghe sự kiện phím `Enter` khiến phím này chèn ký tự `\n`; Không có thuộc tính `maxlength="200"`. |
| **BUG-03** | Khóa học chưa xuất bản (`DRAFT`): Mọi thay đổi bài học/chương phải gom chung vào 1 lần gửi duyệt xuất bản, không được hiện banner "Bản nháp cập nhật đang soạn". | Backend & Frontend | `src/pwd301/services/lesson_service.py`, `frontend/assets/js/views/instructor.js` | `lesson_service.py` (`get_course_changeset_status`) vẫn tính toán changeset cho khóa học `DRAFT`, trả về `has_changes: true` làm kích hoạt banner cập nhật không mong muốn. |
| **BUG-04** | Khóa học đang gửi duyệt (`SUBMITTED_FOR_REVIEW`): Cấm tuyệt đối mọi hành vi sửa đổi khóa học, bài học, tài nguyên (Fail-Closed Freeze). | Backend & Frontend | `src/pwd301/blueprints/instructor/routes.py`, `src/pwd301/services/lesson_service.py`, `frontend/assets/js/views/instructor.js` | Tuyến tải tệp `upload_course_file_route` thiếu kiểm tra trạng thái khóa học khi đang gửi duyệt; Frontend chưa vô hiệu hóa nút tải ảnh bìa khi `isFrozen = true`. |
| **BUG-05** | Đổi văn bản nhãn giao diện từ `"Bản nháp cập nhật đang soạn"` thành `"Nội dung cập nhật"`. | Frontend | `frontend/assets/js/views/instructor.js` | Chuỗi văn bản cứng tại dòng 937 chưa được cập nhật theo từ vựng nghiệp vụ chuẩn của dự án. |
| **BUG-06** | Tải ảnh bìa khóa học tự cố định hình ảnh, thiếu tính năng kéo thả, zoom và chọn vùng hiển thị chuẩn tỷ lệ 16:9. | Frontend | `frontend/assets/js/ui.js`, `frontend/assets/js/views/instructor.js` | Thẻ input file gửi trực tiếp tệp ảnh gốc lên server mà không có modal tương tác canvas để người dùng crop và căn góc ảnh 16:9. |
| **BUG-07** | Sinh viên học xong bài không tự động cập nhật tiến trình và không tự đánh dấu tích hoàn thành trên sidebar (phải reload lại trang). | Frontend | `frontend/assets/js/views/student.js` | Hàm `setLessonCompleted()` chỉ cập nhật biến `activeItem.isCompleted` nhưng không cập nhật `_isCompleted` trong mảng `modules`, không kích hoạt vẽ lại accordion và không tính lại phần trăm thanh tiến độ trên header. |
| **BUG-08** | Thiếu chức năng cho phép các role người dùng xóa thông báo (yêu cầu xóa mềm trong cơ sở dữ liệu). | Fullstack (DB, Backend, Frontend) | `src/pwd301/models/notification_audit.py`, `src/pwd301/services/notification_service.py`, `src/pwd301/blueprints/auth/routes.py`, `frontend/assets/js/router.js` | Bảng `notifications` trong SQL Server chưa có cột `deleted_at`; Backend thiếu API `DELETE /notifications/<id>` với điều kiện lọc `deleted_at IS NULL`; Giao diện dropdown thiếu nút xóa từng thông báo. |
| **BUG-09** | Yêu cầu sửa hoặc xóa bài giảng/khóa học khi Admin duyệt xong không tự biến mất khỏi danh sách chờ duyệt. | Frontend | `frontend/assets/js/views/admin.js` | Danh sách yêu cầu thay đổi trong bảng chờ duyệt thiếu nút thao tác phê duyệt trực tiếp; Trang diff review không reset trạng thái bộ lọc khiến mục đã duyệt vẫn nằm trong hàng chờ. |
| **BUG-10** | Tab "Tất cả" sau vài giây tự động bị nháy loading và nhảy ngược về tab "Chờ duyệt". | Frontend | `frontend/assets/js/views/admin.js`, `frontend/assets/js/router.js` | Hàm `fetchAdminPendingCounts` hoặc polling định kỳ kích hoạt re-render toàn bộ tab và ép bộ lọc `_activeCrFilter` về giá trị mặc định `'PENDING'`. |
| **BUG-11** | Toàn bộ giao diện quản trị bị nháy load lại rất khó chịu sau mỗi vài giây. | Frontend | `frontend/assets/js/router.js` | Polling thông báo ngầm (`refreshNotificationBadge`) gọi hàm re-render giao diện ngoài ý muốn khi không có thay đổi số lượng badge thực tế. |

---

## 3. PHÂN TÍCH RỦI RO & BẪY HỒI QUY NGHIỆP VỤ

1. **Rủi ro phá vỡ tính khép kín của CSDL (Database Schema Drift)**:
   - Thêm cột `deleted_at` vào bảng `notifications` bắt buộc dùng `DATETIME2(3)` cho phép NULL để không làm mất dữ liệu lịch sử hoặc vi phạm ràng buộc NOT NULL hiện có.
2. **Rủi ro gian lận khi khóa học đang xét duyệt (Audit Invariant Violation)**:
   - Giảng viên gửi duyệt khóa học nhưng âm thầm thay đổi nội dung bài giảng, thêm/bớt tài liệu hoặc thay đổi bài kiểm tra. Nếu không khóa ở cấp dịch vụ backend (Fail-Closed), dữ liệu được duyệt sẽ không khớp với dữ liệu thực tế giảng dạy.
3. **Rủi ro bất đồng bộ trạng thái giao diện (UI State Desynchronization)**:
   - Sử dụng `window.location.reload()` để giải quyết vấn đề hiển thị là phản mẫu (anti-pattern) làm mất ngữ cảnh người dùng, gián đoạn video đang phát và gây quá tải HTTP request.
4. **Rủi ro tự phê duyệt quyền hạn (Self-Review Authorization Bypass)**:
   - Quản trị viên không được phép tự duyệt yêu cầu thay đổi do chính mình tạo ra (`requested_by_user_id == actor.id`). Hệ thống phải bảo toàn kiểm tra an ninh nghiêm ngặt này.
