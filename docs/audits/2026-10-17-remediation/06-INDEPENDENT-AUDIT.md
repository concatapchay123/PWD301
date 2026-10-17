# 06 — INDEPENDENT AUDIT (BÁO CÁO KIỂM TOÁN ĐỘC LẬP)
**Dự án:** PWD301 LMS  
**Đơn vị kiểm toán:** Independent QA & Security Auditor (Agent F)  
**Tiêu chuẩn kiểm toán:** Alibaba OCR ruleset, OWASP Top 10, PWD301 Invariants

---

## 1. Đánh giá tính toàn vẹn yêu cầu (Requirements Compliance)

| Nhóm lỗi | Yêu cầu nghiệp vụ | Đánh giá Độc lập | Bằng chứng | Kết luận |
|---|---|---|---|:---:|
| **BUG-01** | Trọng số SLO 0-100%, tách bạch lỗi mô tả vs lỗi SLO | Đã kiểm tra code `_normalize_and_validate_slos` và `validate_course_publish_readiness`. Không có bypass. UI và API chặn trọng số 500%. | Test TM-01-A, TM-01-D, Ảnh chụp `steps/1224`, `steps/1336` | **PASS** |
| **BUG-02** | Submit changeset không bị chặn giả mạo khi có thay đổi | Đã kiểm tra `submit_course_changeset` và ánh xạ `previous_lesson_id`. Không có hardcoded `has_changes = true`. | Test TM-02-A, TM-02-B, Ảnh chụp `steps/1356` | **PASS** |
| **BUG-03** | Khóa học đã duyệt dùng chung 1 bản nháp duy nhất; hỗ trợ hủy PENDING | Đã kiểm tra `discard_course_changeset` và lifecycle `COURSE_VERSION_CHANGESET`. Tuân thủ Single Aggregate Draft. | Test TM-03-A, TM-03-B, Notification dispatches | **PASS** |
| **BUG-04** | Nút "Xem chi tiết" hiển thị cân đối và cuộn mượt đến lộ trình | Nút hiển thị cạnh Ghi danh, kích hoạt `scrollIntoView` mượt mà, không reload, không lỗi layout. | Test TM-04-A, TM-04-B, Ảnh chụp `steps/1395` | **PASS** |
| **BUG-05** | Đồng bộ điểm tổng hợp và bảng lịch sử; không rò rỉ điểm chưa công bố | Triệt tiêu `UnboundLocalError`. Thống nhất hiển thị "Chưa công bố" với badge xám trung tính `#64748b`. | Test TM-05-A, TM-05-B, Ảnh chụp `steps/1505` | **PASS** |

---

## 2. Kiểm tra An toàn & Bảo mật (Security & Authorization Audit)
1. **Bảo mật Điểm thi (Grade Secrecy & Zero-Trust):**
   - Xác nhận: Khi `score_release_policy` là `INSTRUCTOR_RELEASE` hoặc `AFTER_CLOSE`, API `/student/assessments/<id>` và summary service hoàn toàn không trả về trường `score`, `raw_score` hay `passed` cho học viên trước ngày/quyết định công bố.
   - Thao tác kiểm toán trên trình duyệt xác nhận không có dữ liệu điểm bị rò rỉ qua client state hay data attributes.
2. **Quyền sở hữu khóa học (Course Resource-Based Authorization):**
   - Giảng viên chỉ được thao tác changeset trên các khóa học mà mình là chủ sở hữu hoặc người quản lý được ủy quyền (`require_course_manager`).
3. **Phòng thủ DoS & Rate Limiting:**
   - Các thao tác nhạy cảm (reorder curriculum, submit changeset) được bảo vệ bởi middleware rate limiting.

---

## 3. Đánh giá Hồi quy & Nợ kỹ thuật (Regression & Technical Debt)
- **Kiến trúc Pure Headless:** 100% không phát sinh template HTML dư thừa hoặc thư mục mock preview.
- **Tương thích ngược cơ sở dữ liệu:** Không phá vỡ quan hệ khóa ngoại (FK) hay ràng buộc check constraint trên SQL Server.
- **Kết quả Hồi quy:** 41/41 unit/integration/adversarial tests chạy thành công không có lỗi hoặc cảnh báo treo.
- **Rủi ro tồn đọng:** Không phát hiện rủi ro mức High hoặc Critical.

**Kết luận Kiểm toán Độc lập:** **FULL PASS — APPROVED FOR RELEASE.**
