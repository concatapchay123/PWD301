import json
import sys
import io
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"
ITERATION_DIR = Path("qa-audit/iterations/iteration-04/evidence")
GLOBAL_SCREENSHOTS = Path("qa-audit/screenshots")
RESULTS_FILE = Path("qa-audit/iterations/iteration-04/results.json")

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
    draw.text((120, 48), f"Proof: {description} | URL: {img_path}", fill=(161, 161, 170))
    
    new_img.save(img_path)
    # Also copy to global screenshots
    dest_global = GLOBAL_SCREENSHOTS / Path(img_path).name
    new_img.save(dest_global)

def run():
    print("[*] Launching Real Chrome Browser via Playwright for Iteration 04...")
    results = {
        "iteration": 4,
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
        page.wait_for_timeout(2000)
        
        # -----------------------------------------------------------------------
        # TC-IT04-001: Topbar Brand Identity & PPTQ Logo Render
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT04-001: Topbar Brand Identity & PPTQ Logo Render...")
        tc01 = {
            "id": "TC-IT04-001",
            "name": "Topbar Brand Identity & PPTQ Logo Render",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        logo_visible = page.is_visible("img[alt='PPTQ Logo']")
        topbar_title = page.inner_text("#app-topbar").strip() if page.is_visible("#app-topbar") else ""
        user_name = page.inner_text("#topbar-user-name").strip() if page.is_visible("#topbar-user-name") else ""
        role_badge = page.inner_text("#topbar-role-badge").strip() if page.is_visible("#topbar-role-badge") else ""
        avatar_initials = page.inner_text("#topbar-avatar-initials").strip() if page.is_visible("#topbar-avatar-initials") else ""
        
        tc01["notes"].append(f"Logo visible: {logo_visible}, User name: '{user_name}', Role badge: '{role_badge}', Initials: '{avatar_initials}'")
        
        if not logo_visible or not user_name or "HỌC VIÊN" not in role_badge:
            tc01["status"] = "FAIL"
            tc01["notes"].append("Topbar brand elements missing or incorrect.")
            
        img1_path = ITERATION_DIR / "IT04_TC01_topbar_brand_identity.png"
        page.screenshot(path=str(img1_path))
        annotate(str(img1_path), "TC-IT04-001", "Topbar Brand Identity", f"Logo: {logo_visible}, Role: {role_badge}, User: {user_name}", tc01["status"])
        tc01["evidence"].append(str(img1_path.name))
        results["test_cases"].append(tc01)
        
        # -----------------------------------------------------------------------
        # TC-IT04-002: Dynamic Role Navigation Items Render
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT04-002: Dynamic Role Navigation Items Render...")
        tc02 = {
            "id": "TC-IT04-002",
            "name": "Dynamic Role Navigation Items Render",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        nav_links = page.query_selector_all("#topbar-navigation-items a")
        link_texts = [link.inner_text().strip() for link in nav_links]
        link_hrefs = [link.get_attribute("href") for link in nav_links]
        
        tc02["notes"].append(f"Rendered Navigation Links ({len(nav_links)}): {list(zip(link_texts, link_hrefs))}")
        
        expected_items = ["Trang chủ", "Khám phá Khóa học", "Khóa học của tôi", "Bài kiểm tra"]
        matched_items = [item for item in expected_items if any(item in text for text in link_texts)]
        
        if len(matched_items) < len(expected_items):
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Missing navigation items: set(expected) - set(matched) = {set(expected_items) - set(matched_items)}")
            
        img2_path = ITERATION_DIR / "IT04_TC02_dynamic_nav_items.png"
        page.screenshot(path=str(img2_path))
        annotate(str(img2_path), "TC-IT04-002", "Dynamic Nav Items", f"Rendered {len(nav_links)} role menu links: {matched_items}", tc02["status"])
        tc02["evidence"].append(str(img2_path.name))
        results["test_cases"].append(tc02)
        
        # -----------------------------------------------------------------------
        # TC-IT04-003: Mobile Drawer Open/Close Interaction (375x667 Viewport)
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT04-003: Mobile Drawer Open/Close Interaction...")
        tc03 = {
            "id": "TC-IT04-003",
            "name": "Mobile Drawer Open/Close Interaction",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Emulate mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(500)
        
        mobile_btn = page.query_selector("#topbar-mobile-menu-btn")
        is_btn_visible = page.is_visible("#topbar-mobile-menu-btn")
        tc03["notes"].append(f"Mobile menu button visible on 375x667: {is_btn_visible}")
        
        # Click mobile menu button
        page.click("#topbar-mobile-menu-btn")
        page.wait_for_timeout(500)
        
        drawer_visible = page.is_visible("#mobile-nav-drawer")
        backdrop_visible = page.is_visible("#mobile-nav-backdrop")
        aria_expanded = page.get_attribute("#topbar-mobile-menu-btn", "aria-expanded")
        
        tc03["notes"].append(f"Drawer opened: visible={drawer_visible}, backdrop={backdrop_visible}, aria-expanded={aria_expanded}")
        
        img3_path = ITERATION_DIR / "IT04_TC03_mobile_drawer_opened.png"
        page.screenshot(path=str(img3_path))
        
        # Close drawer
        page.click("#mobile-nav-close-btn")
        page.wait_for_timeout(500)
        drawer_closed = not page.is_visible("#mobile-nav-drawer")
        tc03["notes"].append(f"Drawer closed after close button click: {drawer_closed}")
        
        if not is_btn_visible or not drawer_visible or not drawer_closed:
            tc03["status"] = "FAIL"
            tc03["notes"].append("Mobile drawer open/close cycle failed.")
            
        annotate(str(img3_path), "TC-IT04-003", "Mobile Drawer Interaction", f"Drawer opened: {drawer_visible}, closed cleanly: {drawer_closed}", tc03["status"])
        tc03["evidence"].append(str(img3_path.name))
        results["test_cases"].append(tc03)
        
        # Restore desktop viewport
        page.set_viewport_size({"width": 1366, "height": 768})
        page.wait_for_timeout(500)
        
        # -----------------------------------------------------------------------
        # TC-IT04-004: Focus Exam Mode Shell Guard & AI Tutor Concealment
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT04-004: Focus Exam Mode Shell Guard...")
        tc04 = {
            "id": "TC-IT04-004",
            "name": "Focus Exam Mode Shell Guard & Anti-Leak Header",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Trigger focus route: canonical attempt route
        page.goto(f"{BASE_URL}/#/student/assessments/attempts/1")
        page.wait_for_timeout(1500)
        
        # Evaluate focus mode invariants
        focus_eval = page.evaluate("""() => {
            return {
                bodyHasFocusClass: document.body.classList.contains('fullscreen-focus-mode'),
                floatingAiHidden: document.getElementById('floating-ai-container') ? document.getElementById('floating-ai-container').classList.contains('hidden') : null,
                obsoleteBadgeExists: !!document.getElementById('console-course-progress-badge')
            };
        }""")
        
        tc04["notes"].append(f"Focus Mode Evaluation: {focus_eval}")
        
        if not focus_eval["bodyHasFocusClass"]:
            tc04["status"] = "FAIL"
            tc04["notes"].append("Invariant Violated: body does NOT have 'fullscreen-focus-mode' class during attempt route.")
            
        if not focus_eval["floatingAiHidden"]:
            tc04["status"] = "FAIL"
            tc04["notes"].append("Invariant Violated: Floating AI Tutor container is NOT hidden during exam attempt.")
            
        if focus_eval["obsoleteBadgeExists"]:
            tc04["status"] = "FAIL"
            tc04["notes"].append("Invariant Violated: #console-course-progress-badge is present in header (must be removed).")
            
        img4_path = ITERATION_DIR / "IT04_TC04_focus_exam_mode_guard.png"
        page.screenshot(path=str(img4_path))
        annotate(str(img4_path), "TC-IT04-004", "Focus Exam Mode Guard", f"Focus class: {focus_eval['bodyHasFocusClass']}, AI hidden: {focus_eval['floatingAiHidden']}, Obsolete badge gone: {not focus_eval['obsoleteBadgeExists']}", tc04["status"])
        tc04["evidence"].append(str(img4_path.name))
        results["test_cases"].append(tc04)
        
        # -----------------------------------------------------------------------
        # TC-IT04-005: Unknown Route Graceful Fallback (404 Handling)
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT04-005: Unknown Route Graceful Fallback...")
        tc05 = {
            "id": "TC-IT04-005",
            "name": "Unknown Route Graceful Fallback (404 Handling)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Navigate to a completely invalid hash route
        page.goto(f"{BASE_URL}/#/unknown-invalid-route-xyz-999")
        page.wait_for_timeout(2000)
        
        settled_url = page.url
        tc05["notes"].append(f"URL after navigating to unknown route: {settled_url}")
        
        # Expect fallback redirect to role home
        if "#/student/dashboard" in settled_url or "#/student/" in settled_url:
            tc05["notes"].append("Graceful fallback confirmed: Router redirected unknown route safely to student dashboard.")
        else:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"Router failed to gracefully redirect unknown route; settled at: {settled_url}")
            
        img5_path = ITERATION_DIR / "IT04_TC05_unknown_route_fallback.png"
        page.screenshot(path=str(img5_path))
        annotate(str(img5_path), "TC-IT04-005", "Unknown Route Fallback", f"Safely redirected from unknown route to {settled_url}", tc05["status"])
        tc05["evidence"].append(str(img5_path.name))
        results["test_cases"].append(tc05)
        
        # -----------------------------------------------------------------------
        # TC-IT04-006: Clean Browser History Stack Navigation Integrity
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT04-006: Browser History Stack Navigation Integrity...")
        tc06 = {
            "id": "TC-IT04-006",
            "name": "Clean Browser History Stack Navigation Integrity",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Step 1: Start at dashboard
        page.goto(f"{BASE_URL}/#/student/dashboard")
        page.wait_for_timeout(1000)
        
        # Step 2: Navigate to catalog
        page.goto(f"{BASE_URL}/#/student/catalog")
        page.wait_for_timeout(1000)
        
        # Step 3: Navigate to my learning
        page.goto(f"{BASE_URL}/#/student/courses")
        page.wait_for_timeout(1000)
        
        # Step 4: Go back once -> expect catalog
        page.go_back()
        page.wait_for_timeout(1000)
        back1_url = page.url
        tc06["notes"].append(f"First go_back() reached: {back1_url}")
        
        # Step 5: Go back twice -> expect dashboard
        page.go_back()
        page.wait_for_timeout(1000)
        back2_url = page.url
        tc06["notes"].append(f"Second go_back() reached: {back2_url}")
        
        if "#/student/catalog" not in back1_url or "#/student/dashboard" not in back2_url:
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"History stack navigation broken: back1={back1_url}, back2={back2_url}")
        else:
            tc06["notes"].append("Browser history stack verified: Back transitions cleanly across distinct views.")
            
        img6_path = ITERATION_DIR / "IT04_TC06_browser_history_stack.png"
        page.screenshot(path=str(img6_path))
        annotate(str(img6_path), "TC-IT04-006", "History Stack Navigation", f"Clean back traversal: courses -> {back1_url} -> {back2_url}", tc06["status"])
        tc06["evidence"].append(str(img6_path.name))
        results["test_cases"].append(tc06)
        
        browser.close()

    # Save results to JSON
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"[*] Iteration 04 Execution Complete. Saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run()
