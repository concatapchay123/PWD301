# KẾ HOẠCH TRIỂN KHAI TASK-109: HỆ THỐNG REALTIME TOÀN DIỆN, MODAL XÓA KHÓA HỌC 2FA, CHUẨN HÓA ADMIN & KIỂM THỬ TRÌNH DUYỆT THỰC ĐỊA 20-40 VÒNG

> **Quyền hạn Workflow:** [WORKFLOW_SUPERSESSION.md](../../system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md). Xóa bỏ 100% các logic cũ, workflow cũ đã lỗi thời (WF18–WF22).  
> **Phương thức thực thi:** Multi-Agent Orchestration (Antigravity spawns specialized subagents) + Vòng lặp STLC kiểm thử trình duyệt thật (Real Chrome Browser) tối thiểu 20 vòng, tối đa 40 vòng kèm ảnh chụp minh chứng từng thao tác.

---

## 1. Mục Tiêu & Kiến Trúc Tổng Thể

### 1.1. Mục tiêu (Goals)
1. **Triệt tiêu 100% tình trạng phải bấm F5 tải lại trang**:
   - Xây dựng hệ thống **Server-Sent Events (SSE) native trên Flask** kết hợp **Reactive EventBus** phía Frontend. Mọi thay đổi dữ liệu (CRUD Khóa học, Bài giảng, Câu hỏi, Bài thi, Tài liệu, Người dùng, Cài đặt) đều tự động phát tín hiệu và cập nhật giao diện trong thời gian thực với độ trễ mili-giây.
   - Giảng viên biên tập khóa học: Tự động lưu bản nháp $\rightarrow$ mở sáng ngay lập tức nút *"Gửi xét duyệt"* và *"Xem thay đổi"* trên thanh tác vụ mà không cần F5.
   - Giảng viên gửi xét duyệt $\rightarrow$ Admin nhận thông báo tức thì, chuông rung, badge nhảy số, bảng xét duyệt tự chèn dòng mới mà không cần F5.
2. **Chuẩn hóa Modal Xóa Khóa Học & Khắc phục triệt để lỗi HTTP 405**:
   - Thay thế toàn bộ `window.confirm` / `window.prompt` của trình duyệt bằng **Modal hệ thống chuẩn mực**.
   - Cơ chế bảo mật xác nhận kép 2FA: Người dùng bắt buộc phải gõ chính xác **Mã môn học** và chuỗi ký tự **"XÁC NHẬN XÓA"** thì nút Xóa mới sáng lên.
   - Với Admin: Modal tích hợp thêm ô nhập *"Lý do kiểm toán xóa khóa học"* (Audit Reason) phục vụ nhật ký an ninh.
   - Bổ sung và đồng bộ route backend/frontend để triệt tiêu lỗi HTTP 405 Method Not Allowed khi xóa.
3. **Chuẩn hóa giao diện Quản Lý Khóa Học của Admin**:
   - Đổi tiêu đề thành **"Quản lý khóa học"**.
   - Đồng bộ chính xác tên Giảng viên phụ trách/tạo khóa học (`owner_instructor_name`).
   - Lọc sạch các khóa học Bản nháp (`DRAFT`), chỉ hiển thị các khóa học Đã xuất bản (`PUBLISHED`).
4. **Sửa lỗi va chạm UI của Bạch Tuộc Trợ Lí AI**:
   - Tự động ẩn hoàn toàn nút tròn Bạch tuộc khi khung chat mở ra, đảm bảo không bao giờ đè lên nút đóng `[X]` hay thanh tiêu đề.
   - Khôi phục nút tròn mượt mà về đúng tọa độ cũ khi người dùng bấm nút `[X]` đóng chat.
5. **Thanh lọc toàn bộ logic và workflow cũ**:
   - Đăng ký hợp đồng thay thế WF18–WF22 vào `WORKFLOW_SUPERSESSION.md` và đồng bộ vào `tasks/CURRENT.md`.

---

## 2. Bản Đồ Tác Vụ Chi Tiết (Task Decomposition)

### Task 1: Thanh Lọc & Đăng Ký Hợp Đồng Thay Thế Workflow (Supersession Contract)
- **Files:**
  - Modify: `docs/system/PWD301_SYSTEM_SPECIFICATION/implementation/WORKFLOW_SUPERSESSION.md`
  - Overwrite: `tasks/CURRENT.md`
- **Nội dung:**
  - Bổ sung hợp đồng thay thế WF18 (Modal xóa 2FA), WF19 (Đồng bộ DELETE endpoint 405), WF20 (Admin Quản lý khóa học & lọc draft), WF21 (Kiến trúc Realtime SSE + EventBus), WF22 (Vòng đời ẩn/hiện AI Widget).
  - Cập nhật `tasks/CURRENT.md` chuyển sang `TASK-109: REALTIME LMS ARCHITECTURE & UI HARDENING`, thiết lập trạng thái IN_PROGRESS.

