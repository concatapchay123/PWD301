# TASK-BRAND-CLEANUP: Loại bỏ Logo và Khẩu hiệu, Giữ duy nhất "PPTQ LMS"

**Status:** COMPLETED  
**Completed At:** 2026-10-18  
**Scope:**
1. Xóa toàn bộ hình ảnh logo (`pptq_logo_light.png`, `pptq_logo_dark.png`) trên tất cả các trang giao diện hệ thống (Topbar, Mobile Drawer, Auth/Login, Student Settings).
2. Xóa toàn bộ dòng chữ phụ/khẩu hiệu "People • Passion • Team • Quality" (và các biến thể phân cách).
3. Chuẩn hóa hiển thị thương hiệu chỉ duy nhất là **"PPTQ LMS"** với phong cách Warm Editorial, đậm nét (`font-bold` / `font-extrabold`), phân cấp thị giác rõ ràng và căn chỉnh hoàn hảo.

---

## 1. Các tệp đã chỉnh sửa (Per-file Changes)
- [x] **`frontend/index.html`**:
  - Topbar Brand (`#app-topbar`): Loại bỏ 2 thẻ `<img>` (`pptq_logo_light.png` & `pptq_logo_dark.png`), loại bỏ thẻ `<span>` phụ chứa dòng chữ "People • Passion • Team • Quality", giữ lại duy nhất `<span class="font-bold text-base tracking-tight text-[#222120] dark:text-[#EDEDEB]">PPTQ LMS</span>`.
  - Mobile Drawer (`#mobile-nav-drawer`): Loại bỏ 2 thẻ `<img>` logo, giữ lại duy nhất thẻ `<span>` chứa **PPTQ LMS**.
- [x] **`frontend/assets/js/views/auth.js`**:
  - Auth Brand Header: Loại bỏ khối wrapper chứa 2 ảnh logo PPTQ, loại bỏ thẻ `<p>` phụ chứa "People • Passion • Team • Quality", nâng cấp thẻ tiêu đề thành `<h1 class="text-2xl sm:text-3xl font-extrabold text-[#222120] dark:text-[#EDEDEB] tracking-tight">PPTQ LMS</h1>`.
- [x] **`frontend/assets/js/views/student.js`**:
  - Student Settings Header (`StudentView.renderAccountSettings`): Loại bỏ ảnh logo PPTQ gắn kèm tiêu đề trang cài đặt tài khoản, giữ giao diện phẳng, thoáng đãng và thanh lịch.

---

## 2. Xác minh Thực nghiệm (Empirical Verification - 100% PASS)
- **Node Syntax Check**:
  - `node --check frontend/assets/js/views/auth.js`: 0 lỗi.
  - `node --check frontend/assets/js/views/student.js`: 0 lỗi.
- **Backend Tests**:
  - `pytest tests/test_result_pdf_formatting.py`: 14/14 passed in 2.52s.
- **Playwright Headless Chrome Live E2E Verification (`scripts/verify_brand_removal.py`)**:
  - `[PASS]` Step 1: Kiểm tra trang Đăng nhập (`#/auth/login`): Tiêu đề `PPTQ LMS` hiển thị độc tôn; 0 ảnh logo; 0 chữ "People • Passion • Team • Quality". Minh chứng: `verification/fixes/live_login_pptq_lms_clean.png`.
  - `[PASS]` Step 2: Đăng nhập Sinh viên (`student1@pwd301.local`): Topbar hiển thị duy nhất `PPTQ LMS`; 0 ảnh logo; 0 chữ khẩu hiệu. Minh chứng: `verification/fixes/live_student_topbar_clean.png`.
  - `[PASS]` Step 3: Kiểm tra Trang Cài đặt Sinh viên (`#/student/settings`): Header sạch sẽ, 0 ảnh logo; Topbar giữ `PPTQ LMS`. Minh chứng: `verification/fixes/live_student_settings_clean.png`.
  - `[PASS]` Step 4: Đăng nhập Quản trị viên (`admin@pwd301.local`): Topbar Quản trị hiển thị duy nhất `PPTQ LMS`; 0 ảnh logo. Minh chứng: `verification/fixes/live_admin_topbar_clean.png`.
  - `[PASS]` Step 5: Kiểm tra Viewport Di động (375x667): Form đăng nhập di động hiển thị `PPTQ LMS`; 0 ảnh logo. Minh chứng: `verification/fixes/live_mobile_login_clean.png`.
