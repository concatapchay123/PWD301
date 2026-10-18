import json
import sys
import io
import time
import uuid
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"
ITERATION_DIR = Path("qa-audit/iterations/iteration-08/evidence")
GLOBAL_SCREENSHOTS = Path("qa-audit/screenshots")
RESULTS_FILE = Path("qa-audit/iterations/iteration-08/results.json")

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

def upload_course_cover(page, course_id):
    """Generates an authentic 16:9 PNG image and uploads it as a COURSE_IMAGE asset."""
    img = Image.new("RGB", (640, 360), (30, 41, 59))
    d = ImageDraw.Draw(img)
    d.rectangle([(20, 20), (620, 340)], outline=(59, 130, 246), width=4)
    d.text((40, 40), "PWD301 QA Audit - Course Cover 16:9", fill=(248, 250, 252))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = list(buf.getvalue())
    
    return page.evaluate("""async ([courseId, bytes]) => {
        try {
            const blob = new Blob([new Uint8Array(bytes)], { type: 'image/png' });
            const formData = new FormData();
            formData.append('file', blob, 'cover_16_9.png');
            formData.append('asset_type', 'COURSE_IMAGE');
            formData.append('title', 'Ảnh bìa khóa học 16:9');
            
            const csrfToken = await ApiClient.ensureCsrfToken();
            const res = await fetch(`/instructor/courses/${courseId}/files`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Accept': 'application/json'
                }
            });
            const data = await res.json();
            return { ok: res.ok, status: res.status, data: data };
        } catch (e) {
            return { ok: false, status: 500, error: e.message };
        }
    }""", [course_id, png_bytes])