---

### Task 2: Backend Realtime Infrastructure (SSE Stream & Universal Event Dispatcher)
- **Files:**
  - Create: `src/pwd301/services/realtime_service.py`
  - Modify: `src/pwd301/blueprints/api_notifications/routes.py` (hoặc tạo endpoint `/api/events/stream`)
  - Hook vào các services:
    - `src/pwd301/services/course_service.py` (phát sự kiện `course:created`, `course:updated`, `course:published`, `course:trashed`)
    - `src/pwd301/services/lesson_service.py` (phát sự kiện `changeset:updated`, `changeset:submitted`, `changeset:approved`, `changeset:rejected`)
    - `src/pwd301/services/assessment_service.py` (phát sự kiện `assessment:updated`, `assessment:submitted`)
    - `src/pwd301/services/notification_service.py` (phát sự kiện `notification:broadcast`, `notification:new`)
- **Nội dung:**
  - Xây dựng `SSEManager` quản lý kết nối streaming đa luồng theo user session / role, hỗ trợ cơ chế heartbeat ping (mỗi 15s) tránh rớt kết nối.
  - Endpoint `GET /api/events/stream` (và `/auth/events/stream`) phục vụ định dạng `text/event-stream`, kiểm tra phiên đăng nhập an toàn.
  - Viết test unit kiểm thử phát sự kiện và stream dữ liệu SSE.

---

### Task 3: Frontend Reactive Engine & In-Session Instant State (Zero-F5)
- **Files:**
  - Create/Update: `frontend/assets/js/realtime.js` (hoặc tích hợp vào `frontend/assets/js/router.js` & `frontend/assets/js/ui.js`)
  - Modify: `frontend/assets/js/views/instructor.js`
  - Modify: `frontend/assets/js/views/admin.js`
  - Modify: `frontend/assets/js/views/student.js`
- **Nội dung:**
  - Khởi tạo kết nối `EventSource('/api/events/stream')` với logic auto-reconnect tự động tăng dần thời gian chờ khi mất mạng.
  - Xây dựng `EventBus.on(eventType, callback)` để các view đăng ký nhận tin.
  - **In-Session Reactivity tại Giảng viên Studio**:
    - Khi hook autosave của bài giảng hoặc header khóa học chạy xong: tự động cập nhật local `changesetStatus = { has_changes: true, changes_count: N }`, lập tức gọi hàm re-render thanh công cụ changeset $\rightarrow$ nút *"Gửi xét duyệt"* và *"Xem thay đổi"* sáng lên trong 0 mili-giây.
  - **Cross-User Reactivity tại Admin**:
    - Khi nhận sự kiện `changeset:submitted`: Admin hiển thị Toast thông báo xanh, tăng badge số lượng chờ duyệt trên Topbar, và tự động gọi nạp thêm/cập nhật hàng mới vào bảng chờ duyệt mà không làm mất trạng thái trang.
  - **Reactivity khi Phê Duyệt / Xóa**:
    - Khi Admin duyệt hoặc từ chối: Bên Giảng viên lập tức nhận thông báo và làm mới trạng thái nút.
    - Khi xóa khóa học: Khóa học biến mất khỏi bảng và thẻ của tất cả các màn hình đang mở.

---

### Task 4: Hệ Thống Modal Xóa Khóa Học 2FA & Sửa Lỗi 405 Method Not Allowed
- **Files:**
  - Modify: `src/pwd301/blueprints/instructor/routes.py` (bổ sung route `DELETE /courses/<course_id>` song song với `/courses/<course_id>/trash`)
  - Modify: `src/pwd301/blueprints/admin/routes.py` (bổ sung route `DELETE /courses/<course_id>` song song với `/courses/<course_id>/trash`)
  - Modify: `frontend/assets/js/api.js` (chuẩn hóa `deleteInstructorDraftCourse` và `deleteAdminCourse`)
  - Modify: `frontend/assets/js/ui.js` (bổ sung phương thức `UI.showCourseDelete2FAModal({...})`)
  - Modify: `frontend/assets/js/views/instructor.js` (thay thế `confirm(...)` cũ)
  - Modify: `frontend/assets/js/views/admin.js` (thay thế `prompt(...)` cũ)
