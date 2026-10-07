# BÁO CÁO PHÁT HIỆN HỆ THỐNG THÔNG BÁO TOÀN DIỆN (NOTIFICATION DISCOVERY REPORT)
**Mã tài liệu:** `01_NOTIFICATION_DISCOVERY.md`  
**Dự án:** PWD301 LMS & Assessment Platform (Pure Headless Backend & SPA Frontend)  
**Ngày thực hiện:** 06/10/2026  
**Phương pháp rà soát:** Phân tích cú pháp trừu tượng (AST Analysis), Regex Source Audit, Phân tích luồng dữ liệu (Data-Flow Tracing) và Kiểm thử thực tế trình duyệt (Chrome DevTools MCP).

---

## 1. TỔNG QUAN PHẠM VI & PHƯƠNG PHÁP RÀ SOÁT (EXECUTIVE SUMMARY & SCOPE)

Nhằm giải quyết triệt để tình trạng phân mảnh thông báo, pha trộn ngôn ngữ Anh - Việt, rò rỉ mã lỗi kỹ thuật và không đồng bộ trạng thái giữa Backend CSDL và Giao diện người dùng, đợt rà soát Phase 1 (Discovery) đã quét 100% mã nguồn toàn hệ thống PWD301:
- **Tầng Frontend:** Gồm 8 tệp mã nguồn điều hướng và hiển thị SPA (`frontend/assets/js/ui.js`, `api.js`, `router.js`, `controllers.js`, `views/auth.js`, `views/student.js`, `views/instructor.js`, `views/instructor-exams.js`, `views/admin.js`).
- **Tầng Backend:** Toàn bộ 11 gói dịch vụ (`src/pwd301/services/`), 8 blueprints API RESTful (`src/pwd301/blueprints/`), bộ lọc ngoại lệ trung tâm (`src/pwd301/__init__.py`) và mô hình cơ sở dữ liệu Microsoft SQL Server (`src/pwd301/models/`).
- **Tầng Tương tác Thực nghiệm:** Kiểm thử trực tiếp trên trình duyệt Google Chrome thông qua giao thức Chrome DevTools MCP trên cả 4 vai trò người dùng: Quản trị viên (`ADMIN`), Giảng viên (`INSTRUCTOR`), Học viên (`STUDENT`) và Khách vãng lai (`GUEST`).

---

## 2. TOÀN BỘ CƠ CHẾ TẠO THÔNG BÁO Ở FRONTEND (FRONTEND MECHANISMS)

### 2.1. Hệ thống Toast Notification (`UI.showToast`)
- **Vị trí hiển thị:** Cố định góc trên bên phải màn hình (`#toast-container`), z-index cao nhất (`z-[9999]`), xếp chồng dạng stack theo thứ tự thời gian.
- **Cấu trúc thị giác:** Thiết kế theo phong cách Warm Editorial / Notion-like, bao gồm:
  - Icon badge ngữ cảnh (Check circle, Error, Warning, Info).
  - Nội dung thông báo dạng text có wrap và word-break, loại bỏ mã kỹ thuật UUID thô.
  - Nút đóng nhanh (`close` button).
  - Thanh tiến trình đếm ngược thời gian (`animated progress bar`) tự động co về 0% theo thời lượng hiển thị.
- **Tổng số lượt gọi AST phát hiện:** **359 vị trí** trong 8 tệp giao diện.
- **Các phân loại type:** `success`, `error` / `danger`, `warning`, `info`.

### 2.2. Hệ thống Hộp thoại & Modal Toàn cục (`UI.openModal`, `UI.closeModal`, `UI.closeAllModals`)
- **Quản lý ngăn xếp modal (`UI._modalStack`):** Hỗ trợ hiển thị modal lồng nhau (stacked modals). Khi mở modal mới, modal hiện tại được ẩn tạm thời và tự động phục hồi khi modal con đóng lại.
- **Hỗ trợ phím tắt:** Tự động lắng nghe phím `Escape` để đóng modal trên cùng; click vào lớp nền mờ (`backdrop-blur-sm`) để đóng an toàn.
- **Hộp thoại Thông báo Đơn (`UI.alert`):** Thay thế `window.alert()`. Trả về `Promise<boolean>`, hiển thị nút "Đã hiểu", không chặn UI thread của trình duyệt.
- **Hộp thoại Xác nhận Hành động Nguy hiểm (`UI.confirm`):** Thay thế `window.confirm()`. Trả về `Promise<boolean>`, hỗ trợ cờ `isDanger`, áp dụng tỷ lệ đệm nút bấm 2:1 (`px-4 py-2.5`), nhãn nút rõ ràng (`Xác nhận` / `Hủy bỏ`). Tổng số lượt gọi: **29 vị trí**.
- **Hộp thoại Nhập liệu Nhanh (`UI.prompt`):** Thay thế `window.prompt()`. Trả về `Promise<string|null>`, dùng cho các tác vụ cần lý do từ chối (Từ chối Change Request, Thu hồi quyền). Tổng số lượt gọi: **10 vị trí**.

