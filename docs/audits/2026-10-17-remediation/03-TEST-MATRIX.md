# 03 — TEST MATRIX (MA TRẬN KIỂM THỬ)
**Dự án:** PWD301 LMS  
**Đợt khắc phục:** 17-10 Remediation

---

| Test ID | Bug ID | Preconditions | Actions | Expected Result | Actual Result | PASS / FAIL |
|---|---|---|---|---|---|---|
| **TM-01-A** | BUG-01 | Đăng nhập tài khoản Giảng viên; mở Landing Page Builder | Nhập trọng số SLO = 500% | Frontend hiển thị viền đỏ và thông báo lỗi; API từ chối lưu với lỗi 400 | Chặn lưu ở UI và backend trả lỗi `INVALID_SLO_WEIGHT` | **PASS** |
| **TM-01-B** | BUG-01 | Đang ở Landing Page Builder | Nhập trọng số SLO = -15% hoặc chuỗi chữ 'abc' | Frontend/backend từ chối lưu dữ liệu | Trả về thông báo lỗi trọng số không hợp lệ | **PASS** |
| **TM-01-C** | BUG-01 | Nhập trọng số hợp lệ (ví dụ: 30%, 50%) và lưu | Bấm Lưu thông tin khóa học | Backend lưu thành công vào JSON field; UI hiển thị toast thành công | Lưu thành công, dữ liệu giữ nguyên sau reload | **PASS** |
| **TM-01-D** | BUG-01 | Khóa học có mô tả < 20 ký tự nhưng có đủ SLOs | Gọi endpoint / kiểm tra readiness checklist | Checklist báo mục description không đạt; không đổ lỗi do SLO | Trả về chi tiết: `Mô tả khóa học chưa đạt yêu cầu...` | **PASS** |
| **TM-01-E** | BUG-01 | Khóa học có mô tả > 20 ký tự nhưng chưa có SLOs | Gọi endpoint / kiểm tra readiness checklist | Checklist báo mục SLO không đạt; không báo lỗi description | Trả về chi tiết: `Khóa học cần có ít nhất một chuẩn đầu ra...` | **PASS** |
| **TM-02-A** | BUG-02 | Khóa học đã xuất bản có 01 bài học nháp mới | Giảng viên mở modal "Gửi duyệt đợt cập nhật", nhập tiêu đề và bấm Gửi | Hệ thống không báo lỗi "Không có thay đổi"; gửi thành công sang trạng thái PENDING | Thay đổi được ghi nhận và gửi duyệt thành công | **PASS** |
| **TM-02-B** | BUG-02 | Giảng viên thay đổi thứ tự các bài học trong chương | Lưu và gửi xét duyệt; Admin phê duyệt đợt cập nhật | Các bài học kế thừa đúng thứ tự mới trong bảng chính thức | Mapping qua `previous_lesson_id` bảo toàn đúng rank | **PASS** |
| **TM-03-A** | BUG-03 | Bản nháp đang ở trạng thái PENDING (đã gửi duyệt) | Giảng viên bấm nút "Hủy bỏ bản nháp" (Discard Changeset) | Hệ thống cho phép thu hồi bản nháp về trạng thái tự do để sửa | Thu hồi và xóa bản nháp thành công | **PASS** |
| **TM-03-B** | BUG-03 | Giảng viên lưu một thay đổi trên giáo trình | Quan sát thanh Action Bar trên giao diện | Trạng thái bản nháp và số lượng thay đổi cập nhật tức thì không cần F5 | DOM tự cập nhật qua `refreshChangesetStatus` | **PASS** |
| **TM-04-A** | BUG-04 | Đăng nhập Học viên; mở trang chi tiết khóa học | Quan sát Hero Card giới thiệu khóa học | Nút "Xem chi tiết" (`#btn-scroll-to-syllabus`) hiển thị trang trọng cạnh "Ghi danh" | Nút hiển thị đầy đủ icon và text | **PASS** |
| **TM-04-B** | BUG-04 | Đang ở Hero Card | Bấm nút "Xem chi tiết" | Trình duyệt cuộn mượt (smooth scroll) trực tiếp đến section "Lộ trình đào tạo" | Viewport cuộn đến `#syllabus-section` (`rectTop = 55.67px`) | **PASS** |
| **TM-05-A** | BUG-05 | Học viên nộp bài thi có chính sách INSTRUCTOR_RELEASE | Chưa đến thời điểm công bố điểm của Giảng viên | Hero card hiển thị điểm "Chưa công bố"; Bảng lịch sử hiển thị cột điểm "Chưa công bố", cột kết quả hiển thị badge xám "Chưa công bố" | Không hiển thị "Chờ công bố" một đằng, "Chưa đạt" một nẻo; badge màu xám trung tính | **PASS** |
| **TM-05-B** | BUG-05 | Giảng viên công bố điểm thi cho học viên | Học viên xem lại trang khảo thí / phòng chờ | Điểm hiển thị đồng nhất định dạng `${attemptScore} / ${maxScore}`; Kết quả hiển thị "Đạt" hoặc "Chưa đạt" | Điểm số và trạng thái đồng bộ 100% | **PASS** |
