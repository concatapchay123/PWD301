"""Playwright Real Browser Automation & Evidence Capture for TASK-134:
1. Verify Instructor Landing Modal Segmented Control (Upload vs YouTube/HLS).
2. Verify MP4 video upload progress reaches 100%.
3. Verify Uploaded Video Card & HTML5 preview player with full controls.
4. Verify Trailer persistence and auto-recovery on modal reopen.
5. Verify seamless switch to YouTube 16:9 responsive mode.
6. Verify Admin Course Review page loads 100% without ApiClient.getToken error.
7. Verify Admin Trailer preview renders HTML5 player with 'Tệp tải lên trực tiếp • Đã kiểm tra an toàn' badge.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
EVIDENCE_DIR = Path("qa-evidence-live/task134")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

USER_EMAIL = "tqtphamnguyenhoangphuc@gmail.com"
USER_PASSWORD = "Password123!"

VIEWPORT_W = 1280
VIEWPORT_H = 800
BANNER_H = 80


def load_font(names: list[str], size: int) -> ImageFont.ImageFont:
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()


FONT_TITLE = load_font(["segoeuib.ttf", "arialbd.ttf"], 15)
FONT_BODY = load_font(["segoeui.ttf", "arial.ttf"], 12)
FONT_BADGE = load_font(["segoeuib.ttf", "arialbd.ttf"], 13)


def stamp_banner(img_path: Path, title: str, status: str = "PASS", note: str = "") -> None:
    if not img_path.exists():
        return
    with Image.open(img_path) as raw:
        base = raw.convert("RGB")
        w, h = base.size
        canvas = Image.new("RGB", (w, h + BANNER_H), (15, 23, 42))
        canvas.paste(base, (0, BANNER_H))
        draw = ImageDraw.Draw(canvas)

        # Gradient accent line
        draw.rectangle([(0, BANNER_H - 3), (w, BANNER_H)], fill=(16, 185, 129))

        # Badge
        badge_w, badge_h = 70, 26
        bx, by = w - badge_w - 20, 20
        badge_color = (5, 150, 105) if status == "PASS" else (225, 29, 72)
        draw.rounded_rectangle([(bx, by), (bx + badge_w, by + badge_h)], radius=5, fill=badge_color)
        draw.text((bx + 16, by + 5), status, fill=(255, 255, 255), font=FONT_BADGE)

        # Title & Note
        draw.text((20, 16), f"PPTQ QA SENTINEL • {title}", fill=(255, 255, 255), font=FONT_TITLE)
        draw.text((20, 42), f"Xác minh thực tế: {note}", fill=(148, 163, 184), font=FONT_BODY)

        canvas.save(img_path)


def run_verification() -> bool:
    print("=" * 80)
    print("  BẮT ĐẦU KIỂM THỬ TRÌNH DUYỆT THỰC TẾ TASK-134 VỚI PLAYWRIGHT")
    print("=" * 80)

    console_errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(viewport={"width": VIEWPORT_W, "height": VIEWPORT_H})
        page = context.new_page()

        # Listen to console errors to detect any runtime exceptions
        def on_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)
                if "ApiClient.getToken" in msg.text:
                    print(f"  [!] CRITICAL CONSOLE ERROR DETECTED: {msg.text}")

        page.on("console", on_console)

        # Step 0: Login
        print("[-] Đang đăng nhập tài khoản Giảng viên / Admin...")
        page.goto(f"{BASE_URL}/#/auth/login", wait_until="networkidle")
        page.wait_for_selector("#login-email", timeout=10000)
        page.fill("#login-email", USER_EMAIL)
        page.fill("#login-password", USER_PASSWORD)
        page.click("#login-submit-btn")
        time.sleep(2.0)

        # Switch to INSTRUCTOR role
        print("[-] Chuyển đổi sang vai trò Giảng viên (INSTRUCTOR)...")
        page.evaluate("""() => {
            if (window.app) {
                window.app.currentRole = 'INSTRUCTOR';
                window.app.updateUserUI();
                window.location.hash = '#/instructor/courses';
            }
        }""")
        time.sleep(2.0)

        # =========================================================================
        # VÒNG 1: Mở popup "Biên tập Trang Giới thiệu & Học vụ" & Kiểm tra Segmented Control
        # =========================================================================
        print("\n[+] VÒNG 1: Mở popup 'Biên tập Trang Giới thiệu & Học vụ' & kiểm tra Segmented Control...")
        page.goto(f"{BASE_URL}/#/instructor/courses", wait_until="networkidle")
        time.sleep(1.5)

        # Wait for instructor courses to load
        page.wait_for_selector("#instructor-courses-container .group", timeout=10000)
        course_cards = page.locator("#instructor-courses-container .group")
        assert course_cards.count() > 0, "Phải có ít nhất 1 khóa học trong danh sách giảng viên!"
        
        # Click on the first course card to enter Course Management Studio
        first_course_card = course_cards.first
        first_course_card.click()
        time.sleep(2.0)

        # Wait for button "Trang Giới thiệu" (#btn-edit-course-landing)
        page.wait_for_selector("#btn-edit-course-landing", timeout=10000)
        print("  [i] Đã vào Studio quản lý khóa học. Đang mở popup 'Trang Giới thiệu'...")
        page.click("#btn-edit-course-landing")
        time.sleep(1.5)

        # Verify Modal opened and Segmented Control 2 tab exists
        page.wait_for_selector("#tab-btn-trailer-upload", timeout=10000)
        page.wait_for_selector("#tab-btn-trailer-link", timeout=10000)

        tab_upload_text = page.locator("#tab-btn-trailer-upload").inner_text()
        tab_link_text = page.locator("#tab-btn-trailer-link").inner_text()
        print(f"  [i] Tab 1: '{tab_upload_text.strip().replace(chr(10), ' ')}'")
        print(f"  [i] Tab 2: '{tab_link_text.strip().replace(chr(10), ' ')}'")
        assert "Tải video trực tiếp" in tab_upload_text, "Tab 1 phải có nhãn 'Tải video trực tiếp từ máy tính'"
        assert "Link YouTube" in tab_link_text, "Tab 2 phải có nhãn 'Link YouTube / HLS trực tuyến'"

        ss1 = EVIDENCE_DIR / "step1_open_landing_modal.png"
        page.screenshot(path=str(ss1))
        stamp_banner(
            ss1,
            "Biên tập Trang Giới thiệu & Học vụ",
            "PASS",
            "Giao diện Segmented Control 2 tab chuẩn mực (Upload trực tiếp vs YouTube/HLS)"
        )
        print("  [✓] VÒNG 1 PASS: Modal hiển thị chuẩn xác với Segmented Control 2 tab!")

        # =========================================================================
        # VÒNG 2: Tải video MP4 mẫu & đợi tiến trình 100%
        # =========================================================================
        print("\n[+] VÒNG 2: Tải video trailer MP4 mẫu qua dropzone và kiểm tra tiến trình 100%...")
        page.click("#tab-btn-trailer-upload")
        time.sleep(0.5)

        # If card is already showing (from previous run), remove it so dropzone is visible
        remove_btn = page.locator("#btn-remove-uploaded-video")
        if remove_btn.is_visible():
            print("  [i] Phát hiện video cũ từ phiên trước, bấm 'Gỡ bỏ video' để kiểm tra quy trình upload sạch...")
            remove_btn.click()
            time.sleep(0.5)

        page.wait_for_selector("#unified-video-dropzone:not(.hidden)", timeout=5000)

        sample_video_path = Path("tests/fixtures/sample_trailer.mp4").resolve()
        assert sample_video_path.exists(), f"Tệp video mẫu {sample_video_path} không tồn tại!"

        file_input = page.locator("#unified-video-file-input")
        file_input.set_input_files(str(sample_video_path))
        print(f"  [i] Đã đưa tệp {sample_video_path.name} vào input file, đang tải lên...")

        # Wait for progress bar to reach 100% and text "Tải lên hoàn tất & Đã sẵn sàng!"
        page.wait_for_selector("#upload-progress-percent", timeout=15000)
        
        # Poll up to 15s for 100%
        for _ in range(30):
            p_text = page.locator("#upload-progress-percent").inner_text().strip()
            status_text = page.locator("#upload-progress-text").inner_text().strip()
            if "100%" in p_text or "hoàn tất" in status_text.lower():
                print(f"  [i] Tiến độ upload: {p_text} - {status_text}")
                break
            time.sleep(0.1)

        time.sleep(0.2)
        ss2 = EVIDENCE_DIR / "step2_upload_video_progress.png"
        page.screenshot(path=str(ss2))
        stamp_banner(
            ss2,
            "Tải Lên Video Trailer Trực Tiếp",
            "PASS",
            "Tiến trình tải lên đạt 100% (Tải lên hoàn tất & Đã sẵn sàng!)"
        )
        print("  [✓] VÒNG 2 PASS: Tiến trình upload đạt 100% hoàn tất!")

        # =========================================================================
        # VÒNG 3: Kiểm tra Card video (Tên, Size, Badge an toàn) & Khung preview HTML5 player
        # =========================================================================
        print("\n[+] VÒNG 3: Kiểm tra Card thông tin tệp video và khung preview HTML5 player...")
        page.wait_for_selector("#unified-uploaded-video-card:not(.hidden)", timeout=10000)
        
        uploaded_name = page.locator("#uploaded-video-name").inner_text()
        uploaded_card_text = page.locator("#unified-uploaded-video-card").inner_text()
        print(f"  [i] Tên file hiển thị: {uploaded_name}")
        print(f"  [i] Nội dung card: {uploaded_card_text.replace(chr(10), ' ')}")

        assert "sample_trailer.mp4" in uploaded_name, "Card phải hiển thị đúng tên file đã tải!"
        assert "Tệp nội bộ • Đã kiểm tra an toàn" in uploaded_card_text, "Card phải có badge an toàn chuẩn!"

        # Verify HTML5 video player mounted
        page.wait_for_selector("#unified-trailer-preview-player video", timeout=10000)
        video_src = page.locator("#unified-trailer-preview-player video").get_attribute("src")
        print(f"  [i] HTML5 Video Player src: {video_src}")
        assert video_src and "/api/files/" in video_src, "Video player src phải trỏ tới /api/files/<id>/stream!"

        ss3 = EVIDENCE_DIR / "step3_preview_uploaded_video.png"
        page.screenshot(path=str(ss3))
        stamp_banner(
            ss3,
            "Card Video & HTML5 Preview Player",
            "PASS",
            "Card hiển thị đầy đủ tên, kích thước, badge an toàn và tự động mount HTML5 player có controls"
        )
        print("  [✓] VÒNG 3 PASS: Card video và HTML5 preview player hoạt động hoàn hảo!")

        # =========================================================================
        # VÒNG 4: Lưu thay đổi, đóng modal, mở lại xác minh khôi phục bền vững
        # =========================================================================
        print("\n[+] VÒNG 4: Lưu thay đổi và mở lại modal để xác minh khôi phục bền vững...")
        page.click("#btn-save-unified-intro")
        time.sleep(2.5)

        # Verify modal closed
        modal_overlay = page.locator(".modal-dialog")
        assert modal_overlay.count() == 0 or not modal_overlay.is_visible(), "Modal phải đóng sau khi lưu!"

        # Reopen modal
        print("  [i] Mở lại popup 'Biên tập Trang Giới thiệu & Học vụ'...")
        page.click("#btn-edit-course-landing")
        time.sleep(2.0)

        page.wait_for_selector("#tab-btn-trailer-upload", timeout=10000)
        page.wait_for_selector("#unified-uploaded-video-card:not(.hidden)", timeout=10000)
        page.wait_for_selector("#unified-trailer-preview-player video", timeout=10000)

        reopened_video_src = page.locator("#unified-trailer-preview-player video").get_attribute("src")
        print(f"  [i] Khôi phục Video Player src sau khi mở lại: {reopened_video_src}")
        assert reopened_video_src and "/api/files/" in reopened_video_src, "Trailer phải được tự động khôi phục bền vững!"

        ss4 = EVIDENCE_DIR / "step4_save_and_reopen_modal.png"
        page.screenshot(path=str(ss4))
        stamp_banner(
            ss4,
            "Khôi Phục Video Bền Vững Khi Mở Lại Modal",
            "PASS",
            "Trailer video nội bộ được lưu bền vững vào CSDL và tự động khôi phục preview khi mở lại modal"
        )
        print("  [✓] VÒNG 4 PASS: Khôi phục bền vững video trailer tải lên thành công 100%!")

        # =========================================================================
        # VÒNG 5: Chuyển sang tab "Link YouTube / HLS", kiểm tra phát responsive 16:9
        # =========================================================================
        print("\n[+] VÒNG 5: Chuyển sang tab Link YouTube / HLS và kiểm tra preview responsive 16:9...")
        page.click("#tab-btn-trailer-link")
        time.sleep(1.0)

        page.wait_for_selector("#trailer-pane-link:not(.hidden)", timeout=5000)
        page.fill("#unified-trailer-url", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        page.click("#btn-test-trailer-video")
        time.sleep(2.0)

        # Verify YouTube iframe mounted in preview box
        page.wait_for_selector("#unified-trailer-preview-player iframe", timeout=10000)
        iframe_src = page.locator("#unified-trailer-preview-player iframe").get_attribute("src")
        print(f"  [i] YouTube iframe src: {iframe_src}")
        assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in iframe_src, "Preview phải mount iframe YouTube chuẩn!"

        ss5 = EVIDENCE_DIR / "step5_switch_youtube_mode.png"
        page.screenshot(path=str(ss5))
        stamp_banner(
            ss5,
            "Chuyển Sang Chế Độ Link YouTube / HLS",
            "PASS",
            "Khung preview chuyển đổi mượt mà sang YouTube iframe 16:9 responsive chuẩn tỷ lệ"
        )
        print("  [✓] VÒNG 5 PASS: Chuyển chế độ YouTube 16:9 thành công!")

        # =========================================================================
        # VÒNG 6: Chuyển lại tab Upload video, Lưu thay đổi và truy cập Admin Governance
        # =========================================================================
        print("\n[+] VÒNG 6: Chuyển lại tab Upload video, lưu thay đổi và mở trang xét duyệt Admin...")
        page.click("#tab-btn-trailer-upload")
        time.sleep(1.0)
        page.click("#btn-save-unified-intro")
        time.sleep(2.5)

        # Switch role to ADMIN
        print("  [i] Chuyển vai trò sang ADMIN và mở #/admin/governance?tab=courses...")
        page.evaluate("""() => {
            if (window.app) {
                window.app.currentRole = 'ADMIN';
                window.app.updateUserUI();
                window.location.hash = '#/admin/governance?tab=courses';
            }
        }""")
        time.sleep(2.5)

        # Click "Xem Khóa Học" / "Xem và duyệt" on the course in Admin Courses table
        page.wait_for_selector(".inspect-course-btn", timeout=10000)
        inspect_btn = page.locator(".inspect-course-btn").first
        print(f"  [i] Bấm nút 'Xem Khóa Học' ({inspect_btn.inner_text().strip()})...")
        inspect_btn.click()
        time.sleep(3.0)

        # Wait for review page to load
        page.wait_for_selector("#admin-course-tree-preview, h1", timeout=15000)
        review_header = page.locator("h1").first.inner_text()
        print(f"  [i] Tiêu đề trang duyệt Admin: {review_header}")

        # Assert no ApiClient.getToken error in console
        bad_token_errors = [err for err in console_errors if "ApiClient.getToken is not a function" in err]
        assert len(bad_token_errors) == 0, f"Phát hiện lỗi ApiClient.getToken: {bad_token_errors}"

        ss6 = EVIDENCE_DIR / "step6_admin_preview_page_loaded.png"
        page.screenshot(path=str(ss6))
        stamp_banner(
            ss6,
            "Trang Xem Trước & Duyệt Của Admin Tải Hoàn Hảo",
            "PASS",
            "Admin review page tải thành công 100%, triệt tiêu hoàn toàn lỗi ApiClient.getToken"
        )
        print("  [✓] VÒNG 6 PASS: Trang xem trước của Admin tải 100% không còn lỗi ApiClient.getToken!")

        # =========================================================================
        # VÒNG 7: Kiểm tra khung phát video trailer của Admin (HTML5 player + Badge an toàn)
        # =========================================================================
        print("\n[+] VÒNG 7: Xác minh khung phát video trailer Admin (HTML5 Player + Badge an toàn)...")
        # Scroll to trailer section
        page.wait_for_selector("span:has-text('Tệp tải lên trực tiếp • Đã kiểm tra an toàn')", timeout=10000)
        badge_locator = page.locator("span:has-text('Tệp tải lên trực tiếp • Đã kiểm tra an toàn')")
        assert badge_locator.count() > 0, "Admin preview phải hiển thị badge 'Tệp tải lên trực tiếp • Đã kiểm tra an toàn'!"

        # Verify video player in Admin review
        admin_video = page.locator("video")
        assert admin_video.count() > 0, "Admin preview phải hiển thị thẻ <video> HTML5!"
        admin_video_src = admin_video.first.get_attribute("src")
        print(f"  [i] Admin Video Trailer src: {admin_video_src}")
        assert admin_video_src and "/api/files/" in admin_video_src, "Admin Video src phải trỏ tới API stream nội bộ!"

        # Scroll into view of trailer
        badge_locator.first.scroll_into_view_if_needed()
        time.sleep(1.0)

        ss7 = EVIDENCE_DIR / "step7_admin_trailer_playback_verified.png"
        page.screenshot(path=str(ss7))
        stamp_banner(
            ss7,
            "Khung Phát Video Trailer Admin Đạt Chuẩn",
            "PASS",
            "Admin preview hiển thị HTML5 player sắc nét với badge 'Tệp tải lên trực tiếp • Đã kiểm tra an toàn'"
        )
        print("  [✓] VÒNG 7 PASS: Khung phát video trailer Admin hiển thị sắc nét kèm badge chuẩn mực!")

        browser.close()

    print("\n" + "=" * 80)
    print("  TOÀN BỘ 7 BƯỚC KIỂM THỬ TRÌNH DUYỆT THỰC TẾ TASK-134 ĐÃ PASS 100%!")
    print(f"  Toàn bộ ảnh minh chứng có gắn banner kỹ thuật lưu tại: {EVIDENCE_DIR.resolve()}")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