### 2.3. Các Vi phạm Hộp thoại Trình duyệt Thô Đã Phát hiện (Raw Browser Dialog Invariants)
Trong đợt quét AST, phát hiện **6 vị trí vi phạm nghiêm trọng** việc sử dụng trực tiếp các hàm nguyên bản của trình duyệt, làm đóng băng luồng giao diện và phá vỡ quy chuẩn thiết kế:
1. `frontend/assets/js/controllers.js:30`: `alert(msg);` (Fallback khi không tìm thấy container lỗi đăng nhập).
2. `frontend/assets/js/controllers.js:184`: `alert('Không thể đăng ký: ' + e.message);` (Bắt lỗi ghi danh khóa học).
3. `frontend/assets/js/controllers.js:279`: `const confirmed = confirm('Bạn có chắc chắn muốn nộp bài thi khảo thí này không?...');` (Hộp thoại nộp bài thi).
4. `frontend/assets/js/views/instructor.js:5489`: `const confirmed = window.confirm(...);` (Hộp thoại xác nhận chuyển khóa học vào thùng rác).

### 2.4. Trung tâm Thông báo Nội ứng (Topbar Notification Center)
- **Vị trí:** Biểu tượng chuông trên thanh tiêu đề (`#topbar-notifications-btn`), kèm huy hiệu số lượng thông báo chưa đọc (`#unread-notification-count`).
- **Hành vi:**
  - Nhấp chuột mở dropdown danh sách thông báo mới nhất (`#topbar-notifications-dropdown`).
  - Hỗ trợ đánh dấu tất cả đã đọc thông qua API `POST /api/notifications/read`.
  - Phân loại trực quan: Thông báo phê duyệt giáo trình (`CHANGE_REQUEST`), Khảo thí & Điểm thi (`ASSESSMENT`), Cảnh báo kỷ luật (`ACADEMIC_ALERT`), Thông báo hệ thống (`SYSTEM`).
  - Cơ chế suy thoái mạng an toàn (`markNotificationFetchDegraded`): Khi mất kết nối hoặc API trả lỗi, chuyển sang trạng thái ngoại tuyến mềm dẻo thay vì làm vỡ giao diện.

### 2.5. Các Cơ chế Báo động Khảo thí & Trạng thái Inline
- **Modal Cảnh báo Gian lận Toàn màn hình (`AntiCheatModal`):** Khi phát hiện học viên rời tab (`blur`), chuyển cửa sổ hoặc vi phạm thời gian, kích hoạt modal đỏ cảnh báo cấp độ cao nhất (`CẢNH BÁO VI PHẠM KHẢO THÍ!`), khóa tương tác cho đến khi xác nhận cam kết trung thực.
- **Chỉ báo Tự động Lưu Đáp án (`Autosave Indicator`):** Trên màn hình thi trắc nghiệm và tự luận, hiển thị trạng thái realtime: `"Đang lưu..."` -> `"Đã lưu tự động"` hoặc `"Lỗi lưu đáp án"`.
- **Chỉ báo Biên tập Giáo trình (`Changeset Status Badge`):** Hiển thị nhãn `"Bản nháp cục bộ"`, `"Chờ duyệt"`, `"Đã phê duyệt"` tương ứng với chu kỳ Course Changeset.

---

## 3. TOÀN BỘ CƠ CHẾ TẠO THÔNG BÁO Ở BACKEND (BACKEND MECHANISMS)

### 3.1. Phong bì Phản hồi API Chuẩn hóa (Headless JSON Envelope Invariant)
Hệ thống tuân thủ nghiêm ngặt kiến trúc Pure Headless REST API. Mọi phản hồi HTTP đều được đóng gói theo định dạng JSON thống nhất, tuyệt đối không trả về trang lỗi HTML hay Jinja template:
- **Trường hợp Thành công:**
  ```json
  {
    "success": true,
    "data": { ... },
    "message": "Thực hiện thao tác thành công."
  }
  ```
- **Trường hợp Thất bại / Lỗi nghiệp vụ:**
  ```json
  {
    "success": false,
    "error": {
      "code": "ERROR_CODE_UPPERCASE",
      "message": "Mô tả lỗi chi tiết hoặc thân thiện với người dùng.",
      "details": { ... }
    }
  }
  ```

### 3.2. Bộ lọc Ngoại lệ Tập trung (`DOMAIN_EXCEPTION_HANDLERS`)
Tại `src/pwd301/__init__.py`, hệ thống đăng ký 104 bộ bắt lỗi domain-specific, chuyển hóa toàn bộ lỗi nghiệp vụ thành mã trạng thái HTTP chuẩn mực:
- `AuthenticationError` / `InvalidCredentialsError` -> HTTP 401 (`UNAUTHORIZED` / `INVALID_CREDENTIALS`).
- `AuthorizationError` / `ForbiddenError` -> HTTP 403 (`FORBIDDEN`).
- `ResourceNotFoundError` / `CourseNotFoundError` / `AssessmentNotFoundError` -> HTTP 404 (`NOT_FOUND` / `RESOURCE_NOT_FOUND`).
- `ValidationError` / `InvalidPayloadError` -> HTTP 400 hoặc 422 (`VALIDATION_ERROR`).
- `ConflictError` / `ActiveLeaseExistsError` / `StateTransitionError` -> HTTP 409 (`CONFLICT`).
- `RateLimitExceededError` -> HTTP 429 (`RATE_LIMIT_EXCEEDED`).
- `SystemException` / Lỗi không lường trước -> HTTP 500 (`INTERNAL_SERVER_ERROR`).

