# MA TRẬN KIỂM THỬ THÔNG BÁO TOÀN DIỆN (NOTIFICATION TEST MATRIX)
**Mã tài liệu:** `06_NOTIFICATION_TEST_MATRIX.md`  
**Dự án:** PWD301 LMS & Assessment Platform  
**Phương pháp kiểm thử:** Kiểm thử Đa tầng (Multi-Tier Testing) gồm Automated Unit Tests, API Integration Tests và Real-World Browser Verification (Chrome DevTools MCP).  
**Tỷ lệ Đạt:** 100% (25/25 kịch bản kiểm thử PASS).

---

## 1. MA TRẬN KIỂM THỬ CHI TIẾT THEO VAI TRÒ & NGHIỆP VỤ

| Mã Test Case | Vai trò | Màn hình / Phân hệ | Loại Kịch bản | Thao tác Kiểm thử Thực tế | Thông báo & Hành vi Kỳ vọng | Kết quả Thực tế Quan sát | Trạng thái |
| :--- | :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| **TC-AUTH-01** | `GUEST` | `#/auth` (Đăng nhập) | Validation | Bấm Đăng nhập khi để trống cả email và mật khẩu | Toast Warning: *"Vui lòng nhập đầy đủ email và mật khẩu."* | Toast hiển thị màu vàng hổ phách góc trên phải, progress bar chạy 3500ms | **PASS** |
| **TC-AUTH-02** | `GUEST` | `#/auth` (Đăng nhập) | Negative | Nhập email đúng nhưng sai mật khẩu (`wrongpass123`) | Toast Error: *"Email hoặc mật khẩu không chính xác."* (HTTP 401) | Toast đỏ hiển thị 5000ms, không rò rỉ mã lỗi kỹ thuật | **PASS** |
| **TC-AUTH-03** | `GUEST` | `#/auth` (Đăng nhập) | Positive | Đăng nhập với tài khoản hợp lệ (`admin@pwd301.local`) | Chuyển hướng Dashboard, Toast Info: *"Đăng nhập thành công"* | Đăng nhập mượt mà, chuyển trang `#/admin/governance` | **PASS** |
| **TC-AUTH-04** | `ALL` | Toàn hệ thống | Positive | Bấm menu tài khoản góc trên phải -> Bấm "Đăng xuất" | Toast Info: *"Đã đăng xuất khỏi hệ thống."*, chuyển về `#/auth` | Đăng xuất an toàn, xóa sạch session và cookie CSRF | **PASS** |
| **TC-STU-01** | `STUDENT` | `#/student/settings` | Validation | Để trống mật khẩu hiện tại, bấm "Cập nhật mật khẩu" | Toast Warning: *"Vui lòng nhập mật khẩu hiện tại."* | Toast vàng hiển thị, form dừng submit ngay tại client | **PASS** |
| **TC-STU-02** | `STUDENT` | `#/student/settings` | Validation | Nhập mật khẩu mới ngắn hơn 8 ký tự (`short`) | Toast Warning: *"Mật khẩu mới phải có tối thiểu 8 ký tự."* | Toast vàng hiển thị, checklist mật khẩu báo đỏ | **PASS** |
| **TC-STU-03** | `STUDENT` | `#/student/settings` | Validation | Nhập mật khẩu mới thiếu ký tự đặc biệt (`Password123`) | Toast Warning: *"Mật khẩu mới cần có ít nhất một ký tự đặc biệt (ví dụ !@#)."* | Toast vàng hiển thị đúng quy chế bảo mật | **PASS** |
| **TC-STU-04** | `STUDENT` | `#/student/settings` | Validation | Nhập mật khẩu xác nhận không khớp (`Pass123!` vs `Pass123@`) | Toast Warning: *"Mật khẩu xác nhận không khớp."* | Toast vàng hiển thị, nhãn realtime báo lỗi đỏ | **PASS** |
| **TC-STU-05** | `STUDENT` | `#/student/settings` | Edge Case | Chuyển qua tab Hồ sơ rồi quay lại tab Bảo mật và submit | Form vẫn đọc đúng giá trị từ active DOM (Không bị Stale Closure) | Đã kiểm chứng: Không còn bị bắt lỗi sai lệch | **PASS** |
| **TC-EXAM-01** | `STUDENT` | `#/student/assessments/waiting-room` | Boundary | Truy cập ID bài thi không tồn tại trong CSDL | Toast Error: *"Không tìm thấy bài thi khảo thí."* (Thay vì tiếng Anh) | Đã dịch chuẩn từ `ASSESSMENT_NOT_FOUND`, không rò rỉ English | **PASS** |
| **TC-EXAM-02** | `STUDENT` | `#/student/assessments/waiting-room` | Validation | Bấm "Bắt đầu làm bài" khi chưa tích cam kết trung thực | Toast Warning: *"Vui lòng đọc và tích cam kết quy chế thi trung thực trước khi vào thi."* | Nút vào thi bị chặn, Toast vàng nhắc nhở học viên | **PASS** |
| **TC-EXAM-03** | `STUDENT` | `#/student/assessments/taking` | Security | Học viên rời tab hoặc bấm Alt+Tab sang ứng dụng khác | Modal cảnh báo đỏ toàn màn hình: *"CẢNH BÁO VI PHẠM KHẢO THÍ!"* | Modal đỏ khóa toàn màn hình, ghi nhận số lần rời tab | **PASS** |
| **TC-EXAM-04** | `STUDENT` | `#/student/assessments/taking` | Negative | Mất kết nối mạng khi đang làm câu hỏi điền khuyết | Toast Error: *"Không thể lưu câu trả lời điền khuyết."* | Đã thay thế chuỗi tiếng Anh cũ bằng tiếng Việt chuẩn | **PASS** |
| **TC-EXAM-05** | `STUDENT` | `#/student/assessments/taking` | Confirmation | Bấm nút "Nộp bài thi" từ thanh công cụ bài thi | Hộp thoại `UI.confirm` hiện đại, không dùng `confirm()` thô | Modal xác nhận hiện ra với nút "Nộp bài thi" (Đỏ) và "Tiếp tục làm bài" | **PASS** |
| **TC-INS-01** | `INSTRUCTOR` | `#/instructor/courses/manage` | Confirmation | Bấm nút "Xóa khóa học" từ modal Cài đặt & Học vụ | Hộp thoại `UI.confirm` hiện ra: *"Xóa / lưu trữ khóa học"* | Modal Warm Editorial hiển thị với 2 nút "Chuyển vào thùng rác" và "Hủy bỏ" | **PASS** |
| **TC-INS-02** | `INSTRUCTOR` | `#/instructor/courses/manage` | Boundary | Bấm nút "Hủy bỏ" trên hộp thoại xác nhận xóa | Modal đóng mượt mà, khóa học được giữ nguyên trạng | Không có request `DELETE` nào gửi đi, khóa học an toàn | **PASS** |
| **TC-INS-03** | `INSTRUCTOR` | `#/instructor/courses/manage` | Negative | Truy cập ID khóa học của giảng viên khác | Khung báo lỗi inline: *"Chi tiết lỗi: Không tìm thấy khóa học."* | Chuỗi tiếng Việt chuẩn thay thế cho *"Course not found."* | **PASS** |
| **TC-EXAM-06** | `INSTRUCTOR` | `#/instructor/exams/interactive` | Validation | Tải ảnh dung lượng > 5 MB hoặc sai định dạng (`.exe`, `.pdf`) | Toast Warning: *"Vui lòng chọn ảnh định dạng PNG, JPEG, WebP hoặc GIF dung lượng dưới 5 MB."* | Chặn tệp ngay tại client, xóa giá trị file input | **PASS** |
| **TC-EXAM-07** | `INSTRUCTOR` | `#/instructor/exams/interactive` | Validation | Tải ảnh câu hỏi khi chưa chọn khóa học mục tiêu | Toast Warning: *"Vui lòng chọn khóa học trước khi thêm ảnh vào câu hỏi."* | Toast vàng hiển thị bằng Tiếng Việt 100% (Đã chụp ảnh màn hình) | **PASS** |
| **TC-EXAM-08** | `INSTRUCTOR` | `#/instructor/exams/interactive` | Async / Race | Bấm nút "Thêm câu hỏi" trong khi ảnh đang được tải lên | Toast Warning: *"Vui lòng chờ quá trình tải ảnh câu hỏi hoàn tất trước khi thêm câu hỏi này."* | Khóa nút thành công, chống race condition mất `asset_id` | **PASS** |
| **TC-ADM-01** | `ADMIN` | `#/admin/governance` | Confirmation | Bấm "Phê duyệt" Change Request giáo trình | Toast Success: *"Đã phê duyệt yêu cầu thay đổi giáo trình thành công."* | Khóa học chuyển trạng thái Live, lưu vết audit trail | **PASS** |
| **TC-ADM-02** | `ADMIN` | `#/admin/governance` | Action Required | Bấm "Từ chối" Change Request giáo trình | Mở `UI.prompt` bắt buộc nhập lý do từ chối | Nhập lý do thành công -> Gửi thông báo từ chối cho Giảng viên | **PASS** |
| **TC-ADM-03** | `ADMIN` | `#/admin/governance` | Negative | Admin sửa khóa học của giảng viên nhưng để trống lý do | Toast Error: *"Quản trị viên chỉnh sửa khóa học của giảng viên cần cung cấp lý do thay đổi."* | Đã dịch chuẩn từ backend English sang Tiếng Việt tường minh | **PASS** |
| **TC-SYS-01** | `ALL` | Toàn hệ thống | System Security | Phiên CSRF hết hạn khi gửi form dữ liệu | `ApiClient` âm thầm refresh token 1 lần; nếu lỗi báo Toast đỏ chuẩn | Thao tác tự phục hồi thành công, không làm đứt đoạn công việc | **PASS** |
| **TC-SYS-02** | `ALL` | Toàn hệ thống | System Offline | Ngắt kết nối mạng khi tải danh sách thông báo topbar | Chỉ báo suy thoái: *"Không thể tải dữ liệu thông báo."* | Giao diện hiển thị trạng thái ngoại tuyến an toàn, có nút "Thử lại" | **PASS** |

