# -*- coding: utf-8 -*-
"""Real browser QA verification script on live VPS for Topbar responsive scaling."""

import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

OUTPUT_DIR = "qa-evidence-live/topbar_vps"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_browser_verification():
    print("=" * 80)
    print("KIỂM THỬ TRÌNH DUYỆT THẬT (PLAYWRIGHT) TRÊN PRODUCTION: https://pptq.id.vn")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("[1/5] Điều hướng tới https://pptq.id.vn/#/auth/login...")
        page.goto("https://pptq.id.vn/#/auth/login")
        page.wait_for_selector("#login-email", timeout=15000)

        print("[2/5] Đăng nhập Admin Hoàng Phúc (tqtphamnguyenhoangphuc@gmail.com)...")
        page.fill("#login-email", "tqtphamnguyenhoangphuc@gmail.com")
        page.fill("#login-password", "Password123!")
        page.click("#login-submit-btn")

        page.wait_for_selector("#topbar-avatar-btn", timeout=15000)
        print("-> Đăng nhập thành công! URL:", page.url)

        # Đợi topbar render hoàn tất
        page.wait_for_timeout(1000)

        # --- VIEWPORT 1: 1920x1080 ---
        print("\n[3/5] Kiểm tra Viewport 1920x1080 (Màn hình lớn)...")
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(500)
        page.screenshot(path=f"{OUTPUT_DIR}/1920x1080_topbar.png")

        more_btn_visible_1920 = page.locator("#topbar-admin-more-btn").is_visible()
        print(f"  - 1920x1080 More Button Visible: {more_btn_visible_1920} (Kỳ vọng: False - hiện đủ 8 tab)")
        assert not more_btn_visible_1920, "More button phải ẩn ở 1920px (hiện đủ 8 tab)"

        # --- VIEWPORT 2: 1280x720 ---
        print("\n[4/5] Kiểm tra Viewport 1280x720 (Laptop 13-14 inch phổ thông)...")
        page.set_viewport_size({"width": 1280, "height": 720})
        page.wait_for_timeout(500)

        logo_box = page.locator("#app-topbar a[href='#/']").bounding_box()
        nav_box = page.locator("#topbar-navigation-items").bounding_box()
        avatar_box = page.locator("#topbar-avatar-btn").bounding_box()

        print(f"  - Bounding box Logo: right={logo_box['x'] + logo_box['width']:.1f}px")
        print(f"  - Bounding box Nav : left={nav_box['x']:.1f}px, right={nav_box['x'] + nav_box['width']:.1f}px")
        print(f"  - Bounding box Right Controls: left={avatar_box['x']:.1f}px")

        # Kiểm tra tuyệt đối không có va chạm / đè UI
        assert nav_box['x'] >= (logo_box['x'] + logo_box['width']), "LỖI: Nav đè lên Logo bên trái!"
        assert (nav_box['x'] + nav_box['width']) <= avatar_box['x'], "LỖI: Nav đè lên Avatar / Controls bên phải!"
        print("  -> ✓ XÁC NHẬN ZERO-OVERLAP: Thanh điều hướng nằm gọn giữa Logo và Controls, không đè UI!")

        more_btn_visible_1280 = page.locator("#topbar-admin-more-btn").is_visible()
        print(f"  - 1280x720 More Button Visible: {more_btn_visible_1280} (Kỳ vọng: True)")
        assert more_btn_visible_1280, "Nút Thêm phải hiện ở 1280px"

        # Click nút Thêm để kiểm tra menu thả xuống
        page.click("#topbar-admin-more-btn")
        page.wait_for_timeout(500)
        dropdown_visible = page.locator("#topbar-admin-more-dropdown").is_visible()
        print(f"  - Dropdown 'Thêm' hiển thị khi click: {dropdown_visible} (Kỳ vọng: True)")
        assert dropdown_visible, "Dropdown 'Thêm' không hiển thị"

        page.screenshot(path=f"{OUTPUT_DIR}/1280x720_admin_more_dropdown.png")

        # --- VIEWPORT 3: 1024x768 ---
        print("\n[5/5] Kiểm tra Viewport 1024x768 (Tablet Landscape / Laptop nhỏ)...")
        page.set_viewport_size({"width": 1024, "height": 768})
        page.wait_for_timeout(500)

        nav_box_1024 = page.locator("#topbar-navigation-items").bounding_box()
        avatar_box_1024 = page.locator("#topbar-avatar-btn").bounding_box()
        logo_box_1024 = page.locator("#app-topbar a[href='#/']").bounding_box()

        assert nav_box_1024['x'] >= (logo_box_1024['x'] + logo_box_1024['width']), "LỖI 1024px: Nav đè Logo!"
        assert (nav_box_1024['x'] + nav_box_1024['width']) <= avatar_box_1024['x'], "LỖI 1024px: Nav đè Avatar!"
        print("  -> ✓ XÁC NHẬN ZERO-OVERLAP tại 1024x768!")

        page.screenshot(path=f"{OUTPUT_DIR}/1024x768_topbar.png")

        browser.close()

    print("\n" + "=" * 80)
    print("TẤT CẢ CÁC BƯỚC KIỂM THỬ TRÌNH DUYỆT THẬT TRÊN LIVE VPS ĐÃ THÀNH CÔNG 100%!")
    print("=" * 80)

if __name__ == "__main__":
    run_browser_verification()
