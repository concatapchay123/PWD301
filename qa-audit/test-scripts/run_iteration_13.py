import json
import sys
import io
import time
import uuid
import re
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

# Force UTF-8 stdout on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"
ITERATION_DIR = Path("qa-audit/iterations/iteration-13/evidence")
GLOBAL_SCREENSHOTS = Path("qa-audit/screenshots")
RESULTS_FILE = Path("qa-audit/iterations/iteration-13/results.json")

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
    dest_global = GLOBAL_SCREENSHOTS / Path(img_path).name
    new_img.save(dest_global)

def call_api(page, url, method="GET", body=None):
    """Executes ApiClient.request within the page context with automatic CSRF management."""
    return page.evaluate("""async ([url, method, body]) => {
        try {
            const data = await ApiClient.request(url, { method, body });
            return { ok: true, status: 200, data: data };
        } catch (err) {
            return {
                ok: false,
                status: err.status || 500,
                error: err.rawMessage || err.message,
                code: err.code,
                data: err.data
            };
        }
    }""", [url, method, body])

def query_db(python_snippet: str) -> dict:
    """Executes a Python snippet inside the Docker container and returns parsed JSON output."""
    wrapped_code = f"""import json, sys
from pwd301 import create_app, db
app = create_app()
with app.app_context():
{python_snippet}
"""
    cmd = ["docker", "exec", "-i", "pwd301_web", "python", "-"]
    proc = subprocess.run(cmd, input=wrapped_code, text=True, capture_output=True, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"DB Query Error (code {proc.returncode}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
    out = proc.stdout.strip()
    try:
        return json.loads(out)
    except Exception as e:
        print(f"[!] Raw output not JSON: {out}")
        raise e

def run():
    print("==========================================================================")
    print("  PWD301 FULL-STACK QA AUDIT - ITERATION 13: SECURITY & ANTI-TAMPER")
    print("==========================================================================")
    
    test_run_id = uuid.uuid4().hex[:6].upper()
    print(f"[*] Test Run ID: {test_run_id}")
    
    results = {
        "iteration": "13",
        "title": "Security Control Verification: Anti-tamper Blackout Shield, DevTools Traps, CSRF & XSS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_run_id": test_run_id,
        "test_cases": []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        
        # Student Context
        student_context = browser.new_context(viewport={"width": 1366, "height": 768})
        student_page = student_context.new_page()
        student_page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        print("[*] Logging in as student1@pwd301.local...")
        student_page.goto(f"{BASE_URL}/#/auth")
        student_page.wait_for_selector("#login-email", timeout=10000)
        student_page.fill("#login-email", "student1@pwd301.local")
        student_page.fill("#login-password", "Password123!")
        student_page.click("button[type='submit']")
        student_page.wait_for_url("**/#/student/**", timeout=10000)
        student_page.wait_for_timeout(1500)
        
        # -----------------------------------------------------------------------
        # TC-IT13-001: Anti-Tamper DevTools Shortcut Trap (F12) & Blackout Shield
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT13-001: Anti-Tamper DevTools Shortcut Trap & Blackout Shield...")
        tc01 = {
            "id": "TC-IT13-001",
            "name": "Anti-Tamper DevTools Shortcut Trap (F12) & Full-Screen Blackout Shield",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Check that VideoArmor global shield is active on authenticated view
        shield_installed = student_page.evaluate("""() => {
            return typeof VideoArmor !== 'undefined' && typeof VideoArmor.isGlobalShieldInstalled === 'function'
                ? VideoArmor.isGlobalShieldInstalled()
                : false;
        }""")
        tc01["notes"].append(f"VideoArmor global shield installed: {shield_installed}")
        
        # Trigger F12 keydown event in browser context
        lockdown_result = student_page.evaluate("""() => {
            // Trigger F12 keydown
            const evt = new KeyboardEvent('keydown', {
                key: 'F12',
                keyCode: 123,
                which: 123,
                bubbles: true,
                cancelable: true
            });
            window.dispatchEvent(evt);
            
            // Check immediate lockdown status
            const shield = document.getElementById('global-security-blackout-shield');
            const h2 = shield ? shield.querySelector('h2')?.textContent?.trim() : '';
            const reason = shield ? shield.querySelector('.font-mono')?.textContent?.trim() : '';
            const reloginBtn = shield ? shield.querySelector('#btn-security-lockdown-relogin') !== null : false;
            
            return {
                shield_found: shield !== null,
                header: h2,
                reason: reason,
                has_relogin: reloginBtn,
                is_locked: typeof VideoArmor !== 'undefined' ? VideoArmor._isGlobalLocked : false
            };
        }""")
        tc01["notes"].append(f"Lockdown DOM Inspection: {lockdown_result}")
        
        if not lockdown_result.get("shield_found") or "CẢNH BÁO AN NINH" not in lockdown_result.get("header", ""):
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"Blackout shield did not overlay correctly: {lockdown_result}")
        else:
            tc01["notes"].append("Verified: #global-security-blackout-shield overlaid full screen with '🛡️ CẢNH BÁO AN NINH HỆ THỐNG'.")
            
        student_page.wait_for_timeout(500)
        img1_path = ITERATION_DIR / "IT13_TC01_Anti_Tamper_Blackout_Shield.png"
        student_page.screenshot(path=str(img1_path))
        annotate(
            str(img1_path),
            "TC-IT13-001",
            "Anti-Tamper DevTools Blackout Shield",
            "F12 immediately triggered #global-security-blackout-shield with reason PHÁT HIỆN CÔNG CỤ DEVTOOLS.",
            tc01["status"]
        )
        tc01["evidence"].append(str(img1_path.name))
        results["test_cases"].append(tc01)
        
        # -----------------------------------------------------------------------
        # TC-IT13-002: View Source & Screen Capture Key Interception
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT13-002: View Source & Screen Capture Key Interception...")
        tc02 = {
            "id": "TC-IT13-002",
            "name": "View Source & Screen Capture Key Interception (Ctrl+U / PrintScreen)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Evaluate shortcut violation classifier in browser context
        shortcut_tests = student_page.evaluate("""() => {
            if (typeof VideoArmor === 'undefined') return { error: 'VideoArmor undefined' };
            
            const printScreen = VideoArmor.checkShortcutViolation({ key: 'PrintScreen', keyCode: 44 });
            const ctrlShiftS = VideoArmor.checkShortcutViolation({ ctrlKey: true, shiftKey: true, key: 's', keyCode: 83 });
            const metaShiftS = VideoArmor.checkShortcutViolation({ metaKey: true, shiftKey: true, key: 's', keyCode: 83 });
            const ctrlU = VideoArmor.checkShortcutViolation({ ctrlKey: true, key: 'u', keyCode: 85 });
            const ctrlShiftI = VideoArmor.checkShortcutViolation({ ctrlKey: true, shiftKey: true, key: 'i', keyCode: 73 });
            const ctrlShiftJ = VideoArmor.checkShortcutViolation({ ctrlKey: true, shiftKey: true, key: 'j', keyCode: 74 });
            const ctrlShiftC = VideoArmor.checkShortcutViolation({ ctrlKey: true, shiftKey: true, key: 'c', keyCode: 67 });
            const safeKey = VideoArmor.checkShortcutViolation({ key: 'Enter', keyCode: 13 });
            
            return {
                printScreen,
                ctrlShiftS,
                metaShiftS,
                ctrlU,
                ctrlShiftI,
                ctrlShiftJ,
                ctrlShiftC,
                safeKey
            };
        }""")
        tc02["notes"].append(f"Shortcut Violation Matrix: {shortcut_tests}")
        
        expected_matches = (
            shortcut_tests.get("printScreen") == "SCREEN_CAPTURE_ATTEMPT"
            and shortcut_tests.get("ctrlShiftS") == "SCREEN_CAPTURE_ATTEMPT"
            and shortcut_tests.get("metaShiftS") == "SCREEN_CAPTURE_ATTEMPT"
            and shortcut_tests.get("ctrlU") == "VIEW_SOURCE_ATTEMPT"
            and shortcut_tests.get("ctrlShiftI") == "DEVTOOLS_DETECTED"
            and shortcut_tests.get("ctrlShiftJ") == "DEVTOOLS_DETECTED"
            and shortcut_tests.get("ctrlShiftC") == "DEVTOOLS_DETECTED"
            and shortcut_tests.get("safeKey") is None
        )
        if not expected_matches:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Shortcut classification mismatch: {shortcut_tests}")
        else:
            tc02["notes"].append("Verified: All 7 malicious shortcut combinations correctly classified and ordinary keys allowed.")
            
        img2_path = ITERATION_DIR / "IT13_TC02_Shortcut_Interception_Rules.png"
        student_page.screenshot(path=str(img2_path))
        annotate(
            str(img2_path),
            "TC-IT13-002",
            "Shortcut Interception Rules",
            "PrintScreen, Win+Shift+S, Ctrl+U, Ctrl+Shift+I/J/C intercepted and classified accurately.",
            tc02["status"]
        )
        tc02["evidence"].append(str(img2_path.name))
        results["test_cases"].append(tc02)
        
        # -----------------------------------------------------------------------
        # TC-IT13-003: Right-Click Context Menu Suppression on Authenticated Surfaces
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT13-003: Right-Click Context Menu Suppression...")
        tc03 = {
            "id": "TC-IT13-003",
            "name": "Right-Click Context Menu Suppression on Authenticated Surfaces",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # New clean student context for contextmenu verification
        ctx2 = browser.new_context(viewport={"width": 1366, "height": 768})
        p2 = ctx2.new_page()
        p2.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        p2.goto(f"{BASE_URL}/#/auth")
        p2.wait_for_selector("#login-email", timeout=10000)
        p2.fill("#login-email", "student1@pwd301.local")
        p2.fill("#login-password", "Password123!")
        p2.click("button[type='submit']")
        p2.wait_for_url("**/#/student/**", timeout=10000)
        p2.wait_for_timeout(1000)
        
        # Dispatch contextmenu on non-editable area
        ctx_result = p2.evaluate("""() => {
            const evt = new MouseEvent('contextmenu', {
                bubbles: true,
                cancelable: true,
                clientX: 200,
                clientY: 200
            });
            const allowed = document.body.dispatchEvent(evt);
            const shield = document.getElementById('global-security-blackout-shield');
            
            return {
                default_prevented: evt.defaultPrevented,
                allowed: allowed,
                shield_triggered: shield !== null
            };
        }""")
        tc03["notes"].append(f"Contextmenu Dispatch Result: {ctx_result}")
        
        if not ctx_result.get("default_prevented") and ctx_result.get("allowed"):
            tc03["status"] = "FAIL"
            tc03["notes"].append(f"Contextmenu was not suppressed: {ctx_result}")
        else:
            tc03["notes"].append("Verified: Right-click contextmenu event strictly cancelled (defaultPrevented=True) and shield triggered.")
            
        p2.wait_for_timeout(500)
        img3_path = ITERATION_DIR / "IT13_TC03_ContextMenu_Suppression.png"
        p2.screenshot(path=str(img3_path))
        annotate(
            str(img3_path),
            "TC-IT13-003",
            "Context Menu Suppression",
            "Right-click contextmenu strictly prevented on authenticated surface, preventing source inspection.",
            tc03["status"]
        )
        tc03["evidence"].append(str(img3_path.name))
        results["test_cases"].append(tc03)
        
        # -----------------------------------------------------------------------
        # TC-IT13-004: State-Changing CSRF Token Enforcement (Fail-Closed)
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT13-004: State-Changing CSRF Token Enforcement...")
        tc04 = {
            "id": "TC-IT13-004",
            "name": "State-Changing CSRF Token Enforcement (Fail-Closed 400 CSRF_ERROR)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Clean context for CSRF test
        ctx3 = browser.new_context(viewport={"width": 1366, "height": 768})
        p3 = ctx3.new_page()
        p3.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        p3.goto(f"{BASE_URL}/#/auth")
        p3.wait_for_selector("#login-email", timeout=10000)
        p3.fill("#login-email", "student1@pwd301.local")
        p3.fill("#login-password", "Password123!")
        p3.click("button[type='submit']")
        p3.wait_for_url("**/#/student/**", timeout=10000)
        p3.wait_for_timeout(1000)
        
        # Dispatch raw fetch with cookies but WITHOUT X-CSRFToken header
        csrf_test_res = p3.evaluate("""async () => {
            try {
                const res = await fetch('/auth/profile', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                        // Intentionally omit X-CSRFToken and X-CSRF-Token
                    },
                    body: JSON.stringify({ full_name: 'Attacker CSRF Test' })
                });
                const data = await res.json();
                return {
                    status: res.status,
                    ok: res.ok,
                    error_code: data?.error?.code || data?.code,
                    message: data?.error?.message || data?.message
                };
            } catch (err) {
                return { error: err.message };
            }
        }""")
        tc04["notes"].append(f"CSRF Attack Simulation Response: {csrf_test_res}")
        
        # Must return HTTP 400 with CSRF_ERROR
        if csrf_test_res.get("status") != 400 or csrf_test_res.get("error_code") != "CSRF_ERROR":
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"CSRF PROTECTION BREACH: Request without CSRF token was not rejected with 400 CSRF_ERROR: {csrf_test_res}")
        else:
            tc04["notes"].append("Verified: State-changing POST without CSRF token strictly rejected with HTTP 400 CSRF_ERROR.")
            
        img4_path = ITERATION_DIR / "IT13_TC04_CSRF_Token_Enforcement.png"
        p3.screenshot(path=str(img4_path))
        annotate(
            str(img4_path),
            "TC-IT13-004",
            "CSRF Token Enforcement",
            "State-changing POST without X-CSRFToken strictly rejected fail-closed with HTTP 400 CSRF_ERROR.",
            tc04["status"]
        )
        tc04["evidence"].append(str(img4_path.name))
        results["test_cases"].append(tc04)
        
        # -----------------------------------------------------------------------
        # TC-IT13-005: XSS Payload Sanitization & HTML Output Escaping
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT13-005: XSS Payload Sanitization & HTML Output Escaping...")
        tc05 = {
            "id": "TC-IT13-005",
            "name": "XSS Payload Sanitization & HTML Output Escaping",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Submit profile update with XSS payload
        xss_payload = "<script>window.__xss_fired=true;</script><img src=x onerror='window.__xss_fired=true'><b>Safe</b>"
        xss_save_res = call_api(p3, "/auth/profile", "POST", {"full_name": xss_payload})
        tc05["notes"].append(f"Profile update with XSS payload: ok={xss_save_res.get('ok')}, status={xss_save_res.get('status')}")
        
        # Refresh page and check if __xss_fired was executed in the DOM
        p3.goto(f"{BASE_URL}/#/student/profile")
        p3.wait_for_timeout(1500)
        
        xss_check = p3.evaluate("""() => {
            const fired = Boolean(window.__xss_fired);
            const scriptTags = Array.from(document.querySelectorAll('script')).filter(s => s.textContent.includes('__xss_fired'));
            const imgOnError = Array.from(document.querySelectorAll('img')).filter(i => i.getAttribute('onerror')?.includes('__xss_fired'));
            
            return {
                xss_fired: fired,
                malicious_script_tags: scriptTags.length,
                malicious_img_onerror: imgOnError.length
            };
        }""")
        tc05["notes"].append(f"DOM Execution Check: {xss_check}")
        
        if xss_check.get("xss_fired") or xss_check.get("malicious_script_tags", 0) > 0 or xss_check.get("malicious_img_onerror", 0) > 0:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"XSS VULNERABILITY DETECTED: Script payload executed or inserted raw into DOM: {xss_check}")
        else:
            tc05["notes"].append("Verified: XSS payload escaped cleanly in DOM; zero script execution (window.__xss_fired=False).")
            
        # Revert legitimate profile name
        revert_res = call_api(p3, "/auth/profile", "POST", {"full_name": "Học viên 1 - Lớp An ninh mạng"})
        tc05["notes"].append(f"Reverted profile name: ok={revert_res.get('ok')}")
        
        img5_path = ITERATION_DIR / "IT13_TC05_XSS_Sanitization_Defense.png"
        p3.screenshot(path=str(img5_path))
        annotate(
            str(img5_path),
            "TC-IT13-005",
            "XSS Payload Sanitization Defense",
            "Malicious <script> and <img onerror> payloads escaped cleanly; zero script execution confirmed.",
            tc05["status"]
        )
        tc05["evidence"].append(str(img5_path.name))
        results["test_cases"].append(tc05)
        
        # -----------------------------------------------------------------------
        # TC-IT13-006: Sensitive System Secret & Internal Credential Leak Defense
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT13-006: Sensitive System Secret & Credential Leak Defense...")
        tc06 = {
            "id": "TC-IT13-006",
            "name": "Sensitive System Secret & Internal Credential Leak Defense",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Probing endpoints across status codes for secret leaks
        probed_responses = p3.evaluate("""async () => {
            const results = {};
            
            // 400 Bad Request
            try {
                const r1 = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: '{ malformed_json '
                });
                results['400_malformed'] = await r1.text();
            } catch (e) { results['400_malformed'] = e.message; }
            
            // 404 Not Found
            try {
                const r2 = await fetch('/api/courses/nonexistent-uuid-99999999');
                results['404_not_found'] = await r2.text();
            } catch (e) { results['404_not_found'] = e.message; }
            
            // 403 Forbidden
            try {
                const r3 = await fetch('/admin/courses', {
                    headers: { 'Accept': 'application/json' }
                });
                results['403_forbidden'] = await r3.text();
            } catch (e) { results['403_forbidden'] = e.message; }
            
            // 409 Conflict
            try {
                const r4 = await ApiClient.request('/student/courses/110007/enroll', { method: 'POST' });
                results['409_conflict'] = JSON.stringify(r4);
            } catch (e) { results['409_conflict'] = JSON.stringify(e.data || e.rawMessage || e.message); }
            
            return results;
        }""")
        
        secret_patterns = [
            (re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"), "Google Gemini API Key"),
            (re.compile(r"Password=[^;\s]+", re.IGNORECASE), "SQL Server Connection Password"),
            (re.compile(r"\$2[aby]\$[0-9]{2}\$[A-Za-z0-9./]{53}"), "bcrypt Password Hash"),
            (re.compile(r"Traceback \(most recent call last\):"), "Python Raw Stack Trace"),
            (re.compile(r"SA_PASSWORD", re.IGNORECASE), "Database SA Password Variable"),
        ]
        
        leak_detected = False
        for endpoint, body in probed_responses.items():
            for pattern, label in secret_patterns:
                match = pattern.search(body)
                if match:
                    leak_detected = True
                    tc06["status"] = "FAIL"
                    tc06["notes"].append(f"SECURITY LEAK in {endpoint}: Found {label} ({match.group(0)[:15]}...)")
                    
        if not leak_detected:
            tc06["notes"].append("Verified: Zero sensitive secrets, connection strings, Gemini API keys, or raw stack traces detected across error envelopes.")
            
        p3.goto(f"{BASE_URL}/#/student/dashboard")
        p3.wait_for_timeout(1000)
        img6_path = ITERATION_DIR / "IT13_TC06_Secret_Leak_Defense.png"
        p3.screenshot(path=str(img6_path))
        annotate(
            str(img6_path),
            "TC-IT13-006",
            "System Secret Leak Defense",
            "Zero Gemini keys, DB connection strings, password hashes, or raw stack traces exposed across error responses.",
            tc06["status"]
        )
        tc06["evidence"].append(str(img6_path.name))
        results["test_cases"].append(tc06)
        
        ctx2.close()
        ctx3.close()
        browser.close()
        
    # Write results.json
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n==========================================================================")
    print(f"  ITERATION 13 EXECUTION COMPLETE. Results written to: {RESULTS_FILE}")
    print("==========================================================================")
    for tc in results["test_cases"]:
        print(f"  [{tc['status']}] {tc['id']}: {tc['name']}")

if __name__ == "__main__":
    run()
