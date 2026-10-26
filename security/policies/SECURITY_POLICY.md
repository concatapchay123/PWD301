# CHÍNH SÁCH AN NINH & BẢO MẬT HỆ THỐNG PWD301 (PPTQ LMS)

## 1. Bảo mật Truyền thông Hai Tầng (Two-Tier In-Transit Cryptography)
- Mọi gói tin nhạy cảm (đăng nhập, đăng ký) được mã hóa tại Client bằng Web Crypto API trước khi truyền qua mạng.
- Thuật toán mã hóa lai: Khóa phiên AES-GCM 256 dùng 1 lần được bọc bằng khóa công khai RSA-OAEP 2048 (SHA-256) của Server.
- Phong bì dữ liệu mạng mang định dạng bắt buộc:
  ```json
  {
    "prefix": "PPTQ LMS",
    "encrypted_key": "<rsa_encrypted_aes_key_base64>",
    "iv": "<aes_iv_base64>",
    "ciphertext": "<aes_ciphertext_base64>",
    "timestamp": 1729951234
  }
  ```
- Cơ chế chống tấn công phát lại (Anti-Replay Protection): Server từ chối mọi request có độ lệch thời gian > 60 giây.

## 2. Bảo mật Dữ liệu Tĩnh CSDL Cục Bộ (At-Rest Database Encryption)
- Mật khẩu người dùng: Argon2id chuẩn hóa cá nhân hóa:
  `PPTQ LMS$argon2id$v1$<salt_base64>$<hash_base64>`
- Email và Display Name trong bảng `users`: Mã hóa mức trường (Field-Level Encryption) với AES-256-CBC:
  `PPTQ LMS$aes256$v1$<iv_base64>$<ciphertext_base64>`
- Tìm kiếm $O(1)$ trên cột `email` được duy trì bằng IV tiền định HMAC-SHA256 bí mật, bảo toàn tính toàn vẹn Unique.

## 3. Lớp Giáp Bảo Vệ Nội Dung Học Tập (Video Armor & DRM)
- Video bài giảng được phân giải qua HLS nội bộ có khóa giải mã động (DRM token) thời hạn 12 giờ gắn liền với phiên đăng nhập của học viên.
- Trình phát YouTube bảo toàn tỷ lệ 16:9 responsive không crop viền, che chắn bằng Poster Backdrop Shield trước khi người dùng click phát.
- Chế độ Tua An Toàn (5-Second Seek Unlock): Khóa tua vượt quá điểm đang xem, chỉ tự động mở khóa tự do toàn bộ video khi học viên xem đến 5 giây cuối cùng (currentTime >= Duration - 5s).

## 4. Cơ chế Chống Gian lận Thi cử (Exam Anti-Cheat Shield)
- Giám sát trạng thái mất tiêu điểm cửa sổ (`window.onblur`, `visibilitychange`, `document.hidden`).
- Khi phát hiện mất focus (Alt-Tab, Snipping Tool, OBS, chuyển ứng dụng), màn hình lập tức kích hoạt **Blackout Shield** toàn màn hình: "🛡️ CẢNH BÁO AN NINH HỆ THỐNG".
- Ghi nhận nhật ký vi phạm kiểm toán (`AttemptViolation`) về máy chủ.
- Chặn triệt để các phím tắt DevTools (F12, Ctrl+Shift+I/J/C, Ctrl+U) và chụp màn hình (PrintScreen, Win+Shift+S) kèm xóa trắng clipboard bộ nhớ đệm.

## 5. An Toàn Tệp Tin Kiểu Đóng (Fail-Closed File Security)
- Tệp đính kèm học tập tối đa 50MB, nghiêm cấm tệp nén (.zip, .rar, .7z).
- Tệp tải lên chưa qua quét virus (`PENDING`) hoặc bị cách ly (`QUARANTINED`) hoàn toàn bị chặn truy cập.
