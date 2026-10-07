# BỘ QUY CHUẨN THÔNG BÁO THỐNG NHẤT PWD301 (NOTIFICATION STANDARD SPECIFICATION)
**Mã tài liệu:** `04_NOTIFICATION_STANDARD.md`  
**Dự án:** PWD301 LMS & Assessment Platform  
**Phiên bản:** 1.0 (Canonical & Enforced)  
**Hiệu lực:** Bắt buộc cho toàn bộ lập trình viên, coding agent và các đợt phát triển tiếp theo.

---

## 1. MỤC ĐÍCH & PHẠM VI ÁP DỤNG

Tài liệu này xác lập **Quy chuẩn kỹ thuật và Thiết kế trải nghiệm duy nhất** cho toàn bộ hệ thống thông báo, cảnh báo, hộp thoại và trạng thái phản hồi của dự án PWD301. Mọi thành phần giao diện (Toast, Modal, Confirm, Prompt, Inline Badge, Notification Dropdown) và cấu trúc phản hồi Backend API đều bắt buộc phải tuân thủ nghiêm ngặt theo tiêu chuẩn này.

---

## 2. PHÂN LOẠI THÔNG BÁO & MỨC ĐỘ NGHIÊM TRỌNG (TAXONOMY & SEVERITY)

Hệ thống quy chuẩn thành 8 loại thông báo chức năng:

| Loại Thông báo | Biểu tượng (Material Symbol) | Bảng màu Chủ đạo (Light / Dark) | Thời lượng Mặc định | Trường hợp Sử dụng & Mục đích |
| :--- | :---: | :--- | :---: | :--- |
| **SUCCESS** | `check_circle` | Xanh ngọc lục bảo<br>`text-emerald-600` / `bg-emerald-50` | 3500ms | Thao tác người dùng đã hoàn tất thành công và dữ liệu đã được ghi nhận vào CSDL. |
| **ERROR** | `error` | Đỏ hồng lựu<br>`text-rose-600` / `bg-rose-50` | 5000ms | Thao tác thất bại hoàn toàn do lỗi mạng, lỗi máy chủ hoặc xung đột logic nghiệp vụ. |
| **WARNING** | `warning` | Vàng hổ phách<br>`text-amber-600` / `bg-amber-50` | 3500ms | Có vấn đề cần lưu ý hoặc vi phạm nhẹ (chọn sai tệp, form thiếu trường), người dùng vẫn có thể tiếp tục. |
| **INFO** | `info` | Xanh lam thanh lịch<br>`text-blue-600` / `bg-blue-50` | 3500ms | Cung cấp thông tin tiến trình, ghi nhận trạng thái hoặc thông báo phi tác vụ. |
| **CONFIRMATION** | `help` / `warning` | Modal trung tâm / Nút Primary hoặc Danger | Chờ thao tác | Yêu cầu người dùng xác nhận trước khi thực hiện hành động nguy hiểm không thể hoàn tác (Xóa, Nộp bài thi). |
| **VALIDATION** | `priority_high` | Viền đỏ inline + Text giải thích bên dưới | Theo form | Lỗi dữ liệu nhập liệu không hợp lệ. Hiển thị cục bộ ngay dưới trường nhập liệu. |
| **PERMISSION** | `lock` | Vàng hổ phách hoặc Đỏ | 5000ms | Người dùng bị từ chối truy cập do vai trò không phù hợp hoặc không sở hữu tài nguyên. |
| **SYSTEM** | `security` | Đỏ toàn màn hình (Fullscreen Modal) | Chờ xác nhận | Biến cố cấp cao nhất: Cảnh báo gian lận khảo thí, mất phiên thi hoặc vi phạm an ninh nghiêm trọng. |

---

## 3. QUY TẮC NGÔN NGỮ & BỘ TỪ VỰNG CHUẨN MỰC (GLOSSARY & TONE OF VOICE)

### 3.1. Giọng văn Chủ đạo (Tone of Voice)
- **Học thuật, Chuyên nghiệp & Lịch sự:** Sử dụng ngôi thứ nhất trang trọng ("Thầy/Cô", "Bạn", "Học viên"), xưng hô phù hợp với môi trường đại học.
- **Rõ ràng & Hướng dẫn Hành động (Action-Oriented):** Thông báo lỗi bắt buộc phải chỉ ra người dùng cần làm gì tiếp theo (ví dụ: *"Vui lòng kiểm tra lại kết nối mạng"* thay vì chỉ ghi *"Lỗi kết nối"*).
- **Tuyệt đối Cấm Thuật ngữ Kỹ thuật Thô:** Cấm đưa chuỗi UUID, mã lỗi HTTP thô (500, 404), tên tệp nội bộ, cú pháp SQL hay stack trace vào thông báo người dùng cuối.

