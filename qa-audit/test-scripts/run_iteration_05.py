import json
import sys
import io
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"
ITERATION_DIR = Path("qa-audit/iterations/iteration-05/evidence")
GLOBAL_SCREENSHOTS = Path("qa-audit/screenshots")
RESULTS_FILE = Path("qa-audit/iterations/iteration-05/results.json")

ITERATION_DIR.mkdir(parents=True, exist_ok=True)
GLOBAL_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

def annotate(img_path: str, test_id: str, title: str, description: str, status: str = "PASS"):
    img = Image.open(img_path)
    banner_height = 80
    new_img = Image.new("RGB", (img.width, img.height + banner_height), (24, 24, 27))
    new_img.paste(img, (0, banner_height))
    draw = ImageDraw.Draw(new_img)
    
    status_color = (22, 163, 74) if status == "PASS" else (220, 38, 38)
    draw.rectangle([(20, 18), (105, 42)], fill=status_color)
    draw.text((32, 22), status, fill=(255, 255, 255))
    
    draw.text((120, 20), f"[{test_id}] {title}", fill=(244, 244, 245))
    draw.text((120, 48), f"Proof: {description}", fill=(161, 161, 170))
    
    new_img.save(img_path)
    # Also copy to global screenshots
    dest_global = GLOBAL_SCREENSHOTS / Path(img_path).name
    new_img.save(dest_global)

