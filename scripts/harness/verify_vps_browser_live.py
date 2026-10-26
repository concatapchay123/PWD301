import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def run():
    print("Testing live VPS https://pptq.id.vn ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://pptq.id.vn/", wait_until="networkidle")
        
        # Test 1: Check F12 alert
        print("Testing F12 keydown...")
        page.keyboard.press("F12")
        page.wait_for_selector(".toast-item, #toast-container > div", timeout=5000)
        toast_text = page.locator("#toast-container").inner_text()
        print("Toast on F12:\n" + toast_text)
        assert "CẢNH BÁO AN NINH" in toast_text, "Missing alert text"
        assert "🛡" not in toast_text, "Found shield emoji in toast!"
        print("✓ F12 toast has NO shield icon!")

        # Test 2: Check Ctrl+Shift+I alert
        page.wait_for_timeout(3500)
        print("Testing Ctrl+Shift+I keydown...")
        page.keyboard.press("Control+Shift+I")
        page.wait_for_selector(".toast-item, #toast-container > div", timeout=5000)
        toast_ctrl_i = page.locator("#toast-container").inner_text()
        print("Toast on Ctrl+Shift+I:\n" + toast_ctrl_i)
        assert "CẢNH BÁO AN NINH" in toast_ctrl_i, "Missing alert text"
        assert "🛡" not in toast_ctrl_i, "Found shield emoji in toast!"
        print("✓ Ctrl+Shift+I toast has NO shield icon!")
        
        browser.close()
        print("ALL LIVE TESTS PASSED 100%!")

if __name__ == "__main__":
    run()