- **Nội dung:**
  - Xây dựng Modal Xóa Khóa Học chuyên nghiệp:
    - Hiển thị huy hiệu cảnh báo đỏ nguy hiểm.
    - Hiển thị tên khóa học, mã môn học rõ ràng.
    - Với Admin: Ô nhập Textarea *"Lý do kiểm toán xóa khóa học (Bắt buộc)"*.
    - Xác thực 2 bước (2FA): Ô nhập yêu cầu gõ chính xác **Mã môn** và ô nhập gõ chính xác **"XÁC NHẬN XÓA"**. Nút bấm "Xóa vĩnh viễn" / "Chuyển vào thùng rác" bị khóa mờ (`disabled`) cho đến khi người dùng nhập đúng 100% cả 2 điều kiện.
  - Thử nghiệm gọi API xóa và xử lý phản hồi thành công, hiển thị Toast xanh, phát sự kiện realtime.

---

### Task 5: Chuẩn Hóa Giao Diện Quản Lý Khóa Học Phía Admin
- **Files:**
  - Modify: `frontend/assets/js/views/admin.js`
  - Modify: `src/pwd301/blueprints/admin/routes.py`
- **Nội dung:**
  - Đổi tiêu đề Section 3 thành **"Quản lý khóa học"** (loại bỏ chữ "Quản lý & Xóa...").
  - Cột Giảng viên: Lấy chính xác `c.owner_instructor_name || c.instructor_name || c.instructor?.display_name || c.owner_instructor?.full_name`, chấm dứt việc hiển thị sai lệch "Chưa phân công".
  - Cột Trạng thái & Lọc danh mục: Lọc bỏ hoàn toàn các khóa học có trạng thái `DRAFT` (Bản thảo). Chỉ hiển thị các khóa học đã xuất bản (`PUBLISHED`) cho Admin quản lý.

---

### Task 6: Tối Ưu Hóa Giao Diện Bạch Tuộc Trợ Lí AI (Triệt Tiêu Va Chạm)
- **Files:**
  - Modify: `frontend/assets/js/ui.js` (`FloatingAITutor`)
  - Modify: `frontend/index.html`
- **Nội dung:**
  - Trong `FloatingAITutor.toggleDrawer()` và `openDrawer()`: Khi bung khung chat ra, lập tức ẩn nút tròn `#floating-ai-launcher` (`launcher.style.display = 'none'`).
  - Khi người dùng bấm nút đóng `[X]` ở góc trên bên phải khung chat (hoặc ấn `Esc`): Khung chat ẩn đi và nút tròn `#floating-ai-launcher` lập tức hiện lại mượt mà đúng tọa độ trước đó.
  - Đảm bảo thanh tiêu đề chat (nút refresh và nút close `[X]`) thông thoáng 100%, không bị bất kỳ phần tử nào che lấp.

---

### Task 7: Vòng Lặp Kiểm Thử Trình Duyệt Thực Tế STLC (20-40 Vòng) Bằng Subagents
- **Phương thức:**
  - Spawns các subagent phối hợp: Implementer Subagent, Browser Tester Subagent (tương tác trực tiếp với Chrome thật qua DevTools), và Quality Auditor Subagent.
  - **Mỗi vòng lặp gồm 4 bước bắt buộc**:
    1. Thao tác trên trình duyệt thật (Click, Type, Autosave, Submit, Delete, Verify).
    2. Chụp ảnh màn hình thực tế lưu vào `artifacts/screenshots/roundXX_*.png`.
    3. Ghi chép chú thích chi tiết các hành động đã làm trong ảnh đó.
    4. Đối soát (Audit) với tiêu chí người dùng. Nếu phát hiện lỗi mới hoặc chưa đạt $\rightarrow$ fix bug ngay và lặp lại vòng tiếp theo.
  - **Số vòng tối thiểu:** 20 vòng; **Tối đa:** 40 vòng.

---

## 3. Ma Trận Kế Hoạch 25 Vòng STLC Thực Địa Với Trình Duyệt Thật

