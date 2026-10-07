# PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ HỆ THỐNG THÔNG BÁO (ROOT CAUSE ANALYSIS)
**Mã tài liệu:** `03_NOTIFICATION_ROOT_CAUSE_ANALYSIS.md`  
**Dự án:** PWD301 LMS & Assessment Platform  
**Phương pháp:** 4-Giai đoạn Truy vết Lỗi (Systematic Debugging Protocol) & Phân tích Chuỗi Nhân Quả (Five Whys)  
**Tác giả:** Đội ngũ Kỹ sư Trưởng PWD301

---

## 1. TỔNG QUAN HỆ THỐNG VẤN ĐỀ

Qua đợt kiểm toán Phase 1 & 2, hệ thống ghi nhận hàng loạt biểu hiện bất thường trên giao diện:
- Thông báo xuất hiện bằng tiếng Anh xen lẫn tiếng Việt.
- Lỗi kết nối làm hiện chuỗi raw error kỹ thuật.
- Người dùng bị chặn bởi các hộp thoại `alert` / `confirm` đơ giao diện.
- Form đổi mật khẩu báo lỗi dù đã điền đúng dữ liệu.

Áp dụng quy tắc lập trình chuẩn mực và debug có phương pháp, chúng tôi khẳng định: **Đây không phải là lỗi gõ chữ (typo) riêng lẻ, mà xuất phát từ 6 lỗ hổng kiến trúc và logic gốc rễ (Root Causes - RC).**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        KIẾN TRÚC THÔNG BÁO PWD301                      │
├────────────────────────────────┬───────────────────────────────────────┤
│ BACKEND SERVICES & BLUEPRINTS │ REST API RESPONSE                     │
│ - 952 thông điệp Tiếng Anh    │ { success: false,                     │
│ - 190 thông điệp Tiếng Việt   │   error: { code: "...", message: "..."}│
└───────────────┬────────────────┴───────────────────┬───────────────────┘
                │                                    │
                ▼                                    ▼
       [RC-1: LỖI KIẾN TRÚC]               [RC-2: RAW DIALOGS]
       ApiClient gán err.message           alert() & confirm()
       đè bẹp Tiếng Việt fallback          đóng băng UI thread
                │                                    │
                ├────────────────────────────────────┤
                │                                    ▼
                ▼                          [RC-4: STALE CLOSURE]
       [RC-3: HARDCODE TIẾNG ANH]          Tham chiếu DOM cũ
       Chuỗi rải rác trong file SPA        làm sai lệch form validation
                │                                    │
                └─────────────────┬──────────────────┘
                                  ▼
                         [GIAO DIỆN NGƯỜI DÙNG]
                         UI.showToast() & UI.openModal()
```

---

## 2. CHI TIẾT 6 NGUYÊN NHÂN GỐC RỄ (THE 6 ROOT CAUSES)

---

### RC-1: Kiến trúc Phân mảnh Ngôn ngữ & Thiếu Bộ Từ điển Chuyển đổi Mã lỗi (Architectural Language Mismatch & Missing Error Code Translation Catalog)

#### 1. Cơ chế phát sinh (Mechanism):
- Tại tầng Backend: Toàn bộ 11 gói dịch vụ (`src/pwd301/services/`) được viết theo chuẩn kỹ thuật quốc tế với **952 câu lệnh ném ngoại lệ bằng Tiếng Anh** (chiếm 81.8% tổng số ngoại lệ), ví dụ: `ResourceNotFoundError("Course '...' not found.")`, `ValidationError("Admin direct edits to an Instructor-owned course require a reason.")`.
- Tại bộ lọc ngoại lệ `src/pwd301/__init__.py`: Ngoại lệ được đóng gói vào JSON envelope:
  ```json
  {
    "success": false,
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "Course '5da5cfbc-...' not found."
    }
  }
  ```
- Tại tầng Client HTTP `frontend/assets/js/api.js`: Phương thức `ApiClient.request` nhận phản hồi và khởi tạo:
  ```javascript
  const errorMsg = (data && data.error && data.error.message) || data.message || `Lỗi HTTP ${res.status}`;
  const err = new Error(errorMsg);
  throw err;
  ```
- Tại các tầng Views (`student.js`, `instructor.js`, `admin.js`): Lập trình viên bắt lỗi và hiển thị:
  ```javascript
  UI.showToast(err.message || 'Lỗi nạp dữ liệu khóa học.', 'error');
  ```

#### 2. Điểm nghẽn cốt lõi (Root Cause):
Vì `err.message` luôn mang giá trị chuỗi tiếng Anh có sẵn từ Backend (`"Course not found."`), toán tử logic `||` đánh giá vế trái là *truthy*. Kết quả là **chuỗi dự phòng Tiếng Việt ở vế phải vĩnh viễn không bao giờ được kích hoạt**, trực tiếp rò rỉ nguyên văn câu chữ kỹ thuật tiếng Anh của Backend lên màn hình học viên và giảng viên.

#### 3. Giải pháp triệt để:
Bổ sung phương thức `ApiClient.formatApiErrorMessage` tích hợp bảng từ điển `CODE_TRANSLATIONS` tại trung tâm xử lý HTTP. Tự động kiểm tra: Nếu chuỗi không chứa ký tự tiếng Việt và có mã lỗi định danh (hoặc cụm từ tiếng Anh phổ biến), chuỗi sẽ được chuyển hóa thành Tiếng Việt học thuật chuẩn mực trước khi ném ra ngoài.

---

### RC-2: Vi phạm Bất biến Giao diện với Hộp thoại Trình duyệt Nguyên bản (Raw Browser Dialog Invariant Violations)

#### 1. Cơ chế phát sinh:
- Quét AST phát hiện 4 điểm gọi trực tiếp hàm nguyên bản của Web Browser:
  - `frontend/assets/js/controllers.js:30`: `alert(msg);`
  - `frontend/assets/js/controllers.js:184`: `alert('Không thể đăng ký: ' + e.message);`
  - `controllers.js:279`: `const confirmed = confirm('Bạn có chắc chắn muốn nộp bài thi khảo thí này không?...');`
  - `frontend/assets/js/views/instructor.js:5489`: `const confirmed = window.confirm(...);`

#### 2. Tác hại nghiêm trọng:
1. **Đóng băng luồng thực thi (UI Thread Freezing):** Hàm `window.alert` và `window.confirm` là lời gọi đồng bộ (blocking call). Chúng tạm dừng toàn bộ bộ đếm thời gian (timer) của bài thi và ngắt các luồng WebSocket / Server-Sent Events.
2. **Phá vỡ định luật Jakob's Law & Impeccable Design:** Hộp thoại của hệ điều hành/trình duyệt có giao diện màu xám cơ học, không kế thừa bảng màu Warm Editorial, không hỗ trợ Dark Mode, không có icon badge và tỷ lệ nút bấm thô kệch.
3. **Mù khả năng tự động hóa kiểm thử (Anti-Automation):** Các bộ test headless (Playwright, Puppeteer, Chrome DevTools MCP) có thể bị treo vô hạn nếu gặp dialog ngoài ý muốn.

#### 3. Giải pháp triệt để:
Loại bỏ 100% `alert()` và `confirm()`, thay thế bằng `UI.alert()` và `UI.confirm()`. Cả hai đều trả về `Promise<boolean>`, chạy bất đồng bộ hoàn toàn và render trực tiếp trong DOM nội tại của ứng dụng.

---

### RC-3: Chuỗi Thông báo Tiếng Anh Bị Gán Cứng ở Frontend (Hardcoded Pure English Notification Strings)

#### 1. Cơ chế phát sinh:
Trong các luồng mới được phát triển nhanh (Soạn đề thi tương tác, Autosave câu hỏi điền khuyết), lập trình viên đã chép mã nguồn mẫu từ tài liệu tiếng Anh mà không qua bước chuẩn hóa ngôn ngữ:
- `instructor-exams.js:1130 & 2067`: `'Choose a PNG, JPEG, WebP, or GIF image smaller than 5 MB.'`
- `instructor-exams.js:1136 & 2071`: `'Choose a course before adding an image to a question.'`
- `instructor-exams.js:1169 & 2083`: `'Question image uploaded. It will appear after the security scan completes.'`
- `instructor-exams.js:2121`: `'Wait for the question image upload to finish before adding this question.'`
- `student.js:5063`: `UI.showToast(error.message || 'Could not save the blank answers.', 'error');`
- `router.js:1417`: `message: error?.message || 'Notification data is unavailable.'`

#### 2. Điểm nghẽn cốt lõi:
Sự thiếu vắng bài kiểm tra hồi quy tự động (Regression Linter) để quét các chuỗi ký tự không dấu trong các lệnh gọi `UI.showToast`.

#### 3. Giải pháp triệt để:
Thay thế toàn bộ chuỗi trên sang Tiếng Việt học thuật và thiết lập test case `tests/frontend/notification_ui_contract.test.js` để tự động hóa việc phát hiện chuỗi ngoại lai.

---

### RC-4: Lỗi Tham chiếu Đóng Biến DOM Cũ trong Form Động (Stale Closure DOM Reference Bug)

#### 1. Cơ chế phát sinh:
Tại màn hình Cài đặt học viên `frontend/assets/js/views/student.js:7653-7715`:
```javascript
// Khởi tạo biến đóng ngoài hàm submit
const newPwdInput = container.querySelector('#settings-new-password');
const confPwdInput = container.querySelector('#settings-conf-password');

