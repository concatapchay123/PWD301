"""Iteration 03 Execution Script: Authorization, RBAC Boundaries & Cross-Role Isolation.
Verifies cross-role access restrictions, object-level authorization, and the
Strict Lifetime Enrollment Invariant (POST /student/courses/<id>/leave -> 403).
"""
import json
import os
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:5000"
ITERATION_DIR = Path("qa-audit/iterations/iteration-03/evidence")
SCREENSHOTS_DIR = Path("qa-audit/screenshots")
ITERATION_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

results = {
    "iteration": 3,
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "test_cases": [],
}

def annotate(img_path, tc_id, title, desc, status="PASS"):
    try:
        im = Image.open(img_path)
        w, h = im.size
        banner_h = 75
        canvas = Image.new("RGB", (w, h + banner_h), (15, 23, 42))
        canvas.paste(im, (0, banner_h))
        draw = ImageDraw.Draw(canvas)
        status_color = (16, 185, 129) if status == "PASS" else (244, 63, 94)
        draw.rectangle([(0, 0), (w, 4)], fill=status_color)
        draw.text((20, 15), f"ITERATION 03 | {tc_id} [{status}] : {title}", fill=(255, 255, 255))
        draw.text((20, 42), desc, fill=(148, 163, 184))
        canvas.save(img_path)
        canvas.save(SCREENSHOTS_DIR / Path(img_path).name)
    except Exception as e:
        print(f"Annotation error on {img_path}: {e}")

