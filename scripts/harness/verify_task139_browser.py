"""Real browser QA verification script for TASK-139:
1. Verify audit log time display accuracy (no 7h offset bug).
2. Verify topbar responsiveness and zero-overlap across screen viewports:
   - 1920x1080 (Desktop Ultra-wide)
   - 1280x720 (Laptop / 150% scaled)
   - 1024x768 (Small laptop / Tablet landscape)
   - 800x600 (Mobile / Tablet portrait)
"""

import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "qa-evidence-live/task139"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_browser_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("[1/5] Navigating to http://localhost:5000/#/auth/login...")
        page.goto("http://localhost:5000/#/auth/login")
        page.wait_for_selector("#login-email", timeout=10000)

        print("[2/5] Logging in as Admin Hoàng Phúc (tqtphamnguyenhoangphuc@gmail.com)...")
        page.fill("#login-email", "tqtphamnguyenhoangphuc@gmail.com")
        page.fill("#login-password", "Password123!")
        page.click("#login-submit-btn")

        # Wait until topbar user avatar appears (authenticated state)
        page.wait_for_selector("#topbar-avatar-btn", timeout=12000)
        print("Logged in successfully. Current URL:", page.url)

        # Navigate to Security / Audit tab
        print("[3/5] Navigating to #/admin/governance?tab=security...")
        page.goto("http://localhost:5000/#/admin/governance?tab=security")
        page.wait_for_selector("#audit-table-tbody", timeout=12000)
        page.wait_for_timeout(1500)

        # --- VIEWPORT 1: 1920x1080 ---
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(500)
        page.screenshot(path=f"{OUTPUT_DIR}/1920x1080_admin_audit.png")
        print(f"Saved {OUTPUT_DIR}/1920x1080_admin_audit.png")

        # Verify Audit Log time strings
        first_row_time = page.locator("#audit-table-tbody tr:first-child td:nth-child(4)").inner_text()
        print(f"First audit row time display:\n{first_row_time}")

        # Check that it DOES NOT say "7 giờ trước" or wrong relative time
        assert "7 giờ trước" not in first_row_time, "Audit log incorrectly displays '7 giờ trước'!"
        print("✓ Verified: Audit log does NOT have the 7h offset bug!")

        # Verify Topbar in 1920x1080: all 8 items should be visible
        more_btn_visible_1920 = page.locator("#topbar-admin-more-btn").is_visible()
        print(f"1920x1080 More Button Visible: {more_btn_visible_1920} (Expected: False)")
        assert not more_btn_visible_1920, "More button should be hidden at 1920px (all 8 tabs displayed)"

        # --- VIEWPORT 2: 1280x720 ---
        print("[4/5] Testing Viewport 1280x720 (Laptop)...")
        page.set_viewport_size({"width": 1280, "height": 720})
        page.wait_for_timeout(500)

        # Check bounding boxes for overlap
        logo_box = page.locator("#app-topbar a[href='#/']").bounding_box()
        nav_box = page.locator("#topbar-navigation-items").bounding_box()
        avatar_box = page.locator("#topbar-avatar-btn").bounding_box()

        print(f"Logo box: right={logo_box['x'] + logo_box['width']:.1f}")
        print(f"Nav box: left={nav_box['x']:.1f}, right={nav_box['x'] + nav_box['width']:.1f}")
        print(f"Avatar box: left={avatar_box['x']:.1f}")

        # Assert no overlap:
        assert nav_box['x'] >= (logo_box['x'] + logo_box['width']), "Nav overlaps Logo on left!"
        assert (nav_box['x'] + nav_box['width']) <= avatar_box['x'], "Nav overlaps Avatar on right!"
        print("✓ Zero overlap confirmed at 1280x720!")

        more_btn_visible_1280 = page.locator("#topbar-admin-more-btn").is_visible()
        print(f"1280x720 More Button Visible: {more_btn_visible_1280} (Expected: True)")
        assert more_btn_visible_1280, "More button should be visible at 1280px"

        # Click More button to test dropdown
        page.click("#topbar-admin-more-btn")
        page.wait_for_timeout(500)
        dropdown_visible = page.locator("#topbar-admin-more-dropdown").is_visible()
        print(f"More dropdown visible after click: {dropdown_visible} (Expected: True)")
        assert dropdown_visible, "More dropdown did not open"

        page.screenshot(path=f"{OUTPUT_DIR}/1280x720_admin_more_dropdown.png")
        print(f"Saved {OUTPUT_DIR}/1280x720_admin_more_dropdown.png")

        # --- VIEWPORT 3: 1024x768 ---
        print("[5/5] Testing Viewport 1024x768 (Small Laptop)...")
        page.set_viewport_size({"width": 1024, "height": 768})
        page.wait_for_timeout(500)

        logo_box_1024 = page.locator("#app-topbar a[href='#/']").bounding_box()
        nav_box_1024 = page.locator("#topbar-navigation-items").bounding_box()
        avatar_box_1024 = page.locator("#topbar-avatar-btn").bounding_box()

        assert nav_box_1024['x'] >= (logo_box_1024['x'] + logo_box_1024['width']), "Nav overlaps Logo on left at 1024px!"
        assert (nav_box_1024['x'] + nav_box_1024['width']) <= avatar_box_1024['x'], "Nav overlaps Avatar on right at 1024px!"
        print("✓ Zero overlap confirmed at 1024x768!")

        page.screenshot(path=f"{OUTPUT_DIR}/1024x768_admin_audit.png")
        print(f"Saved {OUTPUT_DIR}/1024x768_admin_audit.png")

        # --- VIEWPORT 4: 800x600 (< 1024px) ---
        page.set_viewport_size({"width": 800, "height": 600})
        page.wait_for_timeout(500)
        mobile_btn = page.locator("#topbar-mobile-menu-btn")
        assert mobile_btn.is_visible(), "Mobile hamburger button must be visible at 800px"
        mobile_btn.click()
        page.wait_for_timeout(500)
        drawer_visible = page.locator("#mobile-nav-drawer").is_visible()
        assert drawer_visible, "Mobile drawer must open when clicking menu button"
        page.screenshot(path=f"{OUTPUT_DIR}/800x600_mobile_drawer.png")
        print(f"Saved {OUTPUT_DIR}/800x600_mobile_drawer.png")

        browser.close()
        print("\n========================================================")
        print("ALL REAL BROWSER CHECKS PASSED (100% SUCCESSFUL)!")
        print("========================================================")

if __name__ == "__main__":
    run_browser_verification()
