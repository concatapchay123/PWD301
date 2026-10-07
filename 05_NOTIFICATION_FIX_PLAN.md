# KẾ HOẠCH KHẮC PHỤC HỆ THỐNG THÔNG BÁO (NOTIFICATION FIX PLAN)
**Mã tài liệu:** `05_NOTIFICATION_FIX_PLAN.md`  
**Dự án:** PWD301 LMS & Assessment Platform  
**Trạng thái:** Hoàn tất 100% Thực thi & Kiểm chứng  
**Mục tiêu:** Khắc phục triệt để các lỗi phân mảnh, rò rỉ tiếng Anh, đơ giao diện và thiết lập rào chắn hồi quy lâu dài.

---

## 1. BẢNG KẾ HOẠCH KHẮC PHỤC TỔNG THỂ (MASTER FIX MATRIX)

Bảng dưới đây phân loại chi tiết toàn bộ các đầu việc khắc phục theo các nhóm: **Quick Fix**, **Structural Fix**, **Refactor** và **Long-term Improvement**:

| Fix ID | Issue (Vấn đề) | Root Cause (Nguyên nhân) | Proposed Fix (Giải pháp đề xuất) | FE | BE | DB | Risk | Dependencies | Test Required | Priority |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :---: |
| **FIX-QF-01** | Gọi `alert()` thô trong `controllers.js:30, 184` làm đơ UI thread | Lập trình viên dùng hàm trình duyệt mặc định làm fallback | Thay bằng `UI.showToast(msg, 'error')` | Có | Không | Không | Rất thấp | `UI.showToast` | Test đơn vị & Test browser | **Quick Fix (P0)** |
| **FIX-QF-02** | Gọi `confirm()` thô khi nộp bài thi (`controllers.js:279`) | Chưa tích hợp modal xác nhận bất đồng bộ | Thay bằng `await UI.confirm('Nộp bài thi khảo thí', ...)` | Có | Không | Không | Rất thấp | `UI.confirm` | Test luồng nộp bài thi | **Quick Fix (P0)** |
| **FIX-QF-03** | Gọi `window.confirm()` khi xóa khóa học (`instructor.js:5489`) | Sử dụng dialog đồng bộ của window | Thay bằng `await UI.confirm('Xóa / lưu trữ khóa học', ..., true)` | Có | Không | Không | Rất thấp | `UI.confirm` | Test luồng xóa khóa học | **Quick Fix (P0)** |
| **FIX-QF-04** | Chuỗi Toast tiếng Anh hard-code trong Soạn đề thi (`instructor-exams.js`) | Sao chép mã nguồn mẫu tiếng Anh chưa bản địa hóa | Chuyển ngữ 100% sang Tiếng Việt học thuật chuẩn mực | Có | Không | Không | Rất thấp | Không | Test giao diện tải ảnh câu hỏi | **Quick Fix (P0)** |
| **FIX-QF-05** | Chuỗi Toast tiếng Anh khi lưu đáp án điền khuyết (`student.js:5063`) | Chưa dịch fallback tiếng Anh | Thay bằng `'Không thể lưu câu trả lời điền khuyết.'` | Có | Không | Không | Rất thấp | Không | Test bài thi điền khuyết | **Quick Fix (P0)** |
| **FIX-QF-06** | Lỗi font ký tự (Mojibake) trong autosave indicator (`student.js:5056`) | Lỗi mã hóa UTF-8 bị lưu sai bảng mã | Sửa lại chuỗi đúng: `'Đang lưu...'` và `'Đã lưu tự động'` | Có | Không | Không | Rất thấp | Không | Test hiển thị autosave | **Quick Fix (P0)** |
| **FIX-QF-07** | Lỗi Stale Closure DOM khi đổi mật khẩu (`student.js:7705-7715`) | Tham chiếu thẻ input cũ trong lexical closure sau khi chuyển tab | Truy vấn tươi từ Active DOM qua `document.getElementById` | Có | Không | Không | Thấp | Không | Test đổi mật khẩu sau chuyển tab | **Quick Fix (P0)** |
| **FIX-SF-01** | Backend ngoại lệ tiếng Anh đè bẹp fallback tiếng Việt của Frontend | `ApiClient.request` gán `err.message` bằng raw backend string | Xây dựng `ApiClient.formatApiErrorMessage` + Bảng từ điển dịch mã lỗi | Có | Không | Không | Trung bình | `api.js` | Test hợp đồng Node.js & Pytest | **Structural Fix (P1)** |
| **FIX-SF-02** | Fallback lỗi nạp khóa học tiếng Anh (`instructor.js:3286`) | Giao diện hiển thị trực tiếp `err.message` | Thay fallback sang `'Không tìm thấy khóa học.'` | Có | Không | Không | Rất thấp | `instructor.js` | Test truy cập khóa học lạ | **Structural Fix (P1)** |
| **FIX-SF-03** | Thông báo suy thoái mạng tiếng Anh (`router.js:1417`) | Chuỗi fallback gán cứng tiếng Anh | Thay bằng `'Không thể tải dữ liệu thông báo.'` | Có | Không | Không | Rất thấp | `router.js` | Test ngắt kết nối mạng | **Structural Fix (P1)** |
| **FIX-RF-01** | Thời lượng Toast không nhất quán (2000ms - 5000ms) | Lập trình viên gán duration tùy ý | Quy chuẩn về 2 mốc chuẩn: 3500ms (thường) và 5000ms (lỗi/nguy hiểm) | Có | Không | Không | Rất thấp | `ui.js` | Audit toàn bộ 359 Toast | **Refactor (P2)** |
| **FIX-RF-02** | Ngăn xếp Toast không giới hạn gây choán màn hình | Thiếu cơ chế giới hạn số lượng Toast hiển thị | Giới hạn tối đa 3 Toast cùng lúc, Toast mới đẩy Toast cũ | Có | Không | Không | Rất thấp | `ui.js` | Test spam click Toast | **Refactor (P2)** |
| **FIX-LT-01** | Backend có 952 câu lệnh ném ngoại lệ bằng tiếng Anh | Lịch sử phát triển backend theo chuẩn quốc tế | Bổ sung lớp bản địa hóa i18n tại tầng `DOMAIN_EXCEPTION_HANDLERS` Backend | Không | Có | Không | Trung bình | `__init__.py` | Toàn bộ backend test suite | **Long-term (P3)** |
| **FIX-LT-02** | SSE / WebSocket thông báo thời gian thực cho học viên | Hiện tại đang dùng polling / fetch on route change | Nâng cấp lên Server-Sent Events khi có hạ tầng Message Queue | Có | Có | Không | Cao | Celery/Redis | Test tải đồng thời | **Long-term (P3)** |

