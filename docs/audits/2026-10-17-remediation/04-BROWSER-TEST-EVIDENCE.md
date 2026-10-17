# 04 — BROWSER TEST EVIDENCE (BẰNG CHỨNG KIỂM THỬ TRÌNH DUYỆT THẬT)
**Dự án:** PWD301 LMS  
**Đợt khắc phục:** 17-10 Remediation  
**Công cụ sử dụng:** Chrome DevTools MCP (Target Page ID: 1, `http://localhost:5000`)  
**Thư mục lưu trữ bằng chứng:** `docs/audits/2026-10-17-remediation/screenshots/`

Toàn bộ 16 bước tương tác thực tế từ đầu đến cuối luồng nghiệp vụ trên hệ thống đang chạy thật đã được chụp ảnh màn hình và lưu trữ đầy đủ.

---

## Danh mục 16 Bước Thao tác và Bằng chứng Ảnh chụp

### Bước 02: Bảng Điều Khiển Giảng Viên (Instructor Dashboard)
- **Tài khoản:** `instructor1@pwd301.local` (TS. Nguyễn An Ninh)
- **URL:** `http://localhost:5000/#/instructor/dashboard`
- **Thao tác:** Đăng nhập thành công và nạp bảng điều khiển của Giảng viên với các thống kê lớp học, ca thi và danh mục tác vụ cần xử lý.
- **Tệp ảnh chụp:** [step02_instructor_dashboard.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step02_instructor_dashboard.png)

---

### Bước 03: Danh Sách Khóa Học Giảng Viên (Instructor Courses List)
- **URL:** `http://localhost:5000/#/instructor/courses`
- **Thao tác:** Xem danh mục 5 khóa học được phân công phụ trách (`WIR201`, `KAL101`, `CEH301`, `PYK201`, `SEC101`). Khóa học `SEC101` ("Bug Bounty Hunting & Bảo mật Ứng dụng Web Toàn diện") ở trạng thái `PUBLISHED`.
- **Tệp ảnh chụp:** [step03_instructor_courses_list.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step03_instructor_courses_list.png)

---

### Bước 04: Soạn Thảo Giáo Trình & Thanh Bản Nháp (Course Curriculum & Changeset Bar)
- **URL:** `http://localhost:5000/#/instructor/courses/manage?id=3a3ec597-34ac-463a-b084-af2592f368fc`
- **Thao tác:** Mở Single-Page Curriculum Studio của khóa học SEC101. Thanh công cụ bản nháp (Working Draft Action Bar) hiển thị số lượng thay đổi đang lưu nháp an toàn.
- **Tệp ảnh chụp:** [step04_course_curriculum_and_changeset_bar.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step04_course_curriculum_and_changeset_bar.png)

---

### Bước 05: Modal Biên Tập Trang Giới Thiệu & Bảng Chuẩn Đầu Ra (SLOs)
- **Thao tác:** Bấm nút "Trang Giới thiệu" (`#btn-edit-course-landing`). Modal Landing Page Builder mở ra hiển thị 3 chuẩn đầu ra (SLO-1, SLO-2, SLO-3) cùng các trọng số hiện tại.
- **Tệp ảnh chụp:** [step05_landing_and_slo_builder_modal.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step05_landing_and_slo_builder_modal.png)

---

### Bước 06: [BUG-01 Test] Chặn Trọng Số SLO Không Hợp Lệ (500%)
- **Thao tác:** Nhập trọng số dị thường `500%` vào ô input của SLO #1, bấm "Lưu thay đổi" (`#btn-save-unified-intro`).
- **Hiện tượng thực tế:** Hệ thống lập tức chặn lưu, viền đỏ trường nhập và hiển thị toast cảnh báo:
  > *"Trọng số của chuẩn đầu ra #1 không hợp lệ (500%). Trọng số phải nằm trong khoảng từ 0% đến 100%."*
- **Tệp ảnh chụp:** [step06_invalid_slo_weight_blocked.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step06_invalid_slo_weight_blocked.png)

---

### Bước 07: [BUG-01 Fix] Sửa Trọng Số Hợp Lệ (30%) & Lưu Thành Công
- **Thao tác:** Sửa trọng số về giá trị hợp lệ `30%`, bấm "Lưu thay đổi".
- **Hiện tượng thực tế:** Dữ liệu chuẩn đầu ra được lưu thành công vào cơ sở dữ liệu qua REST API, hiển thị thông báo cập nhật thành công.
- **Tệp ảnh chụp:** [step07_valid_slo_weight_saved_successfully.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step07_valid_slo_weight_saved_successfully.png)

---

### Bước 08: [BUG-01 Fix] Bảng Kiểm Định Xuất Bản (Publish Readiness Checklist)
- **Thao tác:** Mở modal kiểm tra điều kiện xuất bản (`#btn-submit-review`).
- **Hiện tượng thực tế:** Hệ thống phân tách độc lập và chính xác từng tiêu chuẩn: Tiêu chuẩn Mô tả khóa học (tối thiểu 20 ký tự) và Tiêu chuẩn Chuẩn đầu ra (SLOs) được đánh giá riêng biệt, không còn lỗi gộp thông báo sai.
- **Tệp ảnh chụp:** [step08_course_publish_checklist_modal.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step08_course_publish_checklist_modal.png)

---

