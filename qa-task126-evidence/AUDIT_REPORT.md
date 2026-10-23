# BÁO CÁO NGHIỆM THU KIỂM THỬ TRÌNH DUYỆT THỰC TẾ TASK-126 (40 VÒNG CHUẨN HÓA)

- **Ngày thực hiện**: 2026-10-23 18:23:06
- **Tổng số vòng kiểm thử**: 40 / 40 vòng
- **Kết quả**: **40/40 PASS (100.0%)**
- **Tổng thời gian chạy**: 46.78 giây
- **Thư mục ảnh minh chứng**: `qa-task126-evidence/screenshots/`

## 1. Bảng Tổng hợp Kết quả 40 Vòng Kiểm thử:

| Vòng | Nhóm | Tiêu đề Kiểm thử | Trạng thái | Thời gian | Tệp Ảnh Minh chứng |
| :---: | :--- | :--- | :---: | :---: | :--- |
| 01 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Đăng nhập Học viên & Tải Trang chủ Dashboard | **PASS** | 5670 ms | [`round_01_student_dashboard_landing.png`](screenshots/round_01_student_dashboard_landing.png) |
| 02 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Xác minh Vắng mặt Khối Gợi ý Khóa học (DOM ID Check) | **PASS** | 2 ms | [`round_02_dashboard_no_recommendations_id.png`](screenshots/round_02_dashboard_no_recommendations_id.png) |
| 03 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Xác minh Không Tồn tại Tiêu đề Gợi ý Khóa học | **PASS** | 1 ms | [`round_03_dashboard_no_recommendations_text.png`](screenshots/round_03_dashboard_no_recommendations_text.png) |
| 04 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Kiểm tra Khối 'Khóa học đang theo học' Gọn gàng & Cân đối | **PASS** | 504 ms | [`round_04_dashboard_enrolled_courses_clean.png`](screenshots/round_04_dashboard_enrolled_courses_clean.png) |
| 05 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Kiểm tra Cột Phải 'Việc cần làm hôm nay' Cân xứng | **PASS** | 1 ms | [`round_05_dashboard_todo_column_balanced.png`](screenshots/round_05_dashboard_todo_column_balanced.png) |
| 06 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Kiểm tra Console & Network: Không Gọi API Gợi ý Thừa | **PASS** | 0 ms | [`round_06_dashboard_zero_recommendation_requests.png`](screenshots/round_06_dashboard_zero_recommendation_requests.png) |
| 07 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Điều hướng Sang Trang 'Khám phá Khóa học' (Catalog) | **PASS** | 1016 ms | [`round_07_student_catalog_navigation.png`](screenshots/round_07_student_catalog_navigation.png) |
| 08 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Xác minh Danh mục Khóa học Catalog Hiển thị Đầy đủ | **PASS** | 1 ms | [`round_08_catalog_cards_rendering.png`](screenshots/round_08_catalog_cards_rendering.png) |
| 09 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Kiểm tra Tương tác Tìm kiếm & Lọc trên Catalog | **PASS** | 3 ms | [`round_09_catalog_search_interaction.png`](screenshots/round_09_catalog_search_interaction.png) |
| 10 | Nhóm 1: Tinh gọn Trang chủ & Catalog | Hoàn tất Nhóm 1: Trở về Dashboard An toàn & Toàn vẹn | **PASS** | 817 ms | [`round_10_dashboard_catalog_seamless_cycle.png`](screenshots/round_10_dashboard_catalog_seamless_cycle.png) |
| 11 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Truy cập Trang Giới thiệu Khóa học VVIP | **PASS** | 1015 ms | [`round_11_course_intro_page_landing.png`](screenshots/round_11_course_intro_page_landing.png) |
| 12 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Mở Hộp thoại Cổng Thanh toán Khóa học (Purchase Gateway) | **PASS** | 1030 ms | [`round_12_open_purchase_modal.png`](screenshots/round_12_open_purchase_modal.png) |
| 13 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Đo Kích thước Khung QR Thanh toán Trực tiếp (Chuẩn Lớn >= 288px) | **PASS** | 1553 ms | [`round_13_direct_qr_large_dimensions.png`](screenshots/round_13_direct_qr_large_dimensions.png) |
| 14 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Kiểm tra Huy hiệu Hướng dẫn '🔍 Bấm để phóng to' | **PASS** | 3 ms | [`round_14_qr_zoom_indicator_badge.png`](screenshots/round_14_qr_zoom_indicator_badge.png) |
| 15 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Kích hoạt Cửa sổ Phóng to Toàn màn hình (Lightbox Modal) | **PASS** | 3 ms | [`round_15_qr_lightbox_modal_activated.png`](screenshots/round_15_qr_lightbox_modal_activated.png) |
| 16 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Kiểm tra Độ Nét & Tiêu đề Hộp thoại Lightbox | **PASS** | 3 ms | [`round_16_qr_lightbox_clarity_title.png`](screenshots/round_16_qr_lightbox_clarity_title.png) |
| 17 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Kiểm tra Bảng Tóm tắt Chuyển khoản trong Lightbox | **PASS** | 2 ms | [`round_17_qr_lightbox_summary_details.png`](screenshots/round_17_qr_lightbox_summary_details.png) |
| 18 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Thử nghiệm Nút 'Sao chép' STK & Nội dung Chuyển tiền | **PASS** | 4 ms | [`round_18_qr_lightbox_copy_interaction.png`](screenshots/round_18_qr_lightbox_copy_interaction.png) |
| 19 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Đóng Cửa sổ Lightbox An toàn & Mượt mà | **PASS** | 4 ms | [`round_19_qr_lightbox_close_safe.png`](screenshots/round_19_qr_lightbox_close_safe.png) |
| 20 | Nhóm 2: QR Chuẩn Lớn & Lightbox | Kiểm tra Khung QR Nạp tiền Ví Học viên Chuẩn Lớn | **PASS** | 2562 ms | [`round_20_wallet_deposit_qr_large.png`](screenshots/round_20_wallet_deposit_qr_large.png) |
| 21 | Nhóm 3: Admin Quản trị & Sửa giá | Đăng nhập Quản trị viên & Vào Trang 'Duyệt khóa học' | **PASS** | 5905 ms | [`round_21_admin_courses_tab_landing.png`](screenshots/round_21_admin_courses_tab_landing.png) |
| 22 | Nhóm 3: Admin Quản trị & Sửa giá | Cuộn tới Phân khu 'Quản lý khóa học' | **PASS** | 803 ms | [`round_22_admin_scroll_to_course_mgmt.png`](screenshots/round_22_admin_scroll_to_course_mgmt.png) |
| 23 | Nhóm 3: Admin Quản trị & Sửa giá | Xác minh Cột 'Học phí' trong Bảng Quản lý Khóa học | **PASS** | 10 ms | [`round_23_admin_table_tuition_col_header.png`](screenshots/round_23_admin_table_tuition_col_header.png) |
| 24 | Nhóm 3: Admin Quản trị & Sửa giá | Kiểm tra Hiển thị Học phí Định dạng VNĐ / Miễn phí | **PASS** | 507 ms | [`round_24_admin_table_rows_tuition_formatted.png`](screenshots/round_24_admin_table_rows_tuition_formatted.png) |
| 25 | Nhóm 3: Admin Quản trị & Sửa giá | Kiểm tra Nút Thao tác 'Sửa giá' (Màu Chàm / Icon Payments) | **PASS** | 7 ms | [`round_25_admin_edit_price_buttons_present.png`](screenshots/round_25_admin_edit_price_buttons_present.png) |
| 26 | Nhóm 3: Admin Quản trị & Sửa giá | Mở Hộp thoại Modal 'Điều chỉnh học phí khóa học' | **PASS** | 920 ms | [`round_26_open_edit_price_modal.png`](screenshots/round_26_open_edit_price_modal.png) |
| 27 | Nhóm 3: Admin Quản trị & Sửa giá | Kiểm tra Cấu trúc Nhập liệu Hộp thoại Điều chỉnh Học phí | **PASS** | 2 ms | [`round_27_edit_price_modal_structure.png`](screenshots/round_27_edit_price_modal_structure.png) |
| 28 | Nhóm 3: Admin Quản trị & Sửa giá | Thử nghiệm Chọn Chip Giá Nhanh '1.499.000 đ' & Live Preview | **PASS** | 453 ms | [`round_28_edit_price_chip_preset_interaction.png`](screenshots/round_28_edit_price_chip_preset_interaction.png) |
| 29 | Nhóm 3: Admin Quản trị & Sửa giá | Nhập Lý do Điều chỉnh Học phí (Bắt buộc cho Audit Log) | **PASS** | 312 ms | [`round_29_fill_audit_reason.png`](screenshots/round_29_fill_audit_reason.png) |
| 30 | Nhóm 3: Admin Quản trị & Sửa giá | Lưu Thay đổi Học phí & Kiểm tra Cập nhật Tức thì (0-F5) | **PASS** | 1251 ms | [`round_30_submit_price_update_instant_sync.png`](screenshots/round_30_submit_price_update_instant_sync.png) |
| 31 | Nhóm 4: Audit Log, Thông báo & Ca biên | Chuyển sang Phân hệ 'Bảo mật & Nhật ký' (Audit Trail) | **PASS** | 1206 ms | [`round_31_admin_audit_tab_landing.png`](screenshots/round_31_admin_audit_tab_landing.png) |
| 32 | Nhóm 4: Audit Log, Thông báo & Ca biên | Xác minh Bản ghi Audit Log 'COURSE_PRICE_UPDATED' | **PASS** | 4 ms | [`round_32_audit_log_price_updated_entry.png`](screenshots/round_32_audit_log_price_updated_entry.png) |
| 33 | Nhóm 4: Audit Log, Thông báo & Ca biên | Kiểm tra Chi tiết Snapshot Giá Cũ & Giá Mới trong Audit Log | **PASS** | 3 ms | [`round_33_audit_log_snapshot_details.png`](screenshots/round_33_audit_log_snapshot_details.png) |
| 34 | Nhóm 4: Audit Log, Thông báo & Ca biên | Đăng nhập Giảng viên & Vào Trung tâm Thông báo | **PASS** | 6440 ms | [`round_34_instructor_notifications_landing.png`](screenshots/round_34_instructor_notifications_landing.png) |
| 35 | Nhóm 4: Audit Log, Thông báo & Ca biên | Xác minh Thông báo Can thiệp Admin Gửi tới Giảng viên | **PASS** | 2 ms | [`round_35_instructor_received_price_notif.png`](screenshots/round_35_instructor_received_price_notif.png) |
| 36 | Nhóm 4: Audit Log, Thông báo & Ca biên | Kiểm tra Nội dung Thông báo Chi tiết & Liên kết Điều hướng | **PASS** | 500 ms | [`round_36_notification_content_deep_check.png`](screenshots/round_36_notification_content_deep_check.png) |
| 37 | Nhóm 4: Audit Log, Thông báo & Ca biên | Kiểm tra Ca Biên 1: Bắt buộc Nhập Lý do (Chặn Gửi Rỗng) | **PASS** | 6863 ms | [`round_37_edge_case_empty_reason_blocked.png`](screenshots/round_37_edge_case_empty_reason_blocked.png) |
| 38 | Nhóm 4: Audit Log, Thông báo & Ca biên | Kiểm tra Ca Biên 2: Đóng Modal An toàn bằng Phím Escape | **PASS** | 508 ms | [`round_38_edge_case_escape_cancel_safe.png`](screenshots/round_38_edge_case_escape_cancel_safe.png) |
| 39 | Nhóm 4: Audit Log, Thông báo & Ca biên | Rà soát Toàn diện Console & Network Toàn bộ Phiên | **PASS** | 501 ms | [`round_39_session_wide_console_audit.png`](screenshots/round_39_session_wide_console_audit.png) |
| 40 | Nhóm 4: Audit Log, Thông báo & Ca biên | Tổng kết & Nghiệm thu Toàn diện TASK-126 (40/40 PASS) | **PASS** | 500 ms | [`round_40_task126_final_verification_pass.png`](screenshots/round_40_task126_final_verification_pass.png) |

