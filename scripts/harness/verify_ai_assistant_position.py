"""Verify AI Assistant Position: Always anchored to Bottom-Right Corner.
Verifies:
1. Launcher starts at bottom-right.
2. Clicking launcher opens drawer anchored at bottom-right (NOT top-left).
3. Auto-hide launcher while open so it doesn't obscure drawer.
4. Drawer closes cleanly, launcher restores at bottom-right.
5. Reload page preserves default bottom-right anchoring.
"""
import os
import sys
import threading
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root / "src")]
os.chdir(root)

evidence_dir = root / "artifacts" / "screenshots"
evidence_dir.mkdir(parents=True, exist_ok=True)

test_db_path = root / ".superpowers/pwd301_test_ai_pos.sqlite"
if test_db_path.exists():
    try:
        test_db_path.unlink()
    except Exception:
        pass

os.environ["TEST_DATABASE_URL"] = "sqlite:///" + test_db_path.as_posix()
os.environ["PWD301_TEST_DB_DISPOSABLE"] = "1"
os.environ["APP_ENV"] = "testing"

from backend import create_app
from backend.extensions import db

app = create_app(
    "testing",
    config_override={
        "FILE_STORAGE_ROOT": root / ".superpowers" / "storage_ai_pos",
        "FILE_QUARANTINE_ROOT": root / ".superpowers" / "quarantine_ai_pos",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "ai-pos-secret-test-key",
    },
)

with app.app_context():
    db.create_all()

from werkzeug.serving import make_server

server = make_server("127.0.0.1", 52199, app, threaded=True)
srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
srv_thread.start()
print("[Server] Test server listening at http://127.0.0.1:52199")
time.sleep(1.0)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("[Test] Navigating to http://127.0.0.1:52199...")
        page.goto("http://127.0.0.1:52199/#/auth/login", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # 1. Inspect Launcher Position
        launcher = page.locator("#floating-ai-launcher")
        assert launcher.is_visible(), "Floating AI launcher must be visible"
        l_box = launcher.bounding_box()
        print(f"[Launcher] Position: x={l_box['x']:.1f}, y={l_box['y']:.1f}, w={l_box['width']:.1f}, h={l_box['height']:.1f}")
        
        # Must be in bottom-right quadrant (x > 1150, y > 700 for 1280x800)
        assert l_box["x"] > 1100, f"Launcher x={l_box['x']} should be near right edge (>1100)"
        assert l_box["y"] > 650, f"Launcher y={l_box['y']} should be near bottom edge (>650)"

        # 2. Click Launcher to Open Drawer
        print("[Action] Clicking launcher to open drawer...")
        launcher.click()
        page.wait_for_timeout(500)

        drawer = page.locator("#floating-ai-drawer")
        assert drawer.is_visible(), "Drawer must be visible after click"
        d_box = drawer.bounding_box()
        print(f"[Drawer] Position: x={d_box['x']:.1f}, y={d_box['y']:.1f}, w={d_box['width']:.1f}, h={d_box['height']:.1f}")

        # CRITICAL CHECK: Drawer MUST be at bottom-right corner, NOT top-left
        # Right edge: d_box['x'] + d_box['width'] should be within 30px of 1280 (i.e. ~1260)
        # Bottom edge: d_box['y'] + d_box['height'] should be within 30px of 800 (i.e. ~780)
        drawer_right = d_box["x"] + d_box["width"]
        drawer_bottom = d_box["y"] + d_box["height"]
        print(f"[Drawer Check] Right edge = {drawer_right:.1f} (viewport width = 1280), Bottom edge = {drawer_bottom:.1f} (viewport height = 800)")

        assert drawer_right >= 1250, f"Drawer right edge {drawer_right} must be close to 1280"
        assert drawer_bottom >= 770, f"Drawer bottom edge {drawer_bottom} must be close to 800"
        assert d_box["x"] > 800, f"Drawer left x={d_box['x']} must be on the right side of the screen (>800), NOT top-left!"
        assert d_box["y"] > 200, f"Drawer top y={d_box['y']} must be > 200, NOT top-left!"

        # Launcher must be hidden while drawer is open
        assert not launcher.is_visible(), "Launcher must be hidden when drawer is open to avoid collision"

        # Capture Open Screenshot
        open_shot = evidence_dir / "ai_assistant_bottom_right_open.png"
        page.screenshot(path=str(open_shot))
        print(f"[Evidence] Saved open drawer screenshot to: {open_shot}")

        # 3. Close Drawer
        print("[Action] Clicking close button...")
        close_btn = page.locator("#floating-ai-close-btn")
        close_btn.click()
        page.wait_for_timeout(500)

        assert not drawer.is_visible(), "Drawer must be hidden after closing"
        assert launcher.is_visible(), "Launcher must be visible after closing drawer"
        l_box_after = launcher.bounding_box()
        print(f"[Launcher Restored] Position: x={l_box_after['x']:.1f}, y={l_box_after['y']:.1f}")
        assert l_box_after["x"] > 1100, f"Restored launcher x={l_box_after['x']} must be near right edge"
        assert l_box_after["y"] > 650, f"Restored launcher y={l_box_after['y']} must be near bottom edge"

        # Capture Closed Screenshot
        closed_shot = evidence_dir / "ai_assistant_bottom_right_closed.png"
        page.screenshot(path=str(closed_shot))
        print(f"[Evidence] Saved closed drawer screenshot to: {closed_shot}")

        # 4. Reload page to verify persistence of default position
        print("[Action] Reloading page to verify persistence...")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(500)

        launcher_reloaded = page.locator("#floating-ai-launcher")
        assert launcher_reloaded.is_visible(), "Launcher visible after reload"
        l_reloaded_box = launcher_reloaded.bounding_box()
        print(f"[Launcher After Reload] Position: x={l_reloaded_box['x']:.1f}, y={l_reloaded_box['y']:.1f}")
        assert l_reloaded_box["x"] > 1100, "Launcher after reload must remain at bottom right"
        assert l_reloaded_box["y"] > 650, "Launcher after reload must remain at bottom right"

        # Open drawer again after reload
        launcher_reloaded.click()
        page.wait_for_timeout(500)
        drawer_reloaded = page.locator("#floating-ai-drawer")
        assert drawer_reloaded.is_visible(), "Drawer open after reload"
        d_reloaded_box = drawer_reloaded.bounding_box()
        print(f"[Drawer After Reload] x={d_reloaded_box['x']:.1f}, y={d_reloaded_box['y']:.1f}, right={d_reloaded_box['x'] + d_reloaded_box['width']:.1f}, bottom={d_reloaded_box['y'] + d_reloaded_box['height']:.1f}")
        assert d_reloaded_box["x"] + d_reloaded_box["width"] >= 1250, "Drawer after reload must be at bottom right"
        assert d_reloaded_box["y"] + d_reloaded_box["height"] >= 770, "Drawer after reload must be at bottom right"

        print("[SUCCESS] All AI Assistance Bottom-Right positioning verifications PASSED 100%!")

        browser.close()
finally:
    server.shutdown()
    srv_thread.join(timeout=2.0)