### 3.3. Dịch vụ Thông báo Chuyên biệt (`NotificationService` & `NotificationAudit`)
- Lưu trữ bản ghi thông báo trong cơ sở dữ liệu (`Notification`), gắn với người nhận (`user_id`), loại sự kiện (`event_type`), tiêu đề (`title`), nội dung (`content`) và trạng thái đọc (`is_read`).
- Mọi thông báo quan trọng gửi ra đều được lưu vết kiểm toán bất biến (Append-Only) trong bảng `NotificationAudit` nhằm phục vụ thanh tra học thuật và chống chối bỏ.

---

## 4. BẢNG TỔNG KẾT ĐỊNH LƯỢNG TOÀN DIỆN (DISCOVERY METRICS)

| Hạng mục Kiểm toán | Số lượng Phát hiện | Ghi chú & Đánh giá Kiến trúc |
| :--- | :---: | :--- |
| **Tổng số lệnh gọi Notification ở Frontend** | **406 vị trí** | Quét qua AST trên 8 tệp JavaScript chính. |
| - Gọi Toast (`UI.showToast`) | 359 vị trí | Tần suất xuất hiện cao nhất trong các luồng nghiệp vụ. |
| - Gọi Hộp thoại Xác nhận (`UI.confirm`) | 29 vị trí | Dùng cho hành động xóa, nộp bài, hủy thay đổi. |
| - Gọi Hộp thoại Nhập liệu (`UI.prompt`) | 10 vị trí | Dùng khi cần nhập lý do từ chối hoặc thu hồi quyền. |
| - Gọi Hộp thoại Báo tin (`UI.alert`) | 2 vị trí | Thông báo hướng dẫn và chính sách khảo thí. |
| - Lệnh gọi `alert()` nguyên bản (Vi phạm) | 3 vị trí | Nằm rải rác trong `controllers.js`. |
| - Lệnh gọi `confirm()` nguyên bản (Vi phạm) | 3 vị trí | Nằm trong `controllers.js` và `instructor.js`. |
| **Tổng số câu lệnh Ném Ngoại lệ / Sự kiện Backend**| **1,164 vị trí** | Phát hiện trong toàn bộ 11 service và 8 blueprints. |
| - Ngoại lệ trả về thông điệp Tiếng Anh | 952 vị trí (81.8%) | Nguồn gốc chính gây rò rỉ tiếng Anh ra giao diện. |
| - Ngoại lệ trả về thông điệp Tiếng Việt | 190 vị trí (16.3%) | Đã được bản địa hóa cục bộ tại tầng xác thực. |
| - Ngoại lệ không có thông điệp tường minh | 22 vị trí (1.9%) | Chỉ trả về mã lỗi HTTP thô. |
| **Mã lỗi Backend chuẩn (`error.code`)** | **34 mã chuẩn** | Cần bộ từ điển biên dịch sang Tiếng Việt ở FE. |

---

## 5. KẾT LUẬN GIAI ĐOẠN DISCOVERY

Hệ thống PWD301 đã sở hữu khung UI component rất hiện đại (`UI.showToast`, `UI.openModal`, `UI.confirm`), tuy nhiên hệ thống gặp phải lỗ hổng liên kết nghiêm trọng:
1. **Thiếu tầng chuyển đổi mã lỗi tập trung (Error Code Translation Layer):** Frontend tin cậy hoàn toàn vào chuỗi `err.message` ném từ `ApiClient`, vốn chứa đến 81.8% thông điệp tiếng Anh từ Backend, đè bẹp các chuỗi dự phòng tiếng Việt.
2. **Sự tồn tại của các hộp thoại thô nguyên bản (`alert`/`confirm`):** Vi phạm nguyên tắc bất biến trải nghiệm người dùng Jakob's Law và Impeccable UI.
3. **Một số chuỗi thông báo Tiếng Anh bị hard-code trực tiếp ở Frontend:** Điển hình trong các luồng tải ảnh câu hỏi thi và lưu đáp án điền khuyết.
4. **Lỗi tham chiếu đóng biến (Stale Closure):** Làm sai lệch kết quả validate form đổi mật khẩu học viên.

Các phát hiện này là tiền đề trực tiếp để lập danh mục tồn kho chi tiết tại `02_NOTIFICATION_INVENTORY.md` và phân tích gốc rễ tại `03_NOTIFICATION_ROOT_CAUSE_ANALYSIS.md`.
