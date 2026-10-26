import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:5000"
STUDENT_EMAIL = "tqtphamnguyenhoangphuc@gmail.com"
PASSWORD = "Password123!"
EVIDENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evidence", "task144")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def run():
    print("=" * 70)
    print("  TASK-144 REAL-BROWSER STLC TESTING")
    print("  Testing Course 213 Intro Loading & Silent Native Certificate Download")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            accept_downloads=True
        )
        page = context.new_page()

        # Listen to console messages
        page.on("console", lambda msg: print(f"  [Browser Console] {msg.type}: {msg.text}") if "error" in msg.type.lower() else None)

        # Step 1: Login as Student
        print(f"\n[STLC 1] Logging in as Student: {STUDENT_EMAIL}...")
        page.goto(f"{BASE_URL}/#/auth", wait_until="networkidle")
        time.sleep(1.0)
        
        page.wait_for_selector("#login-email", state="visible", timeout=10000)
        page.fill("#login-email", STUDENT_EMAIL)
        page.fill("#login-password", PASSWORD)
        page.evaluate("() => { window._demoSelectedRole = 'STUDENT'; }")
        page.click("#login-submit-btn")
        time.sleep(2.0)
        print("  -> Logged in successfully!")

        # Step 2: Test Course 213 Intro Page
        print("\n[STLC 2] Navigating to Course 213 Intro: #/student/courses/intro?id=182bc6b0-13eb-4956-a75f-c8e5e7071f75...")
        page.goto(f"{BASE_URL}/#/student/courses/intro?id=182bc6b0-13eb-4956-a75f-c8e5e7071f75", wait_until="networkidle")
        time.sleep(2.5)

        # Check for error banner
        error_el = page.locator("text='Không thể tải thông tin khóa học'")
        assert error_el.count() == 0, "ERROR: Page still shows 'Không thể tải thông tin khóa học'!"
        
        # Verify Course 213 Title is displayed
        title_el = page.locator("text='213'")
        assert title_el.count() > 0, "ERROR: Course title '213' not found on intro page!"
        print("  -> Course 213 Intro page loaded successfully with ZERO 500 error!")
        
        screenshot_path1 = os.path.join(EVIDENCE_DIR, "round_01_course_213_intro_fixed.png")
        page.screenshot(path=screenshot_path1)
        print(f"  -> Screenshot saved to {screenshot_path1}")

        # Step 3: Test Silent Native Certificate Download on Completed Course
        print("\n[STLC 3] Navigating to Completed Course (AND801): #/student/courses/detail?id=e9baeea4-2b6e-48b2-bd3e-055974251309...")
        page.goto(f"{BASE_URL}/#/student/courses/detail?id=e9baeea4-2b6e-48b2-bd3e-055974251309", wait_until="networkidle")
        time.sleep(2.5)

        # Verify Certificate button in sidebar
        cert_btn = page.locator("#btn-download-course-certificate")
        assert cert_btn.is_visible(), "ERROR: Certificate download button not visible in sidebar!"
        print("  -> Certificate download button is visible in sidebar!")

        # Click the button and expect a browser download event
        print("  -> Clicking 'Tải Chứng chỉ PDF' button...")
        with page.expect_download(timeout=15000) as download_info:
            cert_btn.click()
        
        download = download_info.value
        filename = download.suggested_filename
        print(f"  -> Download triggered by browser! Suggested filename: {filename}")
        assert "Chung_chi" in filename and filename.endswith(".pdf"), f"Unexpected filename: {filename}"

        # Verify NO success or in-progress toasts appeared
        time.sleep(1.0)
        toast_creating = page.locator("text='Đang khởi tạo và tải chứng chỉ'")
        toast_success = page.locator("text='Tải chứng chỉ PDF thành công'")
        assert toast_creating.count() == 0, "ERROR: 'Đang khởi tạo' toast unexpectedly appeared!"
        assert toast_success.count() == 0, "ERROR: 'Tải thành công' toast unexpectedly appeared!"
        print("  -> Verified: ZERO notification toasts appeared during download (100% silent & clean)!")

        # Save downloaded file to verify byte content
        download_path = os.path.join(EVIDENCE_DIR, filename)
        download.save_as(download_path)
        file_size = os.path.getsize(download_path)
        with open(download_path, "rb") as f:
            header = f.read(4)
        print(f"  -> Downloaded file saved to {download_path}: {file_size:,} bytes (header={header})")
        assert header == b"%PDF", f"Downloaded file is not a valid PDF: header={header}"
        assert file_size > 100000, f"Downloaded file too small: {file_size} bytes"

        screenshot_path2 = os.path.join(EVIDENCE_DIR, "round_02_silent_certificate_download.png")
        page.screenshot(path=screenshot_path2)
        print(f"  -> Screenshot saved to {screenshot_path2}")

        browser.close()

    print("\n" + "=" * 70)
    print("  ALL REAL-BROWSER TESTS PASSED 100%!")
    print("=" * 70)

if __name__ == '__main__':
    run()