## 2. Chi tiết Nghiệm thu Từng Nhóm Nghiệp vụ:

### Nhóm 1: Tinh gọn Trang chủ Học viên & Bảo toàn Catalog (Vòng 1 - 10)
- **Kết quả**: 10/10 PASS (100%).
- **Xác nhận**: Khối `#dashboard-recommendations-section` và tiêu đề 'Gợi ý khóa học tiếp theo' hoàn toàn biến mất khỏi Trang chủ học viên. Không có request gọi API gợi ý AI dư thừa trên Dashboard. Trang Catalog vẫn giữ nguyên 100% chức năng khám phá, lọc và tìm kiếm.

### Nhóm 2: Khung QR Thanh toán Chuẩn Lớn & Lightbox Phóng to (Vòng 11 - 20)
- **Kết quả**: 10/10 PASS (100%).
- **Xác nhận**: Khung hiển thị mã VietQR (thanh toán khóa học trực tiếp và nạp tiền ví) đạt kích thước lớn chuẩn 288px-320px (`w-72`/`w-80`), hiển thị huy hiệu `🔍 Bấm để phóng to`. Khi click vào ảnh QR, cửa sổ Lightbox `UI.showQrLightbox` bật lên ở trung tâm, QR sắc nét, đầy đủ thông tin thanh toán kèm nút sao chép 1-click.