// Bên trong hàm submit
passwordForm.onsubmit = async (e) => {
  e.preventDefault();
  const currInput = container.querySelector('#settings-curr-password');
  const currVal = currInput ? currInput.value : '';
  const newVal = newPwdInput ? newPwdInput.value : ''; // <- BIẾN ĐÓNG CŨ
  const confVal = confPwdInput ? confPwdInput.value : ''; // <- BIẾN ĐÓNG CŨ
  if (!currVal) {
    UI.showToast('Vui lòng nhập mật khẩu hiện tại.', 'warning');
    return;
  }
};
```

#### 2. Điểm nghẽn cốt lõi:
Khi học viên chuyển qua lại giữa các tab "Hồ sơ" và "Bảo mật", hàm `renderSettings` vẽ lại giao diện DOM. Các thẻ `<input>` cũ bị ngắt kết nối (`detached`). Trong khi `currInput` được truy vấn tươi qua `container.querySelector`, thì `newVal` và `confVal` lại tham chiếu tới `newPwdInput` bị kẹt trong closure từ lần render trước. Kết quả là giá trị `.value` luôn là chuỗi rỗng `""`, kích hoạt các Toast cảnh báo sai lệch một cách khó hiểu.

#### 3. Giải pháp triệt để:
Truy vấn trực tiếp thẻ DOM đang hoạt động bằng `document.getElementById('settings-curr-password')`, `document.getElementById('settings-new-password')` ngay tại thời điểm sự kiện `submit` diễn ra.

---

### RC-5: Thời lượng & Phân cấp Thị giác Không Nhất quán (Inconsistent Durations & Severity Hierarchy)

#### 1. Cơ chế phát sinh:
Tại 359 điểm gọi `UI.showToast`, tham số `duration` bị gán tùy tiện: `2000`, `2500`, `3000`, `3500`, `4000`, `5000`. Một số thông báo lỗi nghiêm trọng lại biến mất sau 2 giây khiến người dùng chưa kịp đọc lý do; ngược lại, các thông báo thao tác nhỏ nhặt lại tồn tại đến 5 giây gây choán góc màn hình.

#### 2. Giải pháp triệt để:
Quy chuẩn hóa thời lượng Toast toàn hệ thống thành 2 mốc duy nhất:
- **Chuẩn thông thường (Normal / Success / Info / Warning):** `3500ms`.
- **Nghiêm trọng (Critical / Error / System Failure):** `5000ms`.

---

### RC-6: Kích hoạt Trùng lặp do Thiếu Khóa Chặn Bất đồng bộ (Duplicate Triggers & Missing Mutex)

#### 1. Cơ chế phát sinh:
Khi bấm nút "Nộp bài", "Lưu giáo trình" hoặc tải tệp lên trong điều kiện mạng lag, nếu không khóa trạng thái `disabled = true` ngay lập tức, người dùng thường có xu hướng nhấp chuột liên tục (rapid clicking). Điều này kích hoạt nhiều request đồng thời, sinh ra nhiều Toast xếp chồng che kín màn hình.

#### 2. Giải pháp triệt để:
Áp dụng cờ `isSubmitting` hoặc vô hiệu hóa nút bấm ngay đầu handler, hiển thị trạng thái xoay vi mô (Micro-loading Spinner: `Đang lưu...`), ngăn chặn 100% việc gửi request và hiển thị thông báo trùng lặp.
