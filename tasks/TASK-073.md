# TASK-073 — Instructor Course Settings & SLO Governance Redesign and Interaction Repairs

**Status:** DONE  
**Assignee:** Antigravity  

## Goal

Khắc phục triệt để và toàn diện 5 khiếm khuyết trong modal "Cài đặt & Học vụ" của Giảng viên (`InstructorView`), tinh gọn giao diện, sửa lỗi tương tác "Giải thích SLO" bằng Micro-Popover thông minh, đồng bộ nhãn giao diện và bảo toàn 100% tính toàn vẹn hệ thống.

## Preconditions

- Không làm vỡ bất kỳ workflow hay logic nào của các màn hình khác (`student`, `admin`, `api_*`).
- Không thay đổi các key dữ liệu backend (`learning_objectives`, `ApiClient.updateCourse`).
- Kiểm thử thực tế trên trình duyệt bằng `chrome-devtools-mcp` với tài khoản Giảng viên thật (`instructor1@pwd301.local`).

## In scope

1. **Làm lại popup khi ấn vào UI "Cài đặt & Học vụ" cho đẹp và gọn hơn**:
   - Chuyển đổi thanh điều hướng subtabs thành dạng **Segmented Control** hiện đại (`p-1 bg-[#F4F1EA] dark:bg-[#262524] rounded-xl`).
   - Tiêu đề modal bổ sung badge mã môn học (`course_code`) và icon tinh gọn.
   - Loại bỏ hoàn toàn lỗi **hai thanh cuộn lồng nhau** (nested double scrollbars).
   - Tối ưu khoảng cách và padding theo chuẩn Warm Editorial.
2. **Khắc phục lỗi khi ấn vào giải thích SLO không hoạt động**:
   - Phân tích root-cause: `openAcademicGlossaryModal` và `helpTooltip` nằm sai phạm vi bên trong `class FloatingAITutor` thay vì `class UI`.
   - Chuyển `UI.openAcademicGlossaryModal` và `UI.helpTooltip` vào đúng `class UI`, đồng thời giữ alias trên `FloatingAITutor` để bảo vệ các màn hình khác không bị gãy vỡ.
   - Đổi nhãn text "Giải thích SLO" thành **chỉ duy nhất icon dấu chấm hỏi (`?`)** đặt cạnh tiêu đề "1. Chuẩn đầu ra".
   - Tích hợp **Micro-Popover** xuất hiện khi **rê chuột (hover)** hoặc **bấm (click)**, kèm nút đóng và hỗ trợ click-outside.
3. **Đổi nhãn tiêu đề**:
   - `"1. Chuẩn đầu ra Môn học (Student Learning Outcomes - SLO)"` $\rightarrow$ `"1. Chuẩn đầu ra"`.
4. **Đổi nhãn nút thêm chuẩn đầu ra**:
   - `"Thêm Chuẩn đầu ra (SLO)"` $\rightarrow$ `"Thêm Chuẩn đầu ra"` (tại button và empty state).
5. **Đổi nhãn nút lưu**:
   - `"Lưu chuẩn đầu ra"` $\rightarrow$ `"Lưu"` (tại button khởi tạo và trong callback khôi phục sau khi lưu).

## Out of scope

- Thay đổi cấu trúc dữ liệu cơ sở dữ liệu MSSQL hay các endpoint API backend.
- Thay đổi các màn hình không liên quan.

## Planned & Completed changes

- `frontend/assets/js/ui.js`:
  - Khai báo trực tiếp `static helpTooltip` và `static openAcademicGlossaryModal` vào trong `class UI`.
  - Triệt tiêu lỗi runtime `TypeError: UI.openAcademicGlossaryModal is not a function`.
- `frontend/assets/js/views/instructor.js`:
  - Thiết kế lại `openCourseSettingsModal` với Segmented Control tabs, header badge và single scrollbar.
  - Cập nhật `renderTabAcademic`: tiêu đề "1. Chuẩn đầu ra", icon `?` popover trigger, nút "Thêm Chuẩn đầu ra", nút "Lưu".
  - Tích hợp logic xử lý sự kiện hover và click cho Micro-Popover giải thích SLO.
  - Đồng bộ innerHTML khôi phục của `saveSlosBtn` thành `Lưu`.
  - Tinh chỉnh `renderTabSettings` với card wrapper tối ưu tỷ lệ.

## Verification results

- **Kiểm thử trình duyệt thật (`chrome-devtools-mcp`)**:
  - Đăng nhập thực tế với `instructor1@pwd301.local` / `Password123!`.
  - Mở modal `Cài đặt & Học vụ` trên môn học `PY301`.
  - Chuyển tab sang `Chuẩn đầu ra & Học vụ`:
    - Tiêu đề hiển thị chuẩn xác: `1. Chuẩn đầu ra`.
    - Nút thêm hiển thị: `+ Thêm Chuẩn đầu ra`.
    - Nút lưu hiển thị: `Lưu`.
  - Rê chuột (hover) vào icon `?`: Micro-Popover giải thích SLO mở mượt mà.
  - Bấm (click) vào icon `?`: Popover cố định, bấm nút `close` hoặc bấm ngoài thì đóng.
  - Bấm `Thêm Chuẩn đầu ra`: số lượng thẻ tăng từ 3 lên 4.
  - Bấm `Lưu`: hiển thị toast thành công, nút hiển thị đúng nhãn `Lưu`.
  - Thử nghiệm gọi trực tiếp `UI.openAcademicGlossaryModal()`: mở sổ tay học vụ thành công 100%.
  - Chuyển đổi qua lại mượt mà giữa các tab `Cài đặt chung`, `Chuẩn đầu ra & Học vụ`, `Danh sách sinh viên`.
