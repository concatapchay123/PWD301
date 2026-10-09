# Tuyên Bố Mục Tiêu (Statement of Intent): Hệ Thống Bảo Vệ Bản Quyền & Chống Gian Lận (TASK-085)

Tài liệu này là nguồn sự thật (Source of Truth) xác lập mục tiêu, phạm vi và ranh giới bất biến cho hệ thống Bảo Vệ Bản Quyền & Chống Can Thiệp Mã Nguồn của nền tảng PWD301, được thống nhất và phê duyệt qua phiên phỏng vấn `/grill-me` ngày 07/10/2026.

---

## 1. Bản Tuyên Bố Mục Tiêu (Statement of Intent)

* **Outcome (Kết quả)**: Xây dựng hệ thống bảo vệ bản quyền và chống gian lận đa tầng cho PWD301 kết hợp: **Mã hóa luồng phân mảnh HLS (AES-128)**, **Thủy ấn động pháp chứng (Dynamic Forensic Watermark)**, **Lớp giáp chống can thiệp Client (Client Armor & DevTools Bouncer)**, và **Kiểm soát tiến độ Zero-Trust Máy chủ (Server-Authoritative Wall-Clock Heartbeat)**.
* **User (Người thụ hưởng)**: Giảng viên, Nhà trường và Quản trị viên (bảo vệ quyền sở hữu trí tuệ bài giảng và đảm bảo tính liêm chính học thuật).
* **Why now (Lý do)**: Triệt tiêu nguy cơ học viên tải lậu trực tiếp video MP4 thô, dùng phần mềm quay trộm bài giảng không để lại dấu vết, hoặc dùng DevTools/Extension can thiệp mã nguồn để bypass thời lượng xem và hoàn thành khóa học ảo.
* **Success (Tiêu chí thành công)**:
  1. Học viên không thể lấy link tải trực tiếp file video thô; luồng phát nội bộ được phân mảnh và mã hóa.
  2. Mọi màn hình phát video (cả video nội bộ và YouTube) đều có thủy ấn định danh học viên (`MSSV - Email - IP - Timestamp`) trôi ngẫu nhiên, không thể xóa hoặc crop mà không làm hỏng video.
  3. Khi có hành vi can thiệp DOM (xóa Watermark), mở DevTools (F12) hoặc rời cửa sổ, trình phát tự động kích hoạt **Blackout (màn hình đen)**, tạm dừng video và ghi nhận sự kiện kiểm toán (`AuditEvent`).
  4. Mọi nỗ lực gửi payload gian lận tiến độ đều bị máy chủ từ chối 100% nếu thiếu chuỗi nhịp tim (Heartbeat) xác thực thời gian xem thực tế.
* **Constraint (Ràng buộc cứng)**: Chạy hoàn toàn trên Web Browser tiêu chuẩn (Chrome, Edge, Firefox), giữ vững kiến trúc Pure Headless REST API của PWD301, không làm chậm trải nghiệm học tập của người dùng trung thực.
* **In-Scope Bắt buộc (TASK-087)**: Tích hợp YouTube Headless Stream API, triệt tiêu 100% controls mặc định của YouTube (`controls=0`, ẩn logo, ẩn nút "Watch on YouTube") và thay thế bằng PWD301 Custom Video Player Shell với thanh điều khiển Flat Editorial độc quyền.
* **Out of scope (Nằm ngoài phạm vi)**: Không cam kết chặn được các thiết bị quay phần cứng vật lý (camera ngoài, card capture HDMI rời) ngoài việc dùng watermark pháp chứng để truy vết và xử lý kỷ luật tài khoản vi phạm.

---

## 2. Bất Biến Thanh Trừng Toàn Diện (Purge & Decommissioning Invariant)

Mọi coding agent trong hiện tại và tương lai BẮT BUỘC tuân thủ:
1. **Bãi bỏ phân phối MP4 thô & Lưu trữ cục bộ trên VPS**: Video bài học nội bộ không bao giờ được trả về trực tiếp dưới dạng file tải về cho học viên qua `/student/files/<id>/download`. Nghiêm cấm lưu trữ video thô đa gigabyte trực tiếp trên ổ cứng VPS mà phải sử dụng kiến trúc phân mảnh HLS hoặc Headless Video Stream (YouTube Unlisted).
2. **Bãi bỏ Iframe YouTube Thô**: Mọi luồng video YouTube BẮT BUỘC bọc trong PWD301 Custom Player Shell; nghiêm cấm để lộ thanh điều khiển hay logo mặc định của YouTube.
3. **Triệt tiêu lỗ hổng nhảy cóc tiến độ**: Nghiêm cấm mọi logic tự động gán `seconds_spent = minimum_completion_seconds` chỉ vì client gửi `view_fraction >= 0.90`. Mọi tiến độ hoàn thành bài học bắt buộc tích lũy thời gian thực tế qua chuỗi nhịp tim (Heartbeat) kiểm tra Wall-Clock Time.
4. **Thủy ấn động bất biến**: Lớp phủ thủy ấn không được phép ẩn hoặc xóa. Mọi hành vi can thiệp DOM vào thẻ Watermark đều phải bị `MutationObserver` phát hiện và kích hoạt màn hình đen bảo vệ ngay lập tức.