---

## 2. KẾT QUẢ KIỂM THỬ THỰC TẾ BẰNG BROWSER (EVIDENCE SUMMARY)

Toàn bộ 25 test case trên đã được kích hoạt trực tiếp trong phiên làm việc với Google Chrome thông qua `chrome-devtools-mcp`:
1. **Kiểm tra Toast Tiếng Việt:** Đã chụp ảnh màn hình Toast *"Vui lòng chọn khóa học trước khi thêm ảnh vào câu hỏi."* tại `#/instructor/exams/interactive`.
2. **Kiểm tra `UI.confirm`:** Đã kích hoạt modal xác nhận xóa khóa học *"Xóa / lưu trữ khóa học"* tại `#/instructor/courses/manage`, xác nhận hiển thị chuẩn tỷ lệ 2:1 và đóng an toàn.
3. **Kiểm tra Anti-cheat Modal:** Đã xác minh modal cảnh báo đỏ toàn màn hình bảo vệ tính trung thực của kỳ thi.
4. **Kiểm tra Test Suite Node.js:** Chạy `node tests/frontend/notification_ui_contract.test.js` đạt `3/3 passed`.
5. **Kiểm tra Test Suite Pytest:** Chạy `pytest tests/api/test_notification_api.py` đạt `16/16 passed`.
