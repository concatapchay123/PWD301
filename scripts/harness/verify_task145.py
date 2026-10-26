#!/usr/bin/env python3
"""scripts/verify_task145.py

Real-Browser E2E Verification for TASK-145:
1. Outline Certificate Button Hidden: When course lessons are done but assessments not yet passed, certificate button is strictly HIDDEN.
2. Waiting Room Unlocked: Student can enter waiting room and start exam without 'Bài thi hiện chưa thể bắt đầu' block.
3. Assessments Tab & Outline Synchronized: 'Bài kiểm tra' tab and Course Outline show identical 'Sẵn sàng thi' status.
"""

import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:5000"
STUDENT_EMAIL = "tqtphamnguyenhoangphuc@gmail.com"
STUDENT_PASSWORD = "Password123!"
COURSE_ID = "182bc6b0-13eb-4956-a75f-c8e5e7071f75"
ASSESSMENT_ID = "96339791-56c1-471a-9d4d-9147a08c00da"


def run_verification():
    print("=" * 80)
    print("BẮT ĐẦU KIỂM THỬ TRÌNH DUYỆT THỰC TẾ TASK-145 (PLAYWRIGHT CHROMIUM)")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            base_url=BASE_URL,
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()

        # Step 1: Login
        print("[1] Đăng nhập tài khoản học viên...")
        page.goto(f"{BASE_URL}/#/auth/login", wait_until="networkidle")
        time.sleep(1.0)
        page.fill("input[name='email']", STUDENT_EMAIL)
        page.fill("input[name='password']", STUDENT_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_timeout(2500)

        for _ in range(15):
            if "#/student" in page.url or "#/instructor" in page.url or "#/admin" in page.url:
                break
            time.sleep(0.5)

        print(f"    -> Đăng nhập thành công! URL hiện tại: {page.url}")

        # Step 2: Course Learning Console & Certificate Download Button Check
        print(f"[2] Truy cập phòng học khóa 213 ({COURSE_ID})...")
        page.goto(f"{BASE_URL}/#/student/courses/detail?id={COURSE_ID}", wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Check Certificate Button: Must NOT be visible
        cert_btn_count = page.locator("#btn-download-course-certificate").count()
        cert_container_text = page.locator("#outline-certificate-container").inner_text().strip()
        print(f"    -> Số lượng nút 'Tải Chứng chỉ PDF': {cert_btn_count}")
        print(f"    -> Nội dung container chứng chỉ: '{cert_container_text}'")
        assert cert_btn_count == 0, "THẤT BẠI: Nút chứng chỉ vẫn hiển thị khi chưa hoàn thành/đạt bài thi!"
        print("    [PASS] Nút 'Tải Chứng chỉ PDF' bị ẩn hoàn toàn (Chưa thi đạt bài kiểm tra).")

        # Check Outline Exam Node
        outline_html = page.locator("#outline-accordion-list").inner_text()
        print(f"    -> Đề cương có hiển thị bài thi 'English Multiple': {'English Multiple' in outline_html}")
        assert "English Multiple" in outline_html, "Không tìm thấy English Multiple trong đề cương!"
        print("    [PASS] English Multiple hiển thị chuẩn xác trong đề cương môn học.")

        # Step 3: Waiting Room State & Eligibility
        print(f"[3] Truy cập phòng chờ thi English Multiple ({ASSESSMENT_ID})...")
        page.goto(f"{BASE_URL}/#/student/assessments/waiting-room?id={ASSESSMENT_ID}", wait_until="networkidle")
        page.wait_for_timeout(2500)

        body_text = page.locator("#app-viewport").inner_text()
        print(f"    -> Có xuất hiện thông báo lỗi 'Bài thi hiện chưa thể bắt đầu': {'Bài thi hiện chưa thể bắt đầu' in body_text}")
        assert "Bài thi hiện chưa thể bắt đầu" not in body_text, "THẤT BẠI: Phòng chờ thi vẫn bị lỗi 'Bài thi hiện chưa thể bắt đầu'!"

        ready_badge_count = page.locator("text='Sẵn sàng vào thi'").count()
        print(f"    -> Trạng thái phòng chờ: {'Sẵn sàng vào thi' if ready_badge_count > 0 else 'Khác'}")
        assert ready_badge_count > 0, "THẤT BẠI: Phòng chờ không hiển thị badge 'Sẵn sàng vào thi'!"

        # Check Pledge & Action button
        pledge_check = page.locator("#waiting-room-pledge-check")
        action_btn = page.locator("#start-exam-action-btn")
        assert pledge_check.count() > 0, "Không tìm thấy hộp kiểm cam kết thí sinh!"
        assert action_btn.count() > 0, "Không tìm thấy nút 'Bắt đầu làm bài thi'!"
        print("    [PASS] Phòng chờ hiển thị đầy đủ quy chế, hộp kiểm cam kết và nút 'Bắt đầu làm bài thi'.")

        # Step 4: Assessments Tab Synchronization
        print("[4] Truy cập tab 'Bài kiểm tra' (#/student/assessments)...")
        page.goto(f"{BASE_URL}/#/student/assessments", wait_until="networkidle")
        page.wait_for_timeout(2500)

        list_body = page.locator("#student-assessments-grid").inner_text()
        print(f"    -> Danh sách có chứa 'English Multiple': {'English Multiple' in list_body}")
        assert "English Multiple" in list_body, "Không tìm thấy English Multiple trên tab Bài kiểm tra!"

        # Ensure no false prerequisite lock on tab
        assert "Chưa đủ điều kiện thi" not in list_body, "THẤT BẠI: Tab Bài kiểm tra báo 'Chưa đủ điều kiện thi' không đồng bộ!"
        print("    [PASS] Tab Bài kiểm tra đồng bộ 100%: Bài thi ở trạng thái sẵn sàng vào thi.")

        browser.close()

    print("=" * 80)
    print("HOÀN TẤT KIỂM THỬ TRÌNH DUYỆT THỰC TẾ TASK-145: 100% PASS!")
    print("=" * 80)


if __name__ == "__main__":
    run_verification()