| Vòng (Round) | Mục tiêu kiểm thử thao tác thật trên Chrome | Bằng chứng ảnh dự kiến |
| :---: | :--- | :--- |
| **R01** | Kiểm tra mở trang Giảng viên & Danh sách khóa học nháp | `r01_instructor_courses_list.png` |
| **R02** | Giảng viên chỉnh sửa Tiêu đề & Mã môn $\rightarrow$ Kiểm tra Autosave Realtime không F5 | `r02_instructor_autosave_header.png` |
| **R03** | Xác minh nút *"Gửi xét duyệt"* và *"Xem thay đổi"* sáng lên tức thì trong 0ms | `r03_changeset_buttons_unlocked.png` |
| **R04** | Giảng viên chỉnh sửa nội dung bài giảng $\rightarrow$ Autosave cập nhật số lượng thay đổi realtime | `r04_lesson_autosave_realtime.png` |
| **R05** | Giảng viên bấm *"Xem thay đổi"* $\rightarrow$ Diff Modal hiển thị chuẩn xác các mục đã sửa | `r05_changeset_diff_modal.png` |
| **R06** | Giảng viên bấm *"Gửi xét duyệt"* khóa học thành công | `r06_changeset_submitted_success.png` |
| **R07** | Mở song song Admin $\rightarrow$ Xác minh Toast notification nảy lên tức thì mà không cần F5 | `r07_admin_realtime_toast_notif.png` |
| **R08** | Xác minh Badge Topbar của Admin nhảy số tự động và bảng Chờ duyệt hiện dòng mới | `r08_admin_review_queue_live.png` |
| **R09** | Admin mở xem Diff đối chiếu khóa học chờ duyệt | `r09_admin_review_diff_view.png` |
| **R10** | Admin bấm Phê duyệt $\rightarrow$ Giảng viên nhận thông báo realtime được duyệt không cần F5 | `r10_admin_approved_instructor_notified.png` |
| **R11** | Giảng viên bấm icon Xóa khóa học nháp $\rightarrow$ Modal Hệ Thống Cảnh Báo Đỏ xuất hiện | `r11_instructor_delete_modal_opened.png` |
| **R12** | Thử nhập sai Mã môn / chữ xác nhận $\rightarrow$ Nút Xóa vẫn bị khóa xám (2FA Guard) | `r12_delete_modal_2fa_disabled.png` |
| **R13** | Nhập đúng Mã môn và chữ "XÁC NHẬN XÓA" $\rightarrow$ Nút Xóa sáng đỏ | `r13_delete_modal_2fa_enabled.png` |
| **R14** | Bấm Xóa $\rightarrow$ Gọi API thành công (không còn lỗi 405), khóa học biến mất realtime | `r14_draft_course_deleted_live.png` |
| **R15** | Vào trang Admin $\rightarrow$ Tiêu đề hiển thị chuẩn xác *"Quản lý khóa học"* | `r15_admin_course_management_title.png` |
| **R16** | Kiểm tra Cột Giảng viên $\rightarrow$ Hiển thị đúng tên giảng viên thực tế (hết 'Chưa phân công') | `r16_admin_instructor_names_synced.png` |
| **R17** | Kiểm tra Cột Trạng thái $\rightarrow$ 100% khóa học nháp đã bị ẩn, chỉ còn khóa học Đã xuất bản | `r17_admin_only_published_courses.png` |
| **R18** | Admin bấm nút Xóa khóa học $\rightarrow$ Modal hệ thống yêu cầu Lý do kiểm toán & 2FA xuất hiện | `r18_admin_soft_delete_modal.png` |
| **R19** | Admin nhập lý do kiểm toán + 2FA và bấm Xóa $\rightarrow$ Xóa mềm TRASH thành công (no 405) | `r19_admin_course_trashed_success.png` |
| **R20** | Click mở Bạch tuộc trợ lí AI $\rightarrow$ Nút tròn tự động ẩn hoàn toàn, không đè lên chat | `r20_ai_launcher_hidden_on_open.png` |
| **R21** | Kiểm tra Header cửa sổ chat $\rightarrow$ Nút làm mới và nút [X] hiển thị nguyên vẹn, sạch sẽ | `r21_ai_header_buttons_visible.png` |
| **R22** | Bấm nút [X] đóng chat $\rightarrow$ Nút tròn hiện lại mượt mà đúng vị trí ban đầu | `r22_ai_launcher_restored_cleanly.png` |
| **R23** | Kéo thả nút tròn Bạch tuộc sang góc khác $\rightarrow$ Mở chat rồi đóng lại $\rightarrow$ Vị trí giữ nguyên | `r23_ai_launcher_drag_and_persist.png` |
| **R24** | Kiểm tra Stress Test luồng SSE: Đóng tab, ngắt mạng giả lập $\rightarrow$ Tự động reconnect mượt mà | `r24_sse_auto_reconnect_test.png` |
| **R25** | Tổng kiểm tra toàn diện (Full Regression Audit) tất cả 4 tính năng đã hoàn thiện 100% | `r25_final_full_system_audit.png` |

---

## 4. Cam Kết Tiêu Chuẩn Kỹ Thuật (Constraints & Non-Negotiables)
- **TDD Iron Law:** Viết bài kiểm tra fail trước khi triển khai code cho các endpoint backend và component modal.
- **Pure Headless Backend:** Giữ vững cấu trúc API JSON chuẩn `{"success": true/false, "data": ...}`.
- **Fail-Closed Security:** Quyền xóa khóa học được phân tách nghiêm ngặt: Giảng viên chỉ được xóa bản nháp của chính mình, Admin xóa mềm có lý do kiểm toán lưu vào Audit Log.
- **Ảnh bằng chứng trung thực:** Toàn bộ ảnh chụp là giao diện từ trình duyệt Chrome thật, được lưu trữ vĩnh viễn trên đĩa kèm chú thích rõ ràng.