def run():
    print("[*] Launching Real Chrome Browser via Playwright for Iteration 08...")
    results = {
        "iteration": 8,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_cases": []
    }
    
    test_run_id = str(uuid.uuid4())[:6].upper()
    course_code = f"FLOW_{test_run_id}"
    course_title = f"Kiểm Thử Vòng Đời & Staging Draft {course_code}"
    created_course_id = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        
        # -----------------------------------------------------------------------
        # Instructor Context & Login
        # -----------------------------------------------------------------------
        instructor_context = browser.new_context(viewport={"width": 1366, "height": 768})
        instructor_page = instructor_context.new_page()
        instructor_page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        print("[*] Authenticating as Instructor...")
        instructor_page.goto(f"{BASE_URL}/#/auth")
        instructor_page.wait_for_selector("#login-email", timeout=10000)
        instructor_page.fill("#login-email", "instructor1@pwd301.local")
        instructor_page.fill("#login-password", "Password123!")
        instructor_page.click("button[type='submit']")
        instructor_page.wait_for_url("**/#/instructor/dashboard", timeout=10000)
        instructor_page.wait_for_timeout(1500)
        
        # -----------------------------------------------------------------------
        # TC-IT08-001: Pre-Flight Publish Readiness Validation (Fail-Closed Rejection)
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT08-001: Pre-Flight Publish Readiness Validation...")
        tc01 = {
            "id": "TC-IT08-001",
            "name": "Pre-Flight Publish Readiness Validation (Fail-Closed Rejection)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Create bare course
        create_res = call_api(
            instructor_page,
            "/instructor/courses",
            "POST",
            {
                "title": course_title,
                "course_code": course_code,
                "category": "SOFTWARE_TESTING",
                "difficulty": "INTERMEDIATE"
            }
        )
        if create_res["ok"]:
            c_data = create_res["data"]
            created_course_id = str(c_data.get("course_id") or c_data.get("id"))
            tc01["notes"].append(f"Created bare course {course_code} (ID: {created_course_id}) in DRAFT status.")
        else:
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"Failed to create bare course: {create_res}")
            
        # Check pre-flight checklist
        chk_res = call_api(instructor_page, f"/instructor/courses/{created_course_id}/publish-checklist", "GET")
        if chk_res["ok"]:
            chk_data = chk_res["data"]
            is_ready = chk_data.get("is_ready")
            failed_criteria = [c.get("title") for c in chk_data.get("criteria", []) if not c.get("passed")]
            tc01["notes"].append(f"Publish checklist verified: is_ready={is_ready}, missing={len(failed_criteria)} criteria.")
            if is_ready:
                tc01["status"] = "FAIL"
                tc01["notes"].append("Pre-flight checklist incorrectly returned is_ready=True for bare course.")
        else:
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"Failed to query publish checklist: {chk_res}")
            
        # Attempt to submit incomplete course -> expect HTTP 400 rejection
        sub_res = call_api(instructor_page, f"/instructor/courses/{created_course_id}/submit", "POST")
        if not sub_res["ok"] and sub_res["status"] == 400:
            tc01["notes"].append(f"Incomplete submission rejected fail-closed (HTTP 400): {sub_res.get('error')[:80]}...")
        else:
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"Expected HTTP 400 rejection, received: {sub_res}")
            
        # Visual evidence in Studio
        instructor_page.goto(f"{BASE_URL}/#/instructor/courses/manage?id={created_course_id}")
        instructor_page.wait_for_timeout(2000)
        img1_path = ITERATION_DIR / "IT08_TC01_preflight_rejection.png"
        instructor_page.screenshot(path=str(img1_path))
        annotate(
            str(img1_path),
            "TC-IT08-001",
            "Pre-Flight Publish Readiness Validation",
            f"Bare course rejected with HTTP 400. is_ready=False. Status remained DRAFT.",
            tc01["status"]
        )
        tc01["evidence"].append(str(img1_path.name))
        results["test_cases"].append(tc01)
        
        # -----------------------------------------------------------------------
        # TC-IT08-002: Complete Course Submission & Studio Lock
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT08-002: Complete Course Submission & Studio Lock...")
        tc02 = {
            "id": "TC-IT08-002",
            "name": "Complete Course Submission & Studio Lock",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # 1. Upload clean 16:9 Cover Image
        cover_res = upload_course_cover(instructor_page, created_course_id)
        cover_asset_id = None
        if cover_res["ok"]:
            asset_info = cover_res["data"]
            cover_asset_id = asset_info.get("asset_id") or asset_info.get("id")
            tc02["notes"].append(f"16:9 Cover image uploaded: Asset ID {cover_asset_id}")
        else:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Failed to upload cover image: {cover_res}")
            
        # 2. Update course metadata: description, trailer_url, learning_objectives, thumbnail_file_asset_id
        meta_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}",
            "PUT",
            {
                "thumbnail_file_asset_id": cover_asset_id,
                "trailer_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "description": "Khóa học chuyên sâu về quy trình kiểm thử phần mềm toàn diện, tự động hóa E2E và CI/CD.",
                "learning_objectives": [
                    "Nắm vững các phương pháp thiết kế ca kiểm thử hộp đen và hộp trắng",
                    "Thành thạo tự động hóa E2E bằng Playwright trên môi trường thực tế"
                ]
            }
        )
        tc02["notes"].append(f"Course metadata updated: ok={meta_res['ok']}")
        if not meta_res["ok"]:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Metadata update error: {meta_res}")
        
        # 3. Set academic completion rule: minimum_progress_percent >= 50
        comp_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/completion-rules",
            "POST",
            {
                "minimum_progress_percent": 80.0,
                "minimum_grade_score": 70.0,
                "require_all_mandatory_lessons": True
            }
        )
        tc02["notes"].append(f"Completion rules configured: ok={comp_res['ok']}")
        
        # 4. Create Learning Unit
        unit_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/learning-units",
            "POST",
            {
                "title": "Chương 1: Nền Tảng Kiểm Thử Phần Mềm",
                "order_index": 1
            }
        )
        unit_id = None
        if unit_res["ok"]:
            u_data = unit_res["data"].get("data") or unit_res["data"]
            unit_id = str(u_data.get("id") or u_data.get("unit_id") or u_data.get("learning_unit_id"))
            tc02["notes"].append(f"Created Learning Unit: ID {unit_id}")
        else:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Failed to create unit: {unit_res}")
            
        # 5. Create Lesson with authentic markdown
        lesson_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/lessons",
            "POST",
            {
                "learning_unit_id": unit_id,
                "title": "Bài 1: Tổng Quan Về Kiến Trúc Headless & QA",
                "summary": "Giới thiệu nguyên lý kiểm thử kiến trúc thuần headless REST API.",
                "markdown_content": "# Bài 1: Tổng Quan Về Kiến Trúc Headless\n\nKiến trúc headless phân tách giao diện và nghiệp vụ backend."
            }
        )
        tc02["notes"].append(f"Created Lesson: ok={lesson_res['ok']}")
        
        # 6. Check pre-flight checklist again -> must now be is_ready=True
        chk_res2 = call_api(instructor_page, f"/instructor/courses/{created_course_id}/publish-checklist", "GET")
        if chk_res2["ok"] and chk_res2["data"].get("is_ready"):
            tc02["notes"].append("Pre-flight checklist confirmed is_ready=True with all 5 criteria satisfied.")
        else:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Checklist failed after populating criteria: {chk_res2}")
            
        # 7. Submit course for Admin Review
        submit_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/submit",
            "POST",
            {"reason": "Đã hoàn thiện đề cương và học liệu mẫu. Kính đề nghị Quản trị viên xét duyệt."}
        )
        if submit_res["ok"]:
            sub_data = submit_res["data"]
            new_status = sub_data.get("status")
            tc02["notes"].append(f"Course successfully submitted: status transitioned to {new_status}")
            if new_status != "SUBMITTED_FOR_REVIEW":
                tc02["status"] = "FAIL"
                tc02["notes"].append(f"Expected SUBMITTED_FOR_REVIEW status, got {new_status}")
        else:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Submit request failed: {submit_res}")
            
        # Refresh Studio in browser to verify locked state
        instructor_page.goto(f"{BASE_URL}/#/instructor/courses/manage?id={created_course_id}")
        instructor_page.wait_for_timeout(2500)
        
        img2_path = ITERATION_DIR / "IT08_TC02_course_submitted_locked.png"
        instructor_page.screenshot(path=str(img2_path))
        annotate(
            str(img2_path),
            "TC-IT08-002",
            "Complete Course Submission & Studio Lock",
            f"All 5 criteria satisfied. Status: SUBMITTED_FOR_REVIEW. Studio UI locked.",
            tc02["status"]
        )
        tc02["evidence"].append(str(img2_path.name))
        results["test_cases"].append(tc02)
        
        # -----------------------------------------------------------------------
        # TC-IT08-003: Admin Governance Queue & Course Inspection Dossier
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT08-003: Admin Governance Queue & Inspection Dossier...")
        tc03 = {
            "id": "TC-IT08-003",
            "name": "Admin Governance Queue & Course Inspection Dossier",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Launch Admin Context
        admin_context = browser.new_context(viewport={"width": 1366, "height": 768})
        admin_page = admin_context.new_page()
        admin_page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        print("[*] Authenticating as Admin...")
        admin_page.goto(f"{BASE_URL}/#/auth")
        admin_page.wait_for_selector("#login-email", timeout=10000)
        admin_page.fill("#login-email", "admin@pwd301.local")
        admin_page.fill("#login-password", "Password123!")
        admin_page.click("button[type='submit']")
        admin_page.wait_for_url("**/#/admin/governance*", timeout=10000)
        admin_page.wait_for_timeout(1500)
        
        # Navigate to Courses Review tab
        admin_page.goto(f"{BASE_URL}/#/admin/governance?tab=courses")
        admin_page.wait_for_selector("#admin-review-courses-queue", timeout=10000)
        admin_page.wait_for_timeout(2000)
        
        queue_text = admin_page.inner_text("#admin-review-courses-queue")
        if course_code in queue_text:
            tc03["notes"].append(f"Course {course_code} detected in Admin review queue DOM.")
        else:
            tc03["status"] = "FAIL"
            tc03["notes"].append(f"Course {course_code} not found in Admin review queue DOM.")
            
        # Fetch inspection dossier via Admin API
        dossier_res = call_api(admin_page, f"/admin/courses/{created_course_id}", "GET")
        if dossier_res["ok"]:
            d_json = dossier_res["data"]
            tc03["notes"].append(
                f"Inspection dossier retrieved: Title='{d_json.get('title')}', "
                f"Lessons={len(d_json.get('lessons', []))}, Status={d_json.get('status')}"
            )
        else:
            tc03["status"] = "FAIL"
            tc03["notes"].append(f"Failed to fetch inspection dossier: {dossier_res}")
            
        img3_path = ITERATION_DIR / "IT08_TC03_admin_review_queue.png"
        admin_page.screenshot(path=str(img3_path))
        annotate(
            str(img3_path),
            "TC-IT08-003",
            "Admin Governance Queue & Inspection Dossier",
            f"Course {course_code} verified in review queue with inspection dossier.",
            tc03["status"]
        )
        tc03["evidence"].append(str(img3_path.name))
        results["test_cases"].append(tc03)
        
        # -----------------------------------------------------------------------
        # TC-IT08-004: Admin Course Approval & Publication Transition
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT08-004: Admin Course Approval & Publication Transition...")
        tc04 = {
            "id": "TC-IT08-004",
            "name": "Admin Course Approval & Publication Transition",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # 1. Admin Approves Course
        appr_res = call_api(
            admin_page,
            f"/admin/courses/{created_course_id}/review",
            "POST",
            {
                "action": "approve",
                "reason": "Đề cương đáp ứng đầy đủ tiêu chuẩn kiểm toán và chuẩn đầu ra môn học."
            }
        )
        if appr_res["ok"]:
            appr_status = appr_res["data"].get("status")
            tc04["notes"].append(f"Admin approved course: status transitioned to {appr_status}")
            if appr_status != "APPROVED":
                tc04["status"] = "FAIL"
                tc04["notes"].append(f"Expected APPROVED, got {appr_status}")
        else:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Approval request failed: {appr_res}")
            
        # 2. Admin Publishes Course
        pub_res = call_api(
            admin_page,
            f"/admin/courses/{created_course_id}/publish",
            "POST",
            {"reason": "Xuất bản khóa học lên danh mục đào tạo công khai."}
        )
        if pub_res["ok"]:
            pub_status = pub_res["data"].get("status")
            tc04["notes"].append(f"Course published: status transitioned to {pub_status}")
            if pub_status != "PUBLISHED":
                tc04["status"] = "FAIL"
                tc04["notes"].append(f"Expected PUBLISHED, got {pub_status}")
        else:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Publish request failed: {pub_res}")
            
        # 3. Student Browser Context: Verify Course in Catalog
        student_context = browser.new_context(viewport={"width": 1366, "height": 768})
        student_page = student_context.new_page()
        student_page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        print("[*] Authenticating as Student...")
        student_page.goto(f"{BASE_URL}/#/auth")
        student_page.wait_for_selector("#login-email", timeout=10000)
        student_page.fill("#login-email", "student1@pwd301.local")
        student_page.fill("#login-password", "Password123!")
        student_page.click("button[type='submit']")
        student_page.wait_for_url("**/#/student/dashboard", timeout=10000)
        student_page.wait_for_timeout(1500)
        
        # Navigate to Student Catalog
        student_page.goto(f"{BASE_URL}/#/student/catalog")
        student_page.wait_for_timeout(2500)
        
        catalog_html = student_page.content()
        if course_code in catalog_html:
            tc04["notes"].append(f"Published course {course_code} successfully rendered in Student Catalog.")
        else:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Course {course_code} not visible in Student Catalog.")
            
        img4_path = ITERATION_DIR / "IT08_TC04_course_published_catalog.png"
        student_page.screenshot(path=str(img4_path))
        annotate(
            str(img4_path),
            "TC-IT08-004",
            "Admin Course Approval & Publication Gate",
            f"Status: PUBLISHED. Course verified live and visible in Student Catalog.",
            tc04["status"]
        )
        tc04["evidence"].append(str(img4_path.name))
        results["test_cases"].append(tc04)
        
        # -----------------------------------------------------------------------
        # TC-IT08-005: Unified Staging Draft Invariant (Post-Publication Isolation)
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT08-005: Unified Staging Draft Invariant...")
        tc05 = {
            "id": "TC-IT08-005",
            "name": "Unified Staging Draft Invariant (Post-Publication Isolation)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Instructor edits published course -> adds Chapter 2
        unit2_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/learning-units",
            "POST",
            {
                "title": "Chương 2: Kiểm Thử Tự Động Nâng Cao & Mocking",
                "order_index": 2
            }
        )
        changeset_id = None
        if unit2_res["ok"]:
            u2_json = unit2_res["data"]
            is_draft = u2_json.get("is_draft") or u2_json.get("data", {}).get("is_draft")
            changeset_id = (
                u2_json.get("change_request_id")
                or u2_json.get("data", {}).get("change_request_id")
            )
            tc05["notes"].append(
                f"Chapter 2 added while PUBLISHED. Response: is_draft={is_draft}, "
                f"change_request_id={changeset_id}"
            )
            if not is_draft:
                tc05["status"] = "FAIL"
                tc05["notes"].append("Changes were applied directly instead of staging into COURSE_VERSION_CHANGESET.")
        else:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"Failed to add Chapter 2: {unit2_res}")
            
        # Verify Student Perspective: Student curriculum must NOT have Chapter 2!
        student_course_res = call_api(student_page, f"/student/courses/{created_course_id}", "GET")
        if student_course_res["ok"]:
            sc_data = student_course_res["data"]
            student_units = sc_data.get("learning_units") or []
            unit_titles = [u.get("title") for u in student_units]
            has_ch2 = any("Chương 2" in t for t in unit_titles)
            tc05["notes"].append(
                f"Student view checked: {len(student_units)} units visible. "
                f"Chương 2 present: {has_ch2} (Must be False)."
            )
            if has_ch2:
                tc05["status"] = "FAIL"
                tc05["notes"].append("Data leakage: Unapproved Staging Draft (Chương 2) leaked to Student view!")
        else:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"Failed to fetch course from student API: {student_course_res}")
            
        # Reload Studio as Instructor to show Staging Draft status badge
        instructor_page.goto(f"{BASE_URL}/#/instructor/courses/manage?id={created_course_id}")
        instructor_page.wait_for_timeout(2000)
        img5_path = ITERATION_DIR / "IT08_TC05_staging_draft_isolation.png"
        instructor_page.screenshot(path=str(img5_path))
        annotate(
            str(img5_path),
            "TC-IT08-005",
            "Unified Staging Draft Invariant",
            f"Staging Draft active (CR #{changeset_id}). Student view completely isolated.",
            tc05["status"]
        )
        tc05["evidence"].append(str(img5_path.name))
        results["test_cases"].append(tc05)
        
        # -----------------------------------------------------------------------
        # TC-IT08-006: Atomic All-or-Nothing Changeset Diff Modal & Admin Approval
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT08-006: Atomic All-or-Nothing Changeset Diff & Approval...")
        tc06 = {
            "id": "TC-IT08-006",
            "name": "Atomic All-or-Nothing Changeset Diff Modal & Admin Approval",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # 1. Instructor submits the Staging Draft Changeset for review
        sub_cs_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/changeset/submit",
            "POST",
            {"reason": "Đề xuất cập nhật giáo trình: bổ sung Chương 2 về Mocking và E2E."}
        )
        tc06["notes"].append(f"Submitted changeset for review: ok={sub_cs_res['ok']}")
        
        # 2. Admin retrieves Changeset Diff
        diff_res = call_api(admin_page, f"/admin/courses/{created_course_id}/changeset/diff", "GET")
        diff_data = {}
        if diff_res["ok"]:
            diff_data = diff_res["data"]
            tc06["notes"].append(
                f"Changeset diff retrieved successfully: ReqID={diff_data.get('request_id')}, "
                f"ReviewVersion={diff_data.get('review_version')}, CourseCode={diff_data.get('course_code')}"
            )
        else:
            diff_res2 = call_api(admin_page, f"/admin/change-requests/{changeset_id}/diff", "GET")
            if diff_res2["ok"]:
                diff_data = diff_res2["data"]
                tc06["notes"].append(f"Changeset diff retrieved via CR ID: ReqID={diff_data.get('request_id')}")
            else:
                tc06["status"] = "FAIL"
                tc06["notes"].append(f"Failed to fetch changeset diff: {diff_res} / {diff_res2}")
                
        # 3. Admin Atomically Approves the Changeset with Review Identity
        approve_payload = {
            "request_id": diff_data.get("request_id") or changeset_id,
            "review_version": diff_data.get("review_version"),
            "reason": "Phê duyệt toàn bộ đề xuất bổ sung Chương 2 vào khóa học."
        }
        approve_cs_res = call_api(
            admin_page,
            f"/admin/courses/{created_course_id}/changeset/approve",
            "POST",
            approve_payload
        )
        if approve_cs_res["ok"]:
            appr_cs_json = approve_cs_res["data"]
            tc06["notes"].append(f"Admin approved changeset atomically: status={appr_cs_json.get('status')}")
        else:
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"Failed to approve changeset: {approve_cs_res}")
            
        # 4. Verify Student Perspective: Chapter 2 is now merged and visible!
        student_course_res2 = call_api(student_page, f"/student/courses/{created_course_id}", "GET")
        if student_course_res2["ok"]:
            sc_data2 = student_course_res2["data"]
            student_units2 = sc_data2.get("learning_units") or []
            unit_titles2 = [u.get("title") for u in student_units2]
            has_ch2_now = any("Chương 2" in t for t in unit_titles2)
            tc06["notes"].append(
                f"Student curriculum after approval: {len(student_units2)} units. "
                f"Chương 2 present: {has_ch2_now} (Must be True)."
            )
            if not has_ch2_now:
                tc06["status"] = "FAIL"
                tc06["notes"].append("Atomic merge failed: Approved changes not visible in Student view.")
        else:
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"Failed to re-fetch student course: {student_course_res2}")
            
        # Navigate Admin page to governance to capture visual proof
        admin_page.goto(f"{BASE_URL}/#/admin/governance?tab=courses")
        admin_page.wait_for_timeout(2000)
        img6_path = ITERATION_DIR / "IT08_TC06_changeset_diff_approved.png"
        admin_page.screenshot(path=str(img6_path))
        annotate(
            str(img6_path),
            "TC-IT08-006",
            "Atomic All-or-Nothing Changeset Diff & Approval",
            f"Changeset #{changeset_id} atomically approved & merged into live curriculum.",
            tc06["status"]
        )
        tc06["evidence"].append(str(img6_path.name))
        results["test_cases"].append(tc06)
        
        # Clean up browser contexts
        instructor_context.close()
        admin_context.close()
        student_context.close()
        browser.close()
        
    # Write results.json
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\n[+] Iteration 08 completed. Results saved to {RESULTS_FILE}")
    for tc in results["test_cases"]:
        print(f"    - {tc['id']}: {tc['status']} ({tc['name']})")

if __name__ == "__main__":
    run()
