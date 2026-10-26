# -*- coding: utf-8 -*-
"""Verification script for live VPS Topbar Dead-Center layout and DevTools security alert."""

import sys
import os
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

OUTPUT_DIR = "qa-evidence-live/vps_deadcenter"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_live_tests():
    print("=" * 80, flush=True)
    print("XÁC MINH TRÌNH DUYỆT THỰC TẾ TRÊN LIVE PRODUCTION (https://pptq.id.vn)", flush=True)
    print("=" * 80, flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # 1. Điều hướng tới live VPS
        print("\n[1/5] Điều hướng tới https://pptq.id.vn/#/auth/login...", flush=True)
        page.goto("https://pptq.id.vn/#/auth/login")
        page.wait_for_selector("#login-email", timeout=15000)

        # 2. Đăng nhập Admin
        print("[2/5] Đăng nhập Admin Hoàng Phúc (tqtphamnguyenhoangphuc@gmail.com)...", flush=True)
        page.fill("#login-email", "tqtphamnguyenhoangphuc@gmail.com")
        page.fill("#login-password", "Password123!")
        page.click("#login-submit-btn")
        page.wait_for_selector("#topbar-avatar-btn", timeout=15000)
        page.wait_for_timeout(1000)
        print(f"-> Đăng nhập thành công! URL hiện tại: {page.url}", flush=True)

        # 3. Kiểm thử Cảnh báo An ninh khi nhấn F12
        print("\n[3/5] Kiểm thử bấm phím F12 trên Production...", flush=True)
        page.keyboard.press("F12")
        page.wait_for_timeout(600)
        toast_f12 = page.locator("#toast-container").inner_text()
        print(f"  -> Toast nhận được khi bấm F12: {repr(toast_f12)}", flush=True)
        assert "CẢNH BÁO AN NINH" in toast_f12, f"LỖI: Không hiển thị toast cảnh báo khi bấm F12! Nhận được: {toast_f12}"
        print("  ✓ XÁC NHẬN: Phím tắt F12 ngay lập tức hiển thị Toast Cảnh Báo An Ninh!", flush=True)

        page.wait_for_timeout(3500)

        # 4. Kiểm thử Cảnh báo An ninh khi bấm Ctrl+Shift+I
        print("\n[4/5] Kiểm thử bấm phím Ctrl+Shift+I trên Production...", flush=True)
        page.keyboard.press("Control+Shift+I")
        page.wait_for_timeout(600)
        toast_ctrl_i = page.locator("#toast-container").inner_text()
        print(f"  -> Toast nhận được khi bấm Ctrl+Shift+I: {repr(toast_ctrl_i)}", flush=True)
        assert "CẢNH BÁO AN NINH" in toast_ctrl_i, f"LỖI: Không hiển thị toast khi bấm Ctrl+Shift+I! Nhận được: {toast_ctrl_i}"
        print("  ✓ XÁC NHẬN: Phím tắt Ctrl+Shift+I ngay lập tức hiển thị Toast Cảnh Báo An Ninh!", flush=True)

        # 5. Kiểm tra Căn giữa Tuyệt đối (Dead-Center) và Không đè UI trên Production
        print("\n[5/5] Kiểm tra Căn giữa Tuyệt đối (Dead-Center) và Không đè UI trên Production...", flush=True)
        viewports = [1920, 1680, 1440, 1350, 1280, 1024]
        for w in viewports:
            page.set_viewport_size({"width": w, "height": 800})
            page.wait_for_timeout(400)

            logo = page.locator('#app-topbar a[href="#/"]').bounding_box()
            nav = page.locator('#topbar-navigation-items').bounding_box()
            right = page.locator('#app-topbar > div:last-child').bounding_box()

            nav_center = nav['x'] + nav['width'] / 2.0
            screen_center = w / 2.0
            offset = abs(nav_center - screen_center)

            print(f"\n--- Màn hình rộng {w}px ---", flush=True)
            print(f"  Nav box   : left={nav['x']:.1f}px, width={nav['width']:.1f}px, right={nav['x']+nav['width']:.1f}px", flush=True)
            print(f"  Tâm Nav   : {nav_center:.1f}px vs Tâm Màn Hình: {screen_center:.1f}px => Lệch: {offset:.2f}px", flush=True)
            print(f"  Logo phải : {logo['x']+logo['width']:.1f}px | Cụm điều khiển trái: {right['x']:.1f}px", flush=True)

            # Khẳng định căn giữa tuyệt đối sai số < 1px
            assert offset < 1.0, f"LỖI: Nav không căn giữa tại {w}px! Sai số: {offset:.2f}px"
            # Khẳng định không đè Logo
            assert nav['x'] >= (logo['x'] + logo['width']), f"LỖI: Nav đè Logo tại {w}px!"
            # Khẳng định không đè Controls bên phải
            assert (nav['x'] + nav['width']) <= right['x'], f"LỖI: Nav đè Controls bên phải tại {w}px!"

            print(f"  -> ✓ PASS: Căn giữa chính xác 100% (Lệch {offset:.2f}px < 1px) & Zero Overlap tại {w}px!", flush=True)

        page.screenshot(path=f"{OUTPUT_DIR}/production_deadcenter_1920.png")
        browser.close()

    print("\n" + "=" * 80, flush=True)
    print("TẤT CẢ CÁC BƯỚC XÁC MINH TRÊN PRODUCTION ĐÃ THÀNH CÔNG 100%!", flush=True)
    print("=" * 80, flush=True)

if __name__ == "__main__":
    run_live_tests()
