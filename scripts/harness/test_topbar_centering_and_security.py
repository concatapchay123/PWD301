# -*- coding: utf-8 -*-
"""Verification script for Topbar Dead-Center layout and DevTools / F12 security warning."""

import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

def run_tests():
    print("=" * 80)
    print("TESTING TOPBAR DEAD-CENTER & DEVTOOLS SECURITY WARNING")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        # 1. Login
        print("\n[Step 1] Navigating to http://localhost:5000/#/auth/login...")
        page.goto("http://localhost:5000/#/auth/login")
        page.wait_for_selector("#login-email", timeout=10000)

        # Login as Admin
        page.fill("#login-email", "tqtphamnguyenhoangphuc@gmail.com")
        page.fill("#login-password", "Password123!")
        page.click("#login-submit-btn")
        page.wait_for_selector("#topbar-avatar-btn", timeout=15000)
        page.wait_for_timeout(1000)
        print("Logged in as Admin successfully.")

        # 2. Test F12 and Shortcut Warning Toast
        print("\n[Step 2] Testing F12 keydown security alert...")
        page.keyboard.press("F12")
        page.wait_for_selector(".toast-item, #toast-container > div", timeout=4000)
        toast_text = page.locator("#toast-container").inner_text()
        print("Toast output after F12:\n", toast_text)
        assert "CẢNH BÁO AN NINH" in toast_text, "Toast does not contain security alert on F12!"
        print("✓ Verified: F12 immediately triggers security warning toast!")

        page.wait_for_timeout(3500) # wait for toast throttle

        print("\n[Step 3] Testing Ctrl+Shift+I shortcut security alert...")
        page.keyboard.press("Control+Shift+I")
        page.wait_for_selector(".toast-item, #toast-container > div", timeout=4000)
        toast_text_i = page.locator("#toast-container").inner_text()
        print("Toast output after Ctrl+Shift+I:\n", toast_text_i)
        assert "CẢNH BÁO AN NINH" in toast_text_i, "Toast does not contain security alert on Ctrl+Shift+I!"
        print("✓ Verified: Ctrl+Shift+I immediately triggers security warning toast!")

        # 3. Test Dead-Center Topbar across Viewports
        print("\n[Step 4] Testing Topbar Dead-Center Alignment across viewports...")
        viewports = [1920, 1680, 1440, 1350, 1280, 1024]
        for w in viewports:
            page.set_viewport_size({"width": w, "height": 800})
            page.wait_for_timeout(500)

            logo = page.locator('#app-topbar a[href="#/"]').bounding_box()
            nav = page.locator('#topbar-navigation-items').bounding_box()
            avatar = page.locator('#topbar-avatar-btn').bounding_box()

            nav_center = nav['x'] + nav['width'] / 2.0
            screen_center = w / 2.0
            offset = abs(nav_center - screen_center)

            print(f"\n--- Viewport {w}px ---")
            print(f"  Nav box: left={nav['x']:.1f}px, width={nav['width']:.1f}px, right={nav['x']+nav['width']:.1f}px")
            print(f"  Nav center: {nav_center:.1f}px vs Screen center: {screen_center:.1f}px => Offset: {offset:.2f}px")
            print(f"  Logo right: {logo['x']+logo['width']:.1f}px | Avatar left: {avatar['x']:.1f}px")

            # Offset must be < 1.0px (mathematical dead center)
            assert offset < 1.0, f"Nav is not dead centered at {w}px! Offset: {offset}px"
            # Zero overlap with Logo
            assert nav['x'] >= (logo['x'] + logo['width']), f"Nav overlaps Logo at {w}px!"
            # Zero overlap with Avatar / controls
            assert (nav['x'] + nav['width']) <= avatar['x'], f"Nav overlaps Avatar at {w}px!"

            print(f"  ✓ Pass: Dead-center (offset {offset:.2f}px < 1px) and zero overlap confirmed at {w}px!")

        browser.close()

    print("\n" + "=" * 80)
    print("ALL DEAD-CENTER & SECURITY VERIFICATIONS PASSED 100%!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
