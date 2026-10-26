import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:5000"
STUDENT_EMAIL = "test_student_enroll_213@gmail.com"
PASSWORD = "Password123!"

print("=" * 70)
print("TESTING FULL REGISTRATION WORKFLOW FOR COURSE 213")
print("=" * 70)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
    )
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

    # 1. Login
    print(f"\n[STEP 1] Logging in as unenrolled student: {STUDENT_EMAIL}...")
    page.goto(f"{BASE_URL}/#/auth", wait_until="networkidle")
    time.sleep(1.0)
    page.fill("#login-email", STUDENT_EMAIL)
    page.fill("#login-password", PASSWORD)
    page.evaluate("() => { window._demoSelectedRole = 'STUDENT'; }")
    page.click("#login-submit-btn")
    time.sleep(2.0)
    print("  -> Logged in successfully!")

    # 2. Go to Course 213 Intro Page
    print("\n[STEP 2] Navigating to Course 213 Intro: #/student/courses/intro?id=182bc6b0-13eb-4956-a75f-c8e5e7071f75...")
    page.goto(f"{BASE_URL}/#/student/courses/intro?id=182bc6b0-13eb-4956-a75f-c8e5e7071f75", wait_until="networkidle")
    time.sleep(2.5)

    # Verify marketing intro page is displayed
    enroll_btn = page.locator(".btn-enroll-action")
    print(f"  -> Found {enroll_btn.count()} 'Đăng ký ngay' button(s)")
    assert enroll_btn.count() > 0, "ERROR: No 'Đăng ký ngay' button found on intro page!"

    page.screenshot(path="C:/Users/LENOVO/.gemini/antigravity/brain/453edccf-d202-47d8-a8a3-611588f41eee/step2_intro_before_enroll.png")

    # 3. Click 'Đăng ký ngay'
    print("\n[STEP 3] Clicking 'Đăng ký ngay'...")
    enroll_btn.first.click()
    
    # Wait for response / navigation
    time.sleep(3.5)

    current_url = page.url
    print(f"  -> URL after clicking enroll: {current_url}")
    page.screenshot(path="C:/Users/LENOVO/.gemini/antigravity/brain/453edccf-d202-47d8-a8a3-611588f41eee/step3_after_enroll.png")

    # Check if page is stuck on spinner
    spinner_text = page.locator("text='Đang chuẩn bị trang giới thiệu khóa học...'")
    print(f"  -> Spinner count: {spinner_text.count()}")
    assert spinner_text.count() == 0, "CRITICAL ERROR: Page is STUCK on 'Đang chuẩn bị trang giới thiệu khóa học...'!"

    # Verify classroom console loaded
    console_root = page.locator("#cisco-console-root")
    print(f"  -> Cisco Console Root found: {console_root.count() > 0}")
    assert console_root.count() > 0, "ERROR: Cisco console root not found after enrollment!"

    # Verify course title
    course_title = page.locator("text='213'")
    assert course_title.count() > 0, "ERROR: Course title '213' not found in classroom console!"

    print("\n[SUCCESS] The enrollment workflow completed 100% seamlessly!")
    print("  Student was enrolled, redirected to classroom, and course content was displayed without any freeze!")