---

## 2. LỘ TRÌNH THỰC THI 3 GIAI ĐOẠN (3-PHASE REMEDIATION ROADMAP)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LỘ TRÌNH KHẮC PHỤC 3 GIAI ĐOẠN                  │
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 1: QUICK FIXES (Ưu tiên P0 - Sửa lỗi cấp bách)                │
│ - Triệt tiêu 100% alert() & confirm() nguyên bản                       │
│ - Bản địa hóa các chuỗi Tiếng Anh hard-code ở Frontend                │
│ - Khắc phục lỗi Stale Closure DOM trong form đổi mật khẩu              │
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 2: STRUCTURAL STANDARDIZATION (Ưu tiên P1 - Chuẩn hóa lõi)   │
│ - Xây dựng ApiClient.formatApiErrorMessage & Bảng từ điển dịch mã lỗi   │
│ - Chuẩn hóa thời lượng Toast (3500ms / 5000ms)                         │
│ - Sửa lỗi mã hóa ký tự (Mojibake) trong autosave indicator             │
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 3: VERIFICATION & HARDENING (Ưu tiên P2 - Kiểm chứng & Khóa) │
│ - Viết bộ kiểm thử hồi quy Node.js (notification_ui_contract.test.js)  │
│ - Kiểm thử tương tác thực tế bằng Chrome DevTools MCP trên 4 vai trò    │
│ - Ban hành bộ tài liệu kiểm toán và rào chắn chống hồi quy             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CHI TIẾT TỪNG ĐẦU VIỆC ĐÃ HOÀN TẤT VÀ KIỂM CHỨNG

