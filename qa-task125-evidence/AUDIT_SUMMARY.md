# BÁO CÁO KIỂM THỬ TRÌNH DUYỆT THỰC TẾ TASK-125 (40 VÒNG CHUẨN HÓA)

> **Mục tiêu nghiệm thu:** Xác minh thực nghiệm trên trình duyệt thật (Playwright Chromium) việc tái thiết kế chứng chỉ hoàn thành khóa học khổ đứng A4 Portrait, đồng bộ Typography Be Vietnam Pro, nhúng Logo chìm Base64, và thanh trừng 100% logic khổ ngang cũ.

---

## 1. TỔNG QUAN KẾT QUẢ KIỂM THỬ

* **Tổng số vòng kiểm thử thực tế:** **40 / 40 vòng**
* **Tỷ lệ vượt qua (Pass Rate):** **100.0% (40/40 PASS)**
* **Thời gian phản hồi trung bình:** **394.8 ms**
* **Tổng thời gian thực thi:** **27.83 giây**
* **Thư mục minh chứng hình ảnh:** `qa-task125-evidence/screenshots/` (đầy đủ 40 ảnh có banner kỹ thuật 100px)

---

## 2. BẢNG TỔNG HỢP CHI TIẾT 40 VÒNG KIỂM THỬ

| Vòng | Nhóm kiểm thử | Thao tác thực tế | Kết quả | Độ trễ | Ảnh minh chứng |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **01** | Nhóm 1: Xác thực & Khám phá | Đăng nhập Học viên & Tải Trang chủ Dashboard | `PASS` | 1004 ms | [round_01_student_dashboard_landing.png](screenshots/round_01_student_dashboard_landing.png) |
| **02** | Nhóm 1: Xác thực & Khám phá | Điều hướng Khóa học của tôi | `PASS` | 1004 ms | [round_02_student_my_courses.png](screenshots/round_02_student_my_courses.png) |
| **03** | Nhóm 1: Xác thực & Khám phá | Kiểm tra Thẻ Khóa học AND801 Đã Hoàn thành | `PASS` | 1 ms | [round_03_course_card_completed_badge.png](screenshots/round_03_course_card_completed_badge.png) |
| **04** | Nhóm 1: Xác thực & Khám phá | Mở Trình Đọc Bài học & Đề cương | `PASS` | 1504 ms | [round_04_learning_reader_landing.png](screenshots/round_04_learning_reader_landing.png) |
| **05** | Nhóm 1: Xác thực & Khám phá | Kiểm tra Cây Đề cương Bài học Sidebar | `PASS` | 3 ms | [round_05_sidebar_outline_rendered.png](screenshots/round_05_sidebar_outline_rendered.png) |
| **06** | Nhóm 1: Xác thực & Khám phá | Xác minh Khung Chứng chỉ Khóa học | `PASS` | 0 ms | [round_06_certificate_container_dom.png](screenshots/round_06_certificate_container_dom.png) |
| **07** | Nhóm 1: Xác thực & Khám phá | Xác minh Nút Tải Chứng chỉ PDF | `PASS` | 2 ms | [round_07_btn_download_certificate_pdf.png](screenshots/round_07_btn_download_certificate_pdf.png) |
| **08** | Nhóm 1: Xác thực & Khám phá | Xác minh Nút Xem trước Chứng chỉ HTML | `PASS` | 1 ms | [round_08_btn_view_certificate_html.png](screenshots/round_08_btn_view_certificate_html.png) |
| **09** | Nhóm 1: Xác thực & Khám phá | Kiểm tra Hiệu ứng Rê chuột Nút Chứng chỉ | `PASS` | 547 ms | [round_09_btn_certificate_hover.png](screenshots/round_09_btn_certificate_hover.png) |
| **10** | Nhóm 1: Xác thực & Khám phá | Audit Khai trừ Badge Cũ Header (Ponytail) | `PASS` | 2 ms | [round_10_legacy_progress_badge_purged.png](screenshots/round_10_legacy_progress_badge_purged.png) |
| **11** | Nhóm 2: HTML Certificate & Typography | Tải Trang Chứng chỉ HTML Trực tiếp | `PASS` | 1684 ms | [round_11_html_cert_full_view.png](screenshots/round_11_html_cert_full_view.png) |
| **12** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Kích thước Canvas A4 Khổ Đứng | `PASS` | 12 ms | [round_12_canvas_dimensions_portrait.png](screenshots/round_12_canvas_dimensions_portrait.png) |
| **13** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Logo Chìm PPTQ Base64 Trung tâm | `PASS` | 7 ms | [round_13_base64_watermark_centered.png](screenshots/round_13_base64_watermark_centered.png) |
| **14** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Khung Viền Kép Hoàng Gia | `PASS` | 2 ms | [round_14_sovereign_double_borders.png](screenshots/round_14_sovereign_double_borders.png) |
| **15** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Logo Hệ thống PPTQ LMS Trên cùng | `PASS` | 7 ms | [round_15_top_system_logo_pptq.png](screenshots/round_15_top_system_logo_pptq.png) |
| **16** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Tiêu đề Hệ thống (Tiếng Việt & Tiếng Anh) | `PASS` | 3 ms | [round_16_academy_names_typography.png](screenshots/round_16_academy_names_typography.png) |
| **17** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Tiêu đề Chính & Phụ Tiếng Anh | `PASS` | 3 ms | [round_17_main_titles_typography.png](screenshots/round_17_main_titles_typography.png) |
| **18** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Tên Học viên Nhận Chứng chỉ | `PASS` | 2 ms | [round_18_recipient_name_typography.png](screenshots/round_18_recipient_name_typography.png) |
| **19** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Đoạn văn Công nhận Hoàn thành | `PASS` | 1 ms | [round_19_citation_block_typography.png](screenshots/round_19_citation_block_typography.png) |
| **20** | Nhóm 2: HTML Certificate & Typography | Kiểm tra Khung Tên Khóa học & Huy hiệu Mã môn | `PASS` | 3 ms | [round_20_course_banner_code_badge.png](screenshots/round_20_course_banner_code_badge.png) |
| **21** | Nhóm 3: Con dấu & Chữ ký | Kiểm tra Cột Hội Đồng Đào Tạo (Bên Trái) | `PASS` | 2 ms | [round_21_left_governance_column.png](screenshots/round_21_left_governance_column.png) |
| **22** | Nhóm 3: Con dấu & Chữ ký | Kiểm tra Cột Ban Giảng Huấn & Quản Trị (Bên Phải) | `PASS` | 2 ms | [round_22_right_governance_column.png](screenshots/round_22_right_governance_column.png) |
| **23** | Nhóm 3: Con dấu & Chữ ký | Kiểm tra Con Dấu Xác Nhận Điện Tử Trung Tâm | `PASS` | 1 ms | [round_23_central_digital_seal_svg.png](screenshots/round_23_central_digital_seal_svg.png) |
| **24** | Nhóm 3: Con dấu & Chữ ký | Xác minh Con Dấu Không Va Chạm Viền & Text | `PASS` | 4 ms | [round_24_seal_geometry_clearance.png](screenshots/round_24_seal_geometry_clearance.png) |
| **25** | Nhóm 3: Con dấu & Chữ ký | Kiểm tra Thanh Thông Tin Chân Trang Registry | `PASS` | 0 ms | [round_25_registry_ledger_bar.png](screenshots/round_25_registry_ledger_bar.png) |
| **26** | Nhóm 3: Con dấu & Chữ ký | Kiểm tra Thông tin Ngày Cấp (Date of Issue) | `PASS` | 3 ms | [round_26_registry_issue_date.png](screenshots/round_26_registry_issue_date.png) |
| **27** | Nhóm 3: Con dấu & Chữ ký | Kiểm tra Mã Số Chứng Chỉ (Credential ID) | `PASS` | 2 ms | [round_27_registry_credential_id.png](screenshots/round_27_registry_credential_id.png) |
| **28** | Nhóm 3: Con dấu & Chữ ký | Mô phỏng Chế độ In Ấn (@media print) | `PASS` | 502 ms | [round_28_print_media_simulation.png](screenshots/round_28_print_media_simulation.png) |
| **29** | Nhóm 3: Con dấu & Chữ ký | Kiểm tra Nạp Phông Chữ Be Vietnam Pro | `PASS` | 1 ms | [round_29_webfont_be_vietnam_pro.png](screenshots/round_29_webfont_be_vietnam_pro.png) |
| **30** | Nhóm 3: Con dấu & Chữ ký | Kiểm tra Tệp Ngoại Tuyến Tại Thư Mục Downloads | `PASS` | 2189 ms | [round_30_downloaded_file_offline_audit.png](screenshots/round_30_downloaded_file_offline_audit.png) |
| **31** | Nhóm 4: PDF & Bảo mật | Kích hoạt Tải Chứng chỉ PDF từ Giao diện Học viên | `PASS` | 4350 ms | [round_31_trigger_pdf_download_event.png](screenshots/round_31_trigger_pdf_download_event.png) |
| **32** | Nhóm 4: PDF & Bảo mật | Kiểm tra Endpoint Xuất PDF Chính thức | `PASS` | 1260 ms | [round_32_direct_pdf_endpoint_check.png](screenshots/round_32_direct_pdf_endpoint_check.png) |
| **33** | Nhóm 4: PDF & Bảo mật | Kiểm tra Hình học & Khổ Giấy PDF (A4 Portrait) | `PASS` | 1 ms | [round_33_pdf_geometry_portrait_a4.png](screenshots/round_33_pdf_geometry_portrait_a4.png) |
| **34** | Nhóm 4: PDF & Bảo mật | Xác minh Nội dung Tệp PDF Xuất ra | `PASS` | 38 ms | [round_34_pdf_content_validation.png](screenshots/round_34_pdf_content_validation.png) |
| **35** | Nhóm 4: PDF & Bảo mật | Kiểm tra Bảo mật Fail-Closed (Chưa Đăng nhập) | `PASS` | 7 ms | [round_35_security_fail_closed_unauth.png](screenshots/round_35_security_fail_closed_unauth.png) |
| **36** | Nhóm 4: PDF & Bảo mật | Kiểm tra Bảo mật Khóa học Chưa Hoàn thành | `PASS` | 10 ms | [round_36_security_incomplete_course.png](screenshots/round_36_security_incomplete_course.png) |
| **37** | Nhóm 4: PDF & Bảo mật | Kiểm tra Phong bì Dữ liệu Metadata JSON | `PASS` | 14 ms | [round_37_certificate_json_metadata.png](screenshots/round_37_certificate_json_metadata.png) |
| **38** | Nhóm 4: PDF & Bảo mật | Kiểm tra Độ Phân Giải Cao Desktop 1920x1080 | `PASS` | 1612 ms | [round_38_desktop_1080p_high_dpi.png](screenshots/round_38_desktop_1080p_high_dpi.png) |
| **39** | Nhóm 4: PDF & Bảo mật | Kiểm toán Toàn vẹn Console & Network | `PASS` | 0 ms | [round_39_console_network_integrity.png](screenshots/round_39_console_network_integrity.png) |
| **40** | Nhóm 4: PDF & Bảo mật | Tổng kết & Nghiệm thu Toàn diện TASK-125 | `PASS` | 0 ms | [round_40_final_acceptance_summary.png](screenshots/round_40_final_acceptance_summary.png) |

---

## 3. KẾT LUẬN NGHIỆM THU
1. **Chuẩn Bất biến A4 Khổ Đứng (Portrait A4):** Cả bản xem trước HTML (`?format=html`) và tệp PDF chính thức đều hiển thị khổ đứng 210mm × 297mm chính xác 100%.
2. **Typography Đồng nhất:** Toàn bộ tiêu đề, phụ đề, tên học viên, đoạn văn công nhận dùng phông `Be Vietnam Pro` sắc nét, huy hiệu mã môn và mã chứng chỉ dùng phông `JetBrains Mono`.
3. **Logo Chìm Base64:** Logo PPTQ được nhúng trực tiếp Base64 với độ mờ trang nhã ~8% ở trung tâm nền chứng chỉ, mở ngoại tuyến không bị mất hình.
4. **Khai trừ Logic Cũ:** Toàn bộ quy ước và mã nguồn nhắc đến chứng chỉ khổ ngang (Landscape A4 cũ) đã được dọn sạch triệt để khỏi `AGENTS.md` và hệ thống.