def run():
    print("[*] Launching Real Chrome Browser via Playwright for Iteration 05...")
    results = {
        "iteration": 5,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_cases": []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        # Initial login as Student
        page.goto(f"{BASE_URL}/#/auth")
        page.wait_for_selector("#login-email", timeout=10000)
        page.fill("#login-email", "student1@pwd301.local")
        page.fill("#login-password", "Password123!")
        page.click("button[type='submit']")
        page.wait_for_url("**/#/student/dashboard", timeout=10000)
        page.wait_for_timeout(1500)
        
        # -----------------------------------------------------------------------
        # TC-IT05-001: Vietnamese Unicode Diacritics Storage & Presentation Integrity
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT05-001: Vietnamese Unicode Diacritics...")
        tc01 = {
            "id": "TC-IT05-001",
            "name": "Vietnamese Unicode Diacritics Storage & Presentation",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        page.goto(f"{BASE_URL}/#/student/settings")
        page.wait_for_selector("#settings-display-name", timeout=8000)
        
        vietnamese_name = "Nguyễn Thị Ánh Tuyết (Kỹ Sư Phần Mềm)"
        page.fill("#settings-display-name", vietnamese_name)
        page.click("#btn-save-profile")
        page.wait_for_timeout(2000)
        
        # Refresh and inspect stored display name
        page.reload()
        page.wait_for_selector("#settings-display-name", timeout=8000)
        stored_name = page.input_value("#settings-display-name")
        topbar_name = page.inner_text("#topbar-user-name").strip()
        
        tc01["notes"].append(f"Input: '{vietnamese_name}', Stored in input: '{stored_name}', Topbar: '{topbar_name}'")
        
        if stored_name != vietnamese_name or not (vietnamese_name.startswith(topbar_name) or topbar_name in vietnamese_name):
            tc01["status"] = "FAIL"
            tc01["notes"].append("Unicode tone mark corruption detected upon saving or reloading.")
            
        img1_path = ITERATION_DIR / "IT05_TC01_vietnamese_unicode_integrity.png"
        page.screenshot(path=str(img1_path))
        annotate(str(img1_path), "TC-IT05-001", "Vietnamese Unicode Diacritics", f"Persisted tone marks: {stored_name}", tc01["status"])
        tc01["evidence"].append(str(img1_path.name))
        results["test_cases"].append(tc01)
        
        # -----------------------------------------------------------------------
        # TC-IT05-002: Client-Side Empty Required Field Validation
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT05-002: Empty Required Field Validation...")
        tc02 = {
            "id": "TC-IT05-002",
            "name": "Client-Side Empty Required Field Validation",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Clear field and enter single space
        page.fill("#settings-display-name", "   ")
        page.click("#btn-save-profile")
        page.wait_for_timeout(500)
        
        # Check validation toast or HTML5 invalid state
        toast_text = page.inner_text("#toast-container") if page.is_visible("#toast-container") else ""
        is_invalid = page.evaluate("() => !document.getElementById('settings-display-name').checkValidity()")
        
        tc02["notes"].append(f"Validation toast: '{toast_text}', Field validity check: is_invalid={is_invalid}")
        
        if not is_invalid and "Vui lòng nhập họ và tên hiển thị hợp lệ" not in toast_text:
            tc02["status"] = "FAIL"
            tc02["notes"].append("Whitespace-only name submitted without client-side blocking or warning.")
            
        img2_path = ITERATION_DIR / "IT05_TC02_empty_field_validation.png"
        page.screenshot(path=str(img2_path))
        annotate(str(img2_path), "TC-IT05-002", "Empty Field Validation", f"Blocked: is_invalid={is_invalid}, toast={toast_text[:40]}", tc02["status"])
        tc02["evidence"].append(str(img2_path.name))
        results["test_cases"].append(tc02)
        
        # -----------------------------------------------------------------------
        # TC-IT05-003: Email Format Boundary Validation
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT05-003: Email Format Boundary Validation...")
        tc03 = {
            "id": "TC-IT05-003",
            "name": "Email Format Boundary Validation",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Open auth page in an isolated unauthenticated browser context
        incognito_ctx = browser.new_context()
        auth_page = incognito_ctx.new_page()
        auth_page.goto(f"{BASE_URL}/#/auth")
        auth_page.wait_for_selector("#tab-nav-register", timeout=8000)
        auth_page.click("#tab-nav-register")
        auth_page.wait_for_selector("#register-email", timeout=8000)
        
        # Test invalid email format
        auth_page.fill("#register-email", "not-a-valid-email-string")
        auth_page.fill("#register-name", "Test User")
        auth_page.fill("#register-password", "Password123!")
        
        email_valid = auth_page.evaluate("() => document.getElementById('register-email').checkValidity()")
        tc03["notes"].append(f"Email 'not-a-valid-email-string' checkValidity: {email_valid}")
        
        if email_valid:
            tc03["status"] = "FAIL"
            tc03["notes"].append("Browser failed to flag malformed email as invalid.")
            
        img3_path = ITERATION_DIR / "IT05_TC03_email_format_boundary.png"
        auth_page.screenshot(path=str(img3_path))
        annotate(str(img3_path), "TC-IT05-003", "Email Format Boundary", f"Malformed email flagged invalid: {not email_valid}", tc03["status"])
        tc03["evidence"].append(str(img3_path.name))
        results["test_cases"].append(tc03)
        incognito_ctx.close()
        
        # -----------------------------------------------------------------------
        # TC-IT05-004: Rapid Double-Submit Button Locking Protection
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT05-004: Rapid Double-Submit Protection...")
        tc04 = {
            "id": "TC-IT05-004",
            "name": "Rapid Double-Submit Button Locking Protection",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        page.fill("#settings-display-name", "Lê Hoàng Long (Senior QA)")
        
        # Double click quickly and verify disabled state during submission
        double_click_eval = page.evaluate("""() => {
            const btn = document.getElementById('btn-save-profile');
            const form = document.getElementById('profile-settings-form');
            btn.click();
            const disabledImmediately = btn.disabled;
            btn.click(); // second click attempt
            return {
                disabledImmediately,
                buttonInnerHTML: btn.innerHTML
            };
        }""")
        
        tc04["notes"].append(f"Double-click evaluation: {double_click_eval}")
        page.wait_for_timeout(1500)
        
        if not double_click_eval["disabledImmediately"] and "Đang lưu" not in double_click_eval["buttonInnerHTML"]:
            tc04["status"] = "FAIL"
            tc04["notes"].append("Submit button was not locked or disabled on first dispatch.")
            
        img4_path = ITERATION_DIR / "IT05_TC04_double_submit_locking.png"
        page.screenshot(path=str(img4_path))
        annotate(str(img4_path), "TC-IT05-004", "Double-Submit Protection", f"Locked: {double_click_eval['disabledImmediately']}, text: {double_click_eval['buttonInnerHTML'][:30]}", tc04["status"])
        tc04["evidence"].append(str(img4_path.name))
        results["test_cases"].append(tc04)
        
        # -----------------------------------------------------------------------
        # TC-IT05-005: Extreme Input Length Boundary Handling
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT05-005: Extreme Input Length Boundary...")
        tc05 = {
            "id": "TC-IT05-005",
            "name": "Extreme Input Length Boundary Handling",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # HTML maxlength test: enter 500 characters into input with maxlength=100
        long_string = "A" * 500
        page.fill("#settings-display-name", long_string)
        actual_input_val = page.input_value("#settings-display-name")
        max_length_attr = page.get_attribute("#settings-display-name", "maxlength")
        
        tc05["notes"].append(f"Entered 500 chars, Actual length: {len(actual_input_val)}, maxlength attr: {max_length_attr}")
        
        # Also test API payload rejection boundary directly
        api_boundary_eval = page.evaluate("""async () => {
            try {
                const res = await ApiClient.updateProfile({ display_name: 'B'.repeat(500) });
                return { ok: true, res };
            } catch(e) {
                return { ok: false, status: e.status, code: e.code, message: e.message };
            }
        }""")
        
        tc05["notes"].append(f"API extreme payload response: {api_boundary_eval}")
        
        if len(actual_input_val) > 100:
            tc05["status"] = "FAIL"
            tc05["notes"].append("Client input failed to enforce maxlength=100.")
            
        if api_boundary_eval.get("status") == 500:
            tc05["status"] = "FAIL"
            tc05["notes"].append("Backend crashed with 500 Internal Server Error on extreme length payload.")
            
        img5_path = ITERATION_DIR / "IT05_TC05_length_boundary_handling.png"
        page.screenshot(path=str(img5_path))
        annotate(str(img5_path), "TC-IT05-005", "Extreme Length Boundary", f"Client capped at {len(actual_input_val)} chars (max={max_length_attr}), API safe: status={api_boundary_eval.get('status')}", tc05["status"])
        tc05["evidence"].append(str(img5_path.name))
        results["test_cases"].append(tc05)
        
        # -----------------------------------------------------------------------
        # TC-IT05-006: Form Input XSS Sanitization & HTML Escape
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT05-006: Form Input XSS Sanitization...")
        tc06 = {
            "id": "TC-IT05-006",
            "name": "Form Input XSS Sanitization & HTML Escape",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        xss_payload = "<script>window.__xss_detected=true;</script><b>SafeName</b>"
        page.fill("#settings-display-name", xss_payload)
        page.click("#btn-save-profile")
        page.wait_for_timeout(1500)
        
        # Check if script executed
        xss_executed = page.evaluate("() => window.__xss_detected === true")
        topbar_html = page.inner_html("#topbar-user-name")
        tc06["notes"].append(f"XSS executed: {xss_executed}, Rendered topbar HTML: {topbar_html}")
        
        if xss_executed or "<script>" in topbar_html:
            tc06["status"] = "FAIL"
            tc06["notes"].append("XSS vulnerability confirmed: script executed or unescaped HTML tag present in DOM.")
            
        img6_path = ITERATION_DIR / "IT05_TC06_xss_sanitization_defense.png"
        page.screenshot(path=str(img6_path))
        annotate(str(img6_path), "TC-IT05-006", "XSS Sanitization Defense", f"XSS executed: {xss_executed}, Safe HTML: {topbar_html}", tc06["status"])
        tc06["evidence"].append(str(img6_path.name))
        results["test_cases"].append(tc06)
        
        browser.close()

    # Save results to JSON
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"[*] Iteration 05 Execution Complete. Saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run()