### 3.1. Nhóm Quick Fixes (Đã xong 100%)
1. **Triệt tiêu toàn bộ Hộp thoại Trình duyệt Nguyên bản:**
   - Thay `alert(msg)` tại `controllers.js:30` bằng `UI.showToast(msg, 'error')`.
   - Thay `alert('Không thể đăng ký...')` tại `controllers.js:184` bằng `UI.showToast(...)`.
   - Thay `confirm(...)` tại `controllers.js:279` bằng `await UI.confirm('Nộp bài thi khảo thí', ...)`.
   - Thay `window.confirm(...)` tại `views/instructor.js:5489` bằng `await UI.confirm('Xóa / lưu trữ khóa học', ..., true)`.
2. **Bản địa hóa các Chuỗi Tiếng Anh Hard-code:**
   - `instructor-exams.js:1130, 2067`: Đổi sang *"Vui lòng chọn ảnh định dạng PNG, JPEG, WebP hoặc GIF dung lượng dưới 5 MB."*
   - `instructor-exams.js:1136, 2071`: Đổi sang *"Vui lòng chọn khóa học trước khi thêm ảnh vào câu hỏi."*
   - `instructor-exams.js:1169, 2083`: Đổi sang *"Đã tải ảnh câu hỏi lên thành công. Ảnh sẽ hiển thị sau khi hoàn tất quét an toàn."*
   - `instructor-exams.js:2121`: Đổi sang *"Vui lòng chờ quá trình tải ảnh câu hỏi hoàn tất trước khi thêm câu hỏi này."*
   - `student.js:5063`: Đổi sang *"Không thể lưu câu trả lời điền khuyết."*
   - `instructor.js:3286`: Đổi sang *"Không tìm thấy khóa học."*
   - `router.js:1417`: Đổi sang *"Không thể tải dữ liệu thông báo."*
3. **Khắc phục Lỗi Tham chiếu Đóng biến DOM (Stale Closure):**
   - Sửa `student.js:7705-7715`: Chuyển sang truy vấn `document.getElementById` tươi trong handler `onsubmit`.
4. **Sửa lỗi mã hóa ký tự Mojibake:**
   - Sửa `student.js:5056, 5060`: Khôi phục chuỗi UTF-8 chuẩn xác.

### 3.2. Nhóm Structural Fixes (Đã xong 100%)
1. **Xây dựng `ApiClient.formatApiErrorMessage`:**
   - Triển khai từ điển `CODE_TRANSLATIONS` cho 34 mã lỗi chuẩn (`UNAUTHORIZED`, `FORBIDDEN`, `COURSE_NOT_FOUND`, `ASSESSMENT_NOT_FOUND`, `CSRF_ERROR`, v.v.).
   - Tự động nhận diện chuỗi tiếng Anh của backend để chuyển dịch sang tiếng Việt trước khi gán vào `err.message`.
   - Bảo toàn `err.code` và `err.rawMessage` cho việc debug chuyên sâu.

### 3.3. Nhóm Hardening & Testing (Đã xong 100%)
1. **Kiểm thử Hợp đồng Tự động:** Viết mới `tests/frontend/notification_ui_contract.test.js` kiểm tra không còn raw alert/confirm và xác minh logic dịch thuật của `ApiClient`.
2. **Kiểm thử Thực tế bằng Chrome DevTools MCP:** Xác minh qua 4 vai trò (`GUEST`, `STUDENT`, `INSTRUCTOR`, `ADMIN`) với bằng chứng screenshot và console logs sạch sẽ.