### 3.2. Bảng Từ vựng Chuẩn mực (Canonical Vocabulary Table)

| Hành động Nghiệp vụ | CẤM DÙNG (Bị loại bỏ) | BẮT BUỘC DÙNG (Chuẩn hóa) |
| :--- | :--- | :--- |
| **Tạo mới thực thể** | Created successfully! / Đã tạo. | `Đã tạo [tên đối tượng] thành công.` |
| **Cập nhật dữ liệu** | Update success / Sửa ok. | `Đã lưu thay đổi thành công.` |
| **Xóa / Đưa vào thùng rác** | Deleted / Xóa xong. | `Đã chuyển [tên đối tượng] vào thùng rác thành công.` |
| **Đăng nhập thất bại** | Invalid credentials / Sai pass. | `Email hoặc mật khẩu không chính xác. Vui lòng kiểm tra lại.` |
| **Hết phiên đăng nhập** | Session expired / 401 Unauthorized. | `Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại để tiếp tục.` |
| **Không có quyền truy cập** | 403 Forbidden / Access denied. | `Bạn không có quyền thực hiện thao tác này.` |
| **Không tìm thấy dữ liệu** | 404 Not Found / Course not found. | `Không tìm thấy [tên đối tượng] yêu cầu trong hệ thống.` |
| **Dung lượng tệp vượt quá** | File too large / Max size exceeded. | `Kích thước tệp vượt quá giới hạn cho phép (tối đa [X] MB).` |
| **Nộp bài thi khảo thí** | Submit exam? / Nộp không? | `Xác nhận nộp bài thi khảo thí` kèm nút `Nộp bài thi` và `Tiếp tục làm bài`. |

---

## 4. QUY CHUẨN CẤU TRÚC PHẢN HỒI BACKEND REST API (CANONICAL ENVELOPE)

Backend chỉ phục vụ duy nhất định dạng JSON thuần túy (Pure Headless):

### Phản hồi Thành công (Success Envelope):
```json
{
  "success": true,
  "message": "Cập nhật thông tin khóa học thành công.",
  "data": {
    "course_id": "5da5cfbc-28a5-4db8-a478-f634676f2c67",
    "updated_at": "2026-10-06T13:10:00Z"
  }
}
```

### Phản hồi Thất bại (Error Envelope):
```json
{
  "success": false,
  "error": {
    "code": "ACTIVE_LEASE_EXISTS",
    "message": "Bài thi đang được mở ở một phiên làm việc khác.",
    "details": {
      "active_session_id": "sess_xyz...",
      "expires_at": "2026-10-06T13:15:00Z"
    }
  }
}
```

---

## 5. BẢN ĐỒ DỊCH MÃ LỖI TẬP TRUNG TẠI CLIENT (`ERROR_CODE_MAP`)

Mọi phản hồi lỗi từ `ApiClient.request` đều đi qua hàm định dạng `ApiClient.formatApiErrorMessage` với bộ từ điển chuẩn:

```javascript
const ERROR_CODE_TRANSLATIONS = {
  'UNAUTHORIZED': 'Phiên làm việc đã hết hạn hoặc chưa đăng nhập.',
  'INVALID_CREDENTIALS': 'Email hoặc mật khẩu không chính xác.',
  'FORBIDDEN': 'Bạn không có quyền thực hiện thao tác này.',
  'CSRF_ERROR': 'Phiên bảo mật đã hết hạn. Vui lòng thử lại.',
  'NOT_FOUND': 'Không tìm thấy dữ liệu yêu cầu.',
  'RESOURCE_NOT_FOUND': 'Không tìm thấy tài nguyên yêu cầu trong hệ thống.',
  'COURSE_NOT_FOUND': 'Không tìm thấy khóa học.',
  'ASSESSMENT_NOT_FOUND': 'Không tìm thấy bài thi khảo thí.',
  'USER_NOT_FOUND': 'Không tìm thấy thông tin người dùng.',
  'VALIDATION_ERROR': 'Dữ liệu đầu vào không hợp lệ. Vui lòng kiểm tra lại.',
  'BAD_REQUEST': 'Yêu cầu không hợp lệ.',
  'CONFLICT': 'Dữ liệu bị trùng lặp hoặc xung đột trạng thái.',
  'ALREADY_EXISTS': 'Dữ liệu đã tồn tại trong hệ thống.',
  'RATE_LIMIT_EXCEEDED': 'Bạn đã thao tác quá nhanh. Vui lòng thử lại sau giây lát.',
  'INTERNAL_ERROR': 'Lỗi máy chủ nội bộ. Vui lòng thử lại sau.',
  'INTERNAL_SERVER_ERROR': 'Lỗi máy chủ nội bộ. Vui lòng thử lại sau.',
  'FILE_TOO_LARGE': 'Kích thước tệp vượt quá giới hạn cho phép.',
  'INVALID_FILE_TYPE': 'Định dạng tệp không được hỗ trợ.',
  'SCAN_FAILED': 'Quét tệp an toàn thất bại.',
  'ATTEMPT_LOCKED': 'Bài thi đã bị khóa hoặc hết thời gian làm bài.',
  'ACTIVE_LEASE_EXISTS': 'Bài thi đang được mở ở một phiên làm việc khác.'
};
```

---

## 6. QUY CHUẨN THIẾT KẾ UI/UX 3 TẦNG IMPECCABLE (3-TIER INVARIANTS)

### 6.1. Tầng 1: Bộ 5 Định luật Nhận thức (Cognitive Invariants)
1. **Jakob's Law:** Không dùng các hộp thoại lạ mắt gây bối rối. Nút [X] luôn ở góc trên phải; phím `Escape` luôn đóng modal; nút Primary luôn ở bên phải, nút Hủy (Secondary) ở bên trái.
2. **Hick's Law:** Mỗi thông báo chỉ yêu cầu tối đa 01 hành động chính. Trong modal xác nhận chỉ có 02 nút bấm: Hành động chính (Xác nhận/Xóa) và Hành động phụ (Hủy).
3. **Law of Proximity:** Khoảng cách giữa các phần tử phản ánh logic: Khoảng cách Icon badge -> Text: 12px; Text -> Nút Close: 16px; Nội dung -> Nút hành động: 24px.
4. **Miller's Law:** Thông báo lỗi form chia theo từng cụm trường thông tin (Chunking), không dồn dập quá 5 thông báo cùng lúc.
5. **Von Restorff Effect:** Hành động nguy hiểm bắt buộc làm nổi bật duy nhất bằng màu Đỏ nguy hiểm (`bg-rose-600 hover:bg-rose-700`), nút Hủy dùng màu nền trung tính viền mờ.

### 6.2. Tầng 2: Quy chuẩn Kỹ thuật Đo lường (Metric Invariants)
- **Tỷ lệ đệm nút bấm 2:1:** $Padding_X = 2 \times Padding_Y$ (ví dụ: `py-2.5 px-5`, `py-2 px-4`).
- **Màu sắc & Tương phản WCAG AA:** Tuyệt đối không dùng Pure Black (`#000000`) hay Pure White (`#ffffff`); sử dụng màu nền ấm `#FAF9F5` (Light) và `#202020` (Dark), viền `#E8E6DF` / `#2E2D2B`. Đảm bảo độ tương phản tối thiểu 4.5:1.
- **Bo góc lồng nhau (Nested Radius):** $Radius_{inner} = Radius_{outer} - Padding$. Khung ngoài `rounded-2xl` (16px), phần tử con bên trong `rounded-xl` (12px) hoặc `rounded-lg` (8px).

### 6.3. Tầng 3: Vòng đời & Tương tác Toast
- **Ngăn xếp (Stacking):** Tối đa 3 Toast hiển thị đồng thời; Toast thứ 4 tự động đẩy Toast cũ nhất biến mất.
- **Thanh tiến trình (Progress Bar):** Chạy mượt mà từ 100% về 0% theo đúng `duration` thiết lập.
- **Khả năng tiếp cận (Accessibility):** Thẻ thông báo được gắn thuộc tính ARIA: `role="alert"` và `aria-live="polite"` (cho Toast thường) hoặc `aria-live="assertive"` (cho Toast lỗi nghiêm trọng).