### Bước 09: [BUG-02] Modal Tóm Tắt Khác Biệt Bản Nháp (Changeset Diff Summary)
- **Thao tác:** Bấm nút "Xem thay đổi" (`#btn-view-changeset-diff`) trên thanh bản nháp.
- **Hiện tượng thực tế:** Modal Diff Engine hiển thị danh mục các bài học được thêm mới hoặc chỉnh sửa (ADDED / MODIFIED / REORDERED) mà không bị duplicate.
- **Tệp ảnh chụp:** [step09_changeset_diff_modal.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step09_changeset_diff_modal.png)

---

### Bước 10: [BUG-03 Fix] Bản Nháp Ở Trạng Thái Chỉnh Sửa Tự Do (Editable Draft Mode)
- **Thao tác:** Thu hồi/mở bản nháp. Nút "Gửi xét duyệt" (`#btn-submit-course-changeset`) hiển thị sáng rõ, sẵn sàng nhận đợt cập nhật.
- **Tệp ảnh chụp:** [step10_editable_draft_action_bar.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step10_editable_draft_action_bar.png)

---

### Bước 11: [BUG-02 / BUG-03] Modal Gửi Duyệt Đợt Cập Nhật Giáo Trình
- **Thao tác:** Bấm nút "Gửi xét duyệt" (`#btn-submit-course-changeset`). Modal hiển thị form nhập Tiêu đề đợt cập nhật và Ghi chú gửi Quản trị viên.
- **Tệp ảnh chụp:** [step11_submit_changeset_modal.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step11_submit_changeset_modal.png)

---

### Bước 12: [BUG-02 / BUG-03] Gửi Duyệt Thành Công & Cập Nhật Phản Ứng Tức Thì Không Cần F5
- **Thao tác:** Nhập tiêu đề và bấm "Gửi Quản trị viên".
- **Hiện tượng thực tế:** Gửi duyệt thành công mà không gặp thông báo lỗi `"Không có thay đổi để gửi xét duyệt"`. Thanh tác vụ tự động chuyển sang huy hiệu màu vàng: **"Đợt cập nhật đang chờ duyệt (PENDING)"** kèm nút "Rút lại yêu cầu" mà không cần F5 tải lại trang.
- **Tệp ảnh chụp:** [step12_changeset_submitted_pending_reactive.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step12_changeset_submitted_pending_reactive.png)

---

### Bước 13: Bảng Điều Khiển Học Viên (Student Dashboard)
- **Tài khoản:** Chuyển sang vai trò Học viên (`HỌC VIÊN`).
- **URL:** `http://localhost:5000/#/student/dashboard`
- **Thao tác:** Nạp giao diện học tập với các thẻ KPI, khóa học đang học và danh sách khảo thí sắp diễn ra.
- **Tệp ảnh chụp:** [step13_student_dashboard.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step13_student_dashboard.png)

---

### Bước 14: [BUG-04 Fix] Hero Card Khóa Học với Nút "Xem Chi Tiết"
- **URL:** `http://localhost:5000/#/student/courses/intro?id=3a3ec597-34ac-463a-b084-af2592f368fc`
- **Thao tác:** Mở trang giới thiệu chi tiết khóa học SEC101.
- **Hiện tượng thực tế:** Nút **"Xem chi tiết"** (`#btn-scroll-to-syllabus`) với icon `menu_book` hiển thị trang trọng, cân đối ngay bên cạnh nút "Ghi danh khóa học".
- **Tệp ảnh chụp:** [step14_hero_card_with_xem_chi_tiet_button.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step14_hero_card_with_xem_chi_tiet_button.png)

---

### Bước 15: [BUG-04 Fix] Cuộn Mượt Đến Lộ Trình Đào Tạo (#syllabus-section)
- **Thao tác:** Bấm nút "Xem chi tiết".
- **Hiện tượng thực tế:** Viewport cuộn mượt (smooth scroll) trực tiếp xuống section "Lộ trình đào tạo" (`#syllabus-section`) với tọa độ đỉnh `rectTop = 55.67px`, hiển thị rõ ràng toàn bộ 4 chương và 12 bài học của khóa học.
- **Tệp ảnh chụp:** [step15_scrolled_to_syllabus_section.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step15_scrolled_to_syllabus_section.png)

---

### Bước 16: Danh Sách Khảo Thí Học Viên (Student Assessments List)
- **URL:** `http://localhost:5000/#/student/assessments`
- **Thao tác:** Nạp danh sách các bài kiểm tra học phần đang mở và kết quả thi.
- **Tệp ảnh chụp:** [step16_student_assessments_list.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step16_student_assessments_list.png)

---

### Bước 17: [BUG-05 Fix] Màn Hình Phòng Chờ Thi & Điểm Số Đồng Bộ "Chưa Công Bố"
- **URL:** `http://localhost:5000/#/student/assessments/waiting-room?id=fa8e64e4-5fb3-4717-9cec-904fa93839df`
- **Thao tác:** Mở phòng chờ thi của bài kiểm tra "Kỳ thi Đánh giá Năng lực Chuyên viên Tình báo An ninh Mạng".
- **Hiện tượng thực tế:** Thẻ 4 thông số hiển thị mục **Điểm** là **"Chưa công bố"** (với badge màu xám trung tính `#64748b`), triệt tiêu hoàn toàn sự mâu thuẫn giữa "Chờ công bố" và "Chưa đạt" khi bài thi chưa đến hạn công bố kết quả.
- **Tệp ảnh chụp:** [step17_waiting_room_synchronized_score.png](file:///e:/PWD301/docs/audits/2026-10-17-remediation/screenshots/step17_waiting_room_synchronized_score.png)