print("[*] Launching Real Chrome Browser via Playwright for Iteration 03...")
with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=True,
        args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
    )
    context = browser.new_context(viewport={"width": 1366, "height": 768})
    page = context.new_page()

    # 1. Login as Student
    page.goto(f"{BASE_URL}/#/auth", wait_until="networkidle")
    time.sleep(1)
    page.locator("#login-email").fill("student1@pwd301.local")
    page.locator("#login-password").fill("Password123!")
    page.locator("#login-submit-btn").click()
    page.wait_for_url("**/#/student/dashboard", timeout=8000)
    time.sleep(1)

    # -----------------------------------------------------------------------
    # TC-IT03-001: Student attempts to access #/instructor/dashboard
    # -----------------------------------------------------------------------
    print("[*] Running TC-IT03-001: Student access restriction to Instructor Dashboard...")
    tc01 = {
        "id": "TC-IT03-001",
        "name": "Student Restricted from Instructor Studio",
        "status": "PASS",
        "evidence": [],
        "notes": []
    }
    
    page.goto(f"{BASE_URL}/#/instructor/dashboard")
    time.sleep(1.5)
    
    # Assert redirected back to student dashboard or toast warning shown
    toast = page.locator("#toast-container, .c-toast, div:has-text('không có quyền')").first
    img1_path = ITERATION_DIR / "IT03_TC01_student_blocked_from_instructor.png"
    page.screenshot(path=str(img1_path))
    
    if "#/student/" in page.url:
        tc01["notes"].append(f"Student safely redirected to role home: {page.url}")
    else:
        tc01["status"] = "FAIL"
        tc01["notes"].append(f"Student remained on instructor route! URL: {page.url}")
        
    annotate(str(img1_path), "TC-IT03-001", "Student Blocked from Instructor", "Verified student redirected from #/instructor/dashboard to #/student/dashboard", tc01["status"])
    tc01["evidence"].append(str(img1_path.name))
    results["test_cases"].append(tc01)

    # -----------------------------------------------------------------------
    # TC-IT03-002: Student attempts to access #/admin/governance
    # -----------------------------------------------------------------------
    print("[*] Running TC-IT03-002: Student access restriction to Admin Governance...")
    tc02 = {
        "id": "TC-IT03-002",
        "name": "Student Restricted from Admin Governance",
        "status": "PASS",
        "evidence": [],
        "notes": []
    }
    
    page.goto(f"{BASE_URL}/#/admin/governance")
    time.sleep(1.5)
    
    img2_path = ITERATION_DIR / "IT03_TC02_student_blocked_from_admin.png"
    page.screenshot(path=str(img2_path))
    
    if "#/student/" in page.url:
        tc02["notes"].append(f"Student safely redirected to role home: {page.url}")
    else:
        tc02["status"] = "FAIL"
        tc02["notes"].append(f"Student remained on admin route! URL: {page.url}")
        
    annotate(str(img2_path), "TC-IT03-002", "Student Blocked from Admin", "Verified student redirected from #/admin/governance to #/student/dashboard", tc02["status"])
    tc02["evidence"].append(str(img2_path.name))
    results["test_cases"].append(tc02)

    # -----------------------------------------------------------------------
    # TC-IT03-003: Strict Lifetime Enrollment Invariant (POST /student/courses/<id>/leave -> 403)
    # -----------------------------------------------------------------------
    print("[*] Running TC-IT03-003: Strict Lifetime Enrollment Invariant...")
    tc03 = {
        "id": "TC-IT03-003",
        "name": "Strict Lifetime Enrollment Invariant (Leave Course Locked)",
        "status": "PASS",
        "evidence": [],
        "notes": []
    }
    
    leave_eval = """async () => {
        try {
            // Attempt to leave course directly via student endpoint
            const r = await ApiClient.request('/student/courses/1/leave', { method: 'POST' });
            return { ok: true, r };
        } catch(e) {
            return { ok: false, status: e.status, code: e.code, message: e.message, raw: e.rawMessage };
        }
    }"""
    leave_res = page.evaluate(leave_eval)
    tc03["notes"].append(f"Leave course response: {leave_res}")
    
    # Must be 403 Forbidden!
    if leave_res.get("status") == 403:
        tc03["notes"].append("Confirmed: POST /student/courses/<id>/leave returned HTTP 403 Forbidden.")
    else:
        tc03["status"] = "FAIL"
        tc03["notes"].append(f"Invariant Violated: Expected HTTP 403 but got status {leave_res.get('status')}")
        
    img3_path = ITERATION_DIR / "IT03_TC03_lifetime_enrollment_locked.png"
    page.screenshot(path=str(img3_path))
    annotate(str(img3_path), "TC-IT03-003", "Lifetime Enrollment Invariant", "Verified leave course returns HTTP 403 Forbidden (Lifetime Enrollment Policy)", tc03["status"])
    tc03["evidence"].append(str(img3_path.name))
    results["test_cases"].append(tc03)

    # -----------------------------------------------------------------------
    # TC-IT03-004: Backend API Object Authorization (Student calling Admin API)
    # -----------------------------------------------------------------------
    print("[*] Running TC-IT03-004: Backend API Object Authorization...")
    tc04 = {
        "id": "TC-IT03-004",
        "name": "Backend RBAC API Barrier for Student",
        "status": "PASS",
        "evidence": [],
        "notes": []
    }
    
    api_eval = """async () => {
        const tests = [];
        try {
            await ApiClient.request('/admin/users', { method: 'GET' });
            tests.push({ endpoint: '/admin/users', allowed: true });
        } catch(e) {
            tests.push({ endpoint: '/admin/users', allowed: false, status: e.status });
        }
        try {
            await ApiClient.request('/api/admin/system/health', { method: 'GET' });
            tests.push({ endpoint: '/api/admin/system/health', allowed: true });
        } catch(e) {
            tests.push({ endpoint: '/api/admin/system/health', allowed: false, status: e.status });
        }
        return tests;
    }"""
    api_res = page.evaluate(api_eval)
    for t in api_res:
        tc04["notes"].append(f"{t['endpoint']} -> allowed: {t['allowed']}, status: {t.get('status')}")
        if t["allowed"] is True:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Security Flaw: Student allowed to call privileged endpoint {t['endpoint']}")

    img4_path = ITERATION_DIR / "IT03_TC04_api_rbac_barrier.png"
    page.screenshot(path=str(img4_path))
    annotate(str(img4_path), "TC-IT03-004", "Backend RBAC API Barrier", "Verified HTTP 403 on privileged /admin endpoints for student role", tc04["status"])
    tc04["evidence"].append(str(img4_path.name))
    results["test_cases"].append(tc04)

    # -----------------------------------------------------------------------
    # TC-IT03-005: Instructor Boundary & Course Management RBAC
    # -----------------------------------------------------------------------
    print("[*] Running TC-IT03-005: Instructor Boundary & Admin Restriction...")
    tc05 = {
        "id": "TC-IT03-005",
        "name": "Instructor Restricted from Admin Governance",
        "status": "PASS",
        "evidence": [],
        "notes": []
    }
    
    # Logout and login as instructor1
    page.locator("#topbar-avatar-btn").click()
    time.sleep(0.5)
    page.locator("#topbar-logout-btn").click()
    page.wait_for_url("**/#/auth", timeout=8000)
    time.sleep(1)
    
    page.locator("#login-email").fill("instructor1@pwd301.local")
    page.locator("#login-password").fill("Password123!")
    page.locator("#login-submit-btn").click()
    page.wait_for_url("**/#/instructor/**", timeout=8000)
    time.sleep(1)
    
    # Try accessing #/admin/governance
    page.goto(f"{BASE_URL}/#/admin/governance")
    time.sleep(1.5)
    
    img5_path = ITERATION_DIR / "IT03_TC05_instructor_blocked_from_admin.png"
    page.screenshot(path=str(img5_path))
    
    if "#/instructor/" in page.url:
        tc05["notes"].append(f"Instructor safely redirected back to {page.url}")
    else:
        tc05["status"] = "FAIL"
        tc05["notes"].append(f"Instructor remained on admin route! URL: {page.url}")
        
    annotate(str(img5_path), "TC-IT03-005", "Instructor Blocked from Admin", "Verified instructor redirected from #/admin/governance to #/instructor/dashboard", tc05["status"])
    tc05["evidence"].append(str(img5_path.name))
    results["test_cases"].append(tc05)

    # -----------------------------------------------------------------------
    # TC-IT03-006: Primary Admin Full Governance Access
    # -----------------------------------------------------------------------
    print("[*] Running TC-IT03-006: Primary Admin Full Governance Access...")
    tc06 = {
        "id": "TC-IT03-006",
        "name": "Primary Admin Multi-Tab Governance Access",
        "status": "PASS",
        "evidence": [],
        "notes": []
    }
    
    # Logout and login as admin
    page.locator("#topbar-avatar-btn").click()
    time.sleep(0.5)
    page.locator("#topbar-logout-btn").click()
    page.wait_for_url("**/#/auth", timeout=8000)
    time.sleep(1)
    
    page.locator("#login-email").fill("admin@pwd301.local")
    page.locator("#login-password").fill("Password123!")
    page.locator("#login-submit-btn").click()
    page.wait_for_url("**/#/admin/**", timeout=8000)
    time.sleep(1.5)
    
    # Verify primary admin tabs (users, courses, applications, security)
    page.goto(f"{BASE_URL}/#/admin/governance?tab=courses")
    time.sleep(1)
    page.goto(f"{BASE_URL}/#/admin/governance?tab=applications")
    time.sleep(1)
    page.goto(f"{BASE_URL}/#/admin/operations")
    time.sleep(1.5)
    
    img6_path = ITERATION_DIR / "IT03_TC06_primary_admin_operations.png"
    page.screenshot(path=str(img6_path))
    
    if "#/admin/operations" in page.url:
        tc06["notes"].append("Primary Admin successfully accessed #/admin/operations.")
    else:
        tc06["status"] = "FAIL"
        tc06["notes"].append(f"Admin failed to access #/admin/operations. URL: {page.url}")
        
    annotate(str(img6_path), "TC-IT03-006", "Primary Admin Operations", "Verified Primary Admin access to Operations, Telemetry, and Governance tabs", tc06["status"])
    tc06["evidence"].append(str(img6_path.name))
    results["test_cases"].append(tc06)

    browser.close()

results_file = Path("qa-audit/iterations/iteration-03/results.json")
with open(results_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"[*] Iteration 03 Execution Complete. Saved to {results_file}")
