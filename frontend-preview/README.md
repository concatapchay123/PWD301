# PWD301 — Frontend Prototype Demo

Bản demo giao diện người dùng hoàn chỉnh cho hệ thống **PWD301 — Online Course Management Platform**, được thiết kế theo triết lý **Functional Minimalism** và quy chuẩn thiết kế sản phẩm SaaS giáo dục hiện đại.

---

## 1. Hướng dẫn Khởi chạy (Cách chạy nhanh nhất trên Windows)

Bản prototype hoạt động hoàn toàn bằng tĩnh (HTML5, Bootstrap 5, CSS3, Vanilla JavaScript), không yêu cầu cài đặt Node.js hay bất kỳ backend Flask / database nào.

### Cách 1: Sử dụng Python Static Server (Khuyến nghị)
Mở PowerShell hoặc Command Prompt tại thư mục dự án:
```powershell
python -m http.server 5500 -d frontend-preview
```
Sau đó mở trình duyệt truy cập:
👉 **[http://localhost:5500](http://localhost:5500)**

### Cách 2: Sử dụng VS Code Live Server hoặc mở trực tiếp
Bạn cũng có thể click chuột phải vào file `frontend-preview/index.html` chọn **Open with Live Server** hoặc mở trực tiếp trong trình duyệt hiện đại (Chrome, Edge, Firefox).

---

## 2. Kiến trúc Kỹ thuật (Frontend Architecture)

```text
frontend-preview/
├── index.html                  # Master AppShell, Topbar, Sidebar, Offcanvas, Toast & Outlet
├── README.md                   # Hướng dẫn chạy và tài liệu kịch bản demo
└── assets/
    ├── css/
    │   └── app.css             # Design tokens, typography hierarchy, 8px spacing, buttons, forms
    ├── vendor/
    │   ├── bootstrap.min.css   # Bootstrap 5.3.3 core styling
    │   └── bootstrap.bundle.min.js # Bootstrap 5.3.3 components
    └── js/
        ├── components.js       # SVG icons, PageHeader, StatCard, Badge, Toast, Defensive Modals
        ├── store.js            # Central Mock Store, seed personas, reactive mutations, local persistence
        ├── router.js           # Hash-based SPA Router (URL hash matching, route parameters)
        ├── views/
        │   ├── public.js       # Catalog, Course Detail, Login, Register, Forgot Password
        │   ├── student.js      # Dashboard, Course Learning, Lesson Reader, Attempt Engine, Results, AI
        │   ├── instructor.js   # Authoring, Question Bank, Assessment Builder, Import, Grading, Analytics
        │   └── admin.js        # Governance, User suspension, Course review, Security center, Audit, Health
        └── app.js              # Application controller, perspective switcher, sidebar sync
```

---

## 3. Triết lý Thiết kế: Functional Minimalism & Anti-AI-Slop

1. **Một Primary Action rõ ràng trên mỗi màn hình:** Không cạnh tranh thị giác bằng 5 nút cùng màu.
2. **Không Card-trong-Card, không Dashboard quá tải:** Chỉ hiển thị 3 chỉ số KPI cốt lõi phục vụ hành động tiếp theo, không đặt các biểu đồ giả để lấp khoảng trống.
3. **Màu sắc & Phông chữ có kiểm soát:**
   - Gam màu học thuật chủ đạo: Deep Academic Navy (`#1E3A8A`) kết hợp bảng Slate trung tính.
   - Tránh hoàn toàn gradient lòe loẹt, hiệu ứng neon, glassmorphism hay bóng đổ nặng.
4. **Defensive UX (Chống thao tác nhầm):**
   - Các hành động phá hủy / nhạy cảm (Tạm ngưng tài khoản, Phục hồi sao lưu) bắt buộc:
     - Nhập mật khẩu quản trị viên xác thực lại
     - Gõ chính xác cụm từ xác nhận viết hoa (Exact phrase confirmation)
     - Nhập lý do thực hiện bắt buộc (Lưu vết kiểm toán)
   - Tự động khóa cấu hình thời gian khi bài thi đã xuất bản (Invariant 13).
   - Tự động khóa cấu trúc câu hỏi và thang điểm khi sinh viên đã bắt đầu thi (Invariant 14).

---

## 4. Chế độ Xem Demo (Perspective Switcher)

Ở thanh thông báo trên cùng của trang web hoặc menu chọn góc nhìn tại Topbar:
- **Khách vãng lai (Public):** Xem danh mục khóa học, chi tiết môn học, form đăng nhập / đăng ký.
- **Sinh viên (Nguyễn Minh Anh):** Trải nghiệm hành trình học tập, đọc bài giảng, làm bài thi trực tiếp với bộ đếm giờ, lưu đáp án tự động, kiểm tra mất mạng (Offline) và tranh chấp phiên (Lease lost).
- **Giảng viên (Trần Hoàng Nam):** Quản lý khóa học, soạn bài giảng, ngân hàng câu hỏi (Revision History), tạo đề thi, import đề Word/PDF, AI sinh câu hỏi, chấm bài tự luận.
- **Quản trị viên (Lê Thu Hà):** Kiểm duyệt khóa học, quản trị người dùng, khóa tài khoản, giám sát sự kiện bảo mật & AI prompt-injection, xem Audit Log bất biến, sao lưu và phục hồi hệ thống.

---

## 5. Hướng dẫn Thử nghiệm 12 Kịch bản Nghiệp vụ (Demo Scenarios)

1. **Kịch bản 1 — Hành trình sinh viên:** Đăng nhập Sinh viên -> Khóa học của tôi -> Chọn môn PWD301 -> Đọc bài giảng 4 -> Đánh dấu hoàn thành -> Vào làm bài kiểm tra giữa kỳ -> Chọn đáp án -> Nộp bài -> Xem trang đã nộp và thông báo chờ chấm tự luận.
2. **Kịch bản 2 — Khóa học bị chặn do thiếu môn tiên quyết:** Vào *Khám phá khóa học* -> Chọn môn *Cơ sở dữ liệu Nâng cao (DBA201)* -> Xem cảnh báo bị chặn vì chưa hoàn thành môn PWD301 -> Bấm vào liên kết dẫn đến môn PWD301.
3. **Kịch bản 3 — Làm bài thi trong điều kiện Mất mạng (Offline):** Vào màn hình làm bài thi (`#/student/attempt/a1`) -> Bấm nút demo `Đang có mạng` chuyển thành `Đang mất mạng (Offline)` -> Thay đổi câu trả lời -> Quan sát trạng thái chuyển thành `⚠ Chưa đồng bộ` -> Bấm kết nối lại mạng -> Hệ thống tự động reconcile và hiện `✓ Đã lưu câu trả lời`.
4. **Kịch bản 4 — Xung đột phiên làm bài thi (Lease Lost / Takeover):** Tại màn hình làm bài thi, bấm nút `Giữ quyền làm bài` chuyển thành `Bị mất quyền (Lease Lost)` -> Biểu mẫu trắc nghiệm bị vô hiệu hóa -> Bấm nút `Chiếm lại phiên (Takeover)` -> Khôi phục quyền làm bài ngay lập tức.
5. **Kịch bản 5 — Giảng viên quản lý bài học:** Đổi sang Giảng viên -> Chọn *Khóa học của tôi* -> Bấm *Bài giảng* môn PWD301 -> Dùng nút mũi tên để đổi thứ tự bài giảng -> Bấm *Sửa nội dung* để chỉnh sửa bài học.
6. **Kịch bản 6 — Ngân hàng câu hỏi & Lịch sử phiên bản:** Vào *Ngân hàng câu hỏi* -> Bấm *Sửa* một câu hỏi đang được sử dụng trong đề thi -> Hệ thống cảnh báo tự động tăng Revision lên v2 -> Nhập lý do điều chỉnh -> Lưu câu hỏi -> Bấm xem *Lịch sử* để đối chiếu v1 và v2.
7. **Kịch bản 7 — Khóa cấu hình đề thi:** Vào *Bài kiểm tra & Đề thi* -> Chọn đề thi PWD301 Giữa kỳ -> Thử đổi trạng thái demo giữa Draft / Published / Student Started -> Quan sát các trường thời gian và cấu trúc câu hỏi bị khóa theo đúng Invariant 13 & 14.
8. **Kịch bản 8 — Import tài liệu & AI sinh câu hỏi:**
   - Vào *Import DOCX/PDF* -> Bấm chọn tệp mẫu -> Xem tiến trình parse và màn hình xem xét câu hỏi (Độ tin cậy cao / Cần xem lại / Trùng lặp).
   - Vào *AI sinh câu hỏi* -> Chọn bài học ngữ cảnh -> Bấm sinh bản thảo -> Thử nghiệm các nút Duyệt lưu (Keep), Sửa (Edit), Bỏ qua (Reject).
9. **Kịch bản 9 — Giảng viên chấm bài tự luận & Phúc khảo:** Vào *Hàng đợi chấm luận* -> Mở bài làm của học viên Nguyễn Minh Anh -> Nhập điểm và nhận xét -> Lưu điểm -> Theo dõi tiến trình chấm lại (Regrade Job) hoàn tất 100%.
10. **Kịch bản 10 — Quản trị viên khóa tài khoản bảo mật:** Đổi sang Quản trị viên -> Vào *Quản lý người dùng* -> Bấm *Khóa tài khoản* của một người dùng -> Nhập mật khẩu xác thực + gõ chính xác cụm từ `TẠM NGƯNG TÀI KHOẢN` + nhập lý do -> Bấm xác nhận -> Vào *Nhật ký Audit Log* kiểm tra bản ghi vừa tạo.
11. **Kịch bản 11 — Chuyển quyền quản lý khóa học:** Vào Quản trị -> Bấm *Chuyển quyền khóa học* -> Chọn môn học, chọn giảng viên mới và nhập lý do bắt buộc -> Bấm chuyển quyền -> Kiểm tra thông tin đã cập nhật.
12. **Kịch bản 12 — Giám sát hạ tầng & Phục hồi sao lưu:** Vào *Sức khỏe dịch vụ* -> Thử bật mô phỏng Scanner bị suy giảm (Degraded) -> Vào *Sao lưu & Phục hồi* -> Tạo bản sao lưu mới -> Bấm *Phục hồi dữ liệu* -> Hộp thoại cảnh báo bảo mật yêu cầu gõ `KHÔI PHỤC DỮ LIỆU` xuất hiện để ngăn chặn bấm nhầm.

---

## 6. Đặt lại Dữ liệu Demo (Reset Demo Data)

Bất kỳ lúc nào, bạn có thể bấm nút **"Đặt lại demo"** ở góc trên cùng bên phải hoặc trong menu Cài đặt (`#/admin/settings`) để xóa sạch các thay đổi tạm và khôi phục toàn bộ kho dữ liệu về trạng thái mẫu chuẩn ban đầu.
