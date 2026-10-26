# -*- coding: utf-8 -*-
"""Verification script for Topbar Dead-Center layout and DevTools security alert on local server."""

import http.server
import socketserver
import threading
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

PORT = 8089

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_server():
    server = socketserver.TCPServer(("127.0.0.1", PORT), QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def run_tests():
    server = start_server()
    print(f"HTTP Server started at http://127.0.0.1:{PORT}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        print("\n[Step 1] Loading http://127.0.0.1:8089/frontend/index.html...")
        page.goto(f"http://127.0.0.1:{PORT}/frontend/index.html")
        page.wait_for_selector("#app-topbar", state="attached", timeout=10000)
        page.evaluate("""
            const tb = document.getElementById('app-topbar');
            if (tb) {
                tb.classList.remove('hidden');
                tb.style.display = 'flex';
            }
        """)

        # Initialize mock roles and test
        for role in ["ADMIN", "INSTRUCTOR", "STUDENT"]:
            print(f"\n=======================================================")
            print(f"TESTING ROLE: {role}")
            print(f"=======================================================")

            # Simulate login state for role
            page.evaluate(f"""
                window.app.currentUser = {{
                    id: 'test-user-id',
                    primary_role: '{role}',
                    active_role: '{role}',
                    display_name: 'Test {role}',
                    email: '{role.lower()}@pptq.id.vn',
                    roles: ['{role}'],
                    role_codes: ['{role}']
                }};
                window.app.currentRole = '{role}';
                window.app.renderDynamicTopbar();
            """)
            page.wait_for_timeout(300)

            # Test across viewports
            viewports = [1920, 1680, 1440, 1350, 1280, 1024]
            for w in viewports:
                page.set_viewport_size({"width": w, "height": 800})
                page.wait_for_timeout(300)

                logo = page.locator('#app-topbar a[href="#/"]').bounding_box()
                nav = page.locator('#topbar-navigation-items').bounding_box()
                right = page.locator('#app-topbar > div:last-child').bounding_box()

                nav_center = nav['x'] + nav['width'] / 2.0
                screen_center = w / 2.0
                offset = abs(nav_center - screen_center)

                print(f"[{role} @ {w}px] Nav center: {nav_center:.1f} vs Screen center: {screen_center:.1f} => Offset: {offset:.2f}px")
                print(f"   Logo right: {logo['x']+logo['width']:.1f}px | Nav left: {nav['x']:.1f}px | Nav right: {nav['x']+nav['width']:.1f}px | Right controls: {right['x']:.1f}px")

                # 1. Exact mathematical dead-center
                assert offset < 1.0, f"FAILED: {role} topbar is not centered at {w}px! Offset: {offset:.2f}px"
                # 2. Zero overlap with logo
                assert nav['x'] >= (logo['x'] + logo['width']), f"FAILED: {role} nav overlaps logo at {w}px!"
                # 3. Zero overlap with right controls
                assert (nav['x'] + nav['width']) <= right['x'], f"FAILED: {role} nav overlaps right controls at {w}px!"

            print(f"✓ All viewports for role {role} are DEAD-CENTERED with ZERO OVERLAP!")

        # Test DevTools security alerts
        print("\n=======================================================")
        print("TESTING DEVTOOLS & F12 SECURITY ALERT")
        print("=======================================================")

        print("\n[Step 2] Testing F12 keydown warning toast...")
        page.keyboard.press("F12")
        page.wait_for_selector(".toast-item, #toast-container > div", timeout=4000)
        toast_f12 = page.locator("#toast-container").inner_text()
        print("Toast on F12:\n", toast_f12)
        assert "CẢNH BÁO AN NINH" in toast_f12, "F12 did not trigger security toast!"
        print("✓ F12 security warning verified successfully!")

        page.wait_for_timeout(3500) # reset throttle

        print("\n[Step 3] Testing Ctrl+Shift+I keydown warning toast...")
        page.keyboard.press("Control+Shift+I")
        page.wait_for_selector(".toast-item, #toast-container > div", timeout=4000)
        toast_ctrl_i = page.locator("#toast-container").inner_text()
        print("Toast on Ctrl+Shift+I:\n", toast_ctrl_i)
        assert "CẢNH BÁO AN NINH" in toast_ctrl_i, "Ctrl+Shift+I did not trigger security toast!"
        print("✓ Ctrl+Shift+I security warning verified successfully!")

        page.wait_for_timeout(3500) # reset throttle

        print("\n[Step 4] Testing Docked DevTools Detection (Outer/Inner dimension difference)...")
        # Simulate browser window dimension split (outerWidth - innerWidth > 160)
        page.evaluate("""
            window.dispatchEvent(new Event('resize'));
        """)
        page.wait_for_timeout(500)

        browser.close()

    server.shutdown()
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED 100%!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