### Nhóm 3: Admin Quản lý Khóa học & Modal Chỉnh sửa Học phí (Vòng 21 - 30)
- **Kết quả**: 10/10 PASS (100%).
- **Xác nhận**: Bảng Quản lý khóa học trong trang Duyệt khóa học của Admin có cột 'Học phí' hiển thị dạng VNĐ hoặc 'Miễn phí'. Nút 'Sửa giá' (icon `payments`) xuất hiện cạnh nút 'Xóa'. Hộp thoại modal `UI.showCoursePriceEditModal` hỗ trợ xem trước tiền tệ, chip preset chọn nhanh, và bắt buộc nhập lý do. Lưu thay đổi cập nhật bảng tức thì 0ms mà không cần F5.

### Nhóm 4: Audit Trail, Thông báo Giảng viên & Ca Biên (Vòng 31 - 40)
- **Kết quả**: 10/10 PASS (100%).
- **Xác nhận**: Mọi thao tác đổi giá tự động sinh bản ghi `AuditEvent` (`COURSE_PRICE_UPDATED`) lưu snapshot giá cũ/mới và lý do; đồng thời tự động gửi thông báo `SYSTEM_ADMIN_INTERVENTION` trực tiếp cho Giảng viên phụ trách. Các ca biên (bỏ trống lý do, đóng Escape) được xử lý fail-closed an toàn.
