"""
Empirical verification script for:
- Removing all logos (light & dark pptq_logo images)
- Removing tagline "People • Passion • Team • Quality"
- Leaving solely "PPTQ LMS" across all system pages and login page.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path("verification/fixes")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

PORT = 5000
BASE_URL = f"http://127.0.0.1:{PORT}"

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))

def run_verification():
    safe_print("=" * 60)
    safe_print("STARTING EMPIRICAL VERIFICATION: PPTQ LMS BRAND CLEANUP")
    safe_print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        # -------------------------------------------------------------
        # STEP 1: VERIFY LOGIN / AUTH PAGE
        # -------------------------------------------------------------
        safe_print("\n[*] Step 1: Checking Login / Auth Page...")
        context1 = browser.new_context(viewport={"width": 1440, "height": 900})
        page1 = context1.new_page()

        page1.goto(f"{BASE_URL}/#/auth/login", wait_until="networkidle")
        page1.wait_for_selector("#login-email", timeout=10000)
        time.sleep(1.0)

        # Check for PPTQ LMS heading
        heading = page1.locator("h1:has-text('PPTQ LMS')")
        assert heading.count() > 0, "Error: 'PPTQ LMS' heading not found on login page"
        heading_text = heading.first.inner_text().strip()
        safe_print(f" -> Found heading: '{heading_text}'")
        assert heading_text == "PPTQ LMS", f"Expected 'PPTQ LMS', got '{heading_text}'"

        # Check that NO pptq_logo exists
        login_logos = page1.locator("img[src*='pptq_logo']")
        assert login_logos.count() == 0, f"Error: Found {login_logos.count()} logo image(s) on login page"
        safe_print(" -> Verified: 0 logo images on login page")

        # Check that slogan does NOT exist
        login_content = page1.content()
        assert "People • Passion • Team • Quality" not in login_content, "Error: Slogan still found in login HTML"
        assert "People . Passion . Team . Quality" not in login_content, "Error: Slogan still found in login HTML"
        safe_print(" -> Verified: Slogan 'People • Passion • Team • Quality' is completely removed")

        # Screenshot login page
        login_shot = EVIDENCE_DIR / "live_login_pptq_lms_clean.png"
        page1.screenshot(path=str(login_shot))
        safe_print(f" -> Saved screenshot: {login_shot}")

        # -------------------------------------------------------------
        # STEP 2: LOGIN & VERIFY TOPBAR ON STUDENT DASHBOARD
        # -------------------------------------------------------------
        safe_print("\n[*] Step 2: Logging in as Student (student1@pwd301.local)...")
        page1.fill("#login-email", "student1@pwd301.local")
        page1.fill("#login-password", "Student@123456")
        page1.click("#login-submit-btn")

        # Wait for topbar to appear
        page1.wait_for_selector("#app-topbar", state="visible", timeout=15000)
        time.sleep(2.0)
        safe_print(" -> Student logged in successfully. Topbar is displayed.")

        # Check Topbar on Student Dashboard
        safe_print("\n[*] Checking Topbar on Student Dashboard...")
        topbar_brand = page1.locator("#app-topbar a[href='#/'] span")
        assert topbar_brand.count() > 0, "Error: Topbar brand text span not found"
        topbar_text = topbar_brand.first.inner_text().strip()
        safe_print(f" -> Topbar brand text: '{topbar_text}'")
        assert topbar_text == "PPTQ LMS", f"Expected 'PPTQ LMS', got '{topbar_text}'"

        # Check no logo images in topbar
        topbar_logos = page1.locator("#app-topbar img[src*='pptq_logo']")
        assert topbar_logos.count() == 0, f"Error: Found {topbar_logos.count()} logo images in topbar"
        safe_print(" -> Verified: 0 logo images in topbar")

        # Check no slogan in topbar
        topbar_html = page1.locator("#app-topbar").inner_html()
        assert "People • Passion • Team • Quality" not in topbar_html, "Error: Slogan found in topbar"
        safe_print(" -> Verified: No slogan in topbar")

        student_shot = EVIDENCE_DIR / "live_student_topbar_clean.png"
        page1.screenshot(path=str(student_shot))
        safe_print(f" -> Saved screenshot: {student_shot}")

        # -------------------------------------------------------------
        # STEP 3: NAVIGATE TO STUDENT SETTINGS & CHECK HEADER
        # -------------------------------------------------------------
        safe_print("\n[*] Step 3: Navigating to Student Settings...")
        page1.goto(f"{BASE_URL}/#/student/settings", wait_until="networkidle")
        time.sleep(1.5)

        # Check that page header has no pptq_logo
        settings_logos = page1.locator("img[src*='pptq_logo']")
        assert settings_logos.count() == 0, f"Error: Found {settings_logos.count()} logo in student settings"
        safe_print(" -> Verified: 0 logo images on Student Settings page")

        # Topbar on Settings page also has PPTQ LMS
        topbar_text_settings = page1.locator("#app-topbar a[href='#/'] span").first.inner_text().strip()
        assert topbar_text_settings == "PPTQ LMS", f"Expected 'PPTQ LMS', got '{topbar_text_settings}'"

        settings_shot = EVIDENCE_DIR / "live_student_settings_clean.png"
        page1.screenshot(path=str(settings_shot))
        safe_print(f" -> Saved screenshot: {settings_shot}")
        context1.close()

        # -------------------------------------------------------------
        # STEP 4: LOGIN AS ADMIN IN ISOLATED CONTEXT
        # -------------------------------------------------------------
        safe_print("\n[*] Step 4: Testing Admin View (admin@pwd301.local)...")
        context2 = browser.new_context(viewport={"width": 1440, "height": 900})
        page2 = context2.new_page()

        page2.goto(f"{BASE_URL}/#/auth/login", wait_until="networkidle")
        page2.wait_for_selector("#login-email", timeout=10000)
        page2.fill("#login-email", "admin@pwd301.local")
        page2.fill("#login-password", "Admin@123456")
        page2.click("#login-submit-btn")
        page2.wait_for_selector("#app-topbar", state="visible", timeout=15000)
        time.sleep(2.0)

        admin_topbar_brand = page2.locator("#app-topbar a[href='#/'] span")
        admin_topbar_text = admin_topbar_brand.first.inner_text().strip()
        assert admin_topbar_text == "PPTQ LMS", f"Expected 'PPTQ LMS' in admin topbar, got '{admin_topbar_text}'"
        admin_topbar_logos = page2.locator("#app-topbar img[src*='pptq_logo']")
        assert admin_topbar_logos.count() == 0, "Error: Logo image found in admin topbar"
        safe_print(f" -> Admin topbar brand text: '{admin_topbar_text}' (No logos)")

        admin_shot = EVIDENCE_DIR / "live_admin_topbar_clean.png"
        page2.screenshot(path=str(admin_shot))
        safe_print(f" -> Saved screenshot: {admin_shot}")
        context2.close()

        # -------------------------------------------------------------
        # STEP 5: TEST MOBILE VIEWPORT (INITIAL 375x667 CONTEXT)
        # -------------------------------------------------------------
        safe_print("\n[*] Step 5: Testing Mobile Viewport (375x667 initial context)...")
        context3 = browser.new_context(viewport={"width": 375, "height": 667})
        page3 = context3.new_page()

        page3.goto(f"{BASE_URL}/#/auth/login", wait_until="networkidle")
        page3.wait_for_selector("#login-email", timeout=10000)

        mobile_brand = page3.locator("h1:has-text('PPTQ LMS')").first.inner_text().strip()
        assert mobile_brand == "PPTQ LMS", f"Expected 'PPTQ LMS' on mobile login, got '{mobile_brand}'"
        mobile_logos = page3.locator("img[src*='pptq_logo']")
        assert mobile_logos.count() == 0, "Error: Logo found on mobile login"
        safe_print(" -> Mobile login verified: 'PPTQ LMS' with 0 logo images")

        mobile_shot = EVIDENCE_DIR / "live_mobile_login_clean.png"
        page3.screenshot(path=str(mobile_shot))
        safe_print(f" -> Saved screenshot: {mobile_shot}")
        context3.close()

        browser.close()

    safe_print("\n" + "=" * 60)
    safe_print("ALL EMPIRICAL VERIFICATION CHECKS PASSED SUCCESSFULLY (100%)!")
    safe_print("=" * 60)

if __name__ == "__main__":
    run_verification()
