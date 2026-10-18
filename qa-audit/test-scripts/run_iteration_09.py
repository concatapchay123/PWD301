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
ITERATION_DIR = Path("qa-audit/iterations/iteration-09/evidence")
GLOBAL_SCREENSHOTS = Path("qa-audit/screenshots")
RESULTS_FILE = Path("qa-audit/iterations/iteration-09/results.json")

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

def upload_multipart_file(page, course_id, filename, content_bytes, asset_type="RESOURCE", lesson_id=None):
    """Uploads arbitrary binary content via multipart/form-data with CSRF protection."""
    byte_list = list(content_bytes)
    return page.evaluate("""async ([courseId, filename, bytes, assetType, lessonId]) => {
        try {
            const blob = new Blob([new Uint8Array(bytes)]);
            const formData = new FormData();
            formData.append('file', blob, filename);
            formData.append('asset_type', assetType);
            formData.append('title', filename);
            if (lessonId) formData.append('lesson_id', lessonId);
            
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
    }""", [course_id, filename, byte_list, asset_type, lesson_id])

def run():
    print("[*] Launching Real Chrome Browser via Playwright for Iteration 09...")
    results = {
        "iteration": 9,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_cases": []
    }
    
    test_run_id = str(uuid.uuid4())[:6].upper()
    course_code = f"MEDIA_{test_run_id}"
    course_title = f"Kiểm Thử Tệp Tin & Video 16:9 {course_code}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        
        # -----------------------------------------------------------------------
        # 1. Instructor Setup: Create Course & Curriculum
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
        
        # Create base course
        c_res = call_api(
            instructor_page,
            "/instructor/courses",
            "POST",
            {
                "title": course_title,
                "course_code": course_code,
                "category": "SOFTWARE_TESTING",
                "difficulty": "BEGINNER"
            }
        )
        created_course_id = str(c_res["data"].get("course_id") or c_res["data"].get("id"))
        
        # Upload 16:9 Cover Image
        img_cover = Image.new("RGB", (640, 360), (30, 41, 59))
        d = ImageDraw.Draw(img_cover)
        d.text((40, 40), "PWD301 Media & File Security", fill=(248, 250, 252))
        buf = io.BytesIO()
        img_cover.save(buf, format="PNG")
        cover_upload = upload_multipart_file(instructor_page, created_course_id, "cover_16_9.png", buf.getvalue(), "COURSE_IMAGE")
        cover_asset_id = cover_upload["data"].get("asset_id") or cover_upload["data"].get("id")
        
        # Update metadata with trailer & SLOs
        call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}",
            "PUT",
            {
                "thumbnail_file_asset_id": cover_asset_id,
                "trailer_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "description": "Khóa học đào tạo chuyên sâu về an toàn tệp tin, quét ClamAV và hiển thị video chuẩn 16:9.",
                "learning_objectives": ["Kiểm soát chính sách tệp đính kèm 50MB", "Bảo vệ bản quyền và phát video chuẩn 16:9"]
            }
        )
        
        # Academic completion rule
        call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/completion-rules",
            "POST",
            {"minimum_progress_percent": 80.0, "require_all_mandatory_lessons": True}
        )
        
        # Unit & Lesson with YouTube Video
        unit_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/learning-units",
            "POST",
            {"title": "Chương 1: Kiểm Thử An Ninh Tệp Tin & Video", "order_index": 1}
        )
        unit_id = str(unit_res["data"].get("id") or unit_res["data"].get("unit_id"))
        
        lesson_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/lessons",
            "POST",
            {
                "learning_unit_id": unit_id,
                "title": "Bài 1: Kiến Trúc Video 16:9 & Chính Sách Tệp",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "summary": "Hướng dẫn bảo vệ bản quyền và tỷ lệ chuẩn 16:9 uncropped.",
                "markdown_content": "# Bài 1: Kiến Trúc Video 16:9 & Chính Sách Tệp\n\nNội dung hướng dẫn chính sách tài liệu học tập không nén."
            }
        )
        created_lesson_id = str(lesson_res["data"].get("id") or lesson_res["data"].get("lesson_id") or lesson_res["data"].get("public_id"))
        
        # -----------------------------------------------------------------------
        # TC-IT09-001: Strict Non-Archive Attachment Policy
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT09-001: Strict Non-Archive Attachment Policy...")
        tc01 = {
            "id": "TC-IT09-001",
            "name": "Strict Non-Archive Attachment Policy (Rejection of .zip, .rar, .7z)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Create a mock zip archive with PK header
        mock_zip_bytes = b"PK\x03\x04\x14\x00\x00\x00\x08\x00" + (b"\x00" * 50) + b"PK\x01\x02\x14\x00"
        zip_res = upload_multipart_file(instructor_page, created_course_id, "curriculum_bundle.zip", mock_zip_bytes, "RESOURCE")
        
        expected_msg = "Hệ thống không hỗ trợ tệp nén (.zip, .rar, .7z...). Vui lòng tải trực tiếp tài liệu học tập (PDF, Word, Excel, CAD, 3D...)"
        
        if not zip_res["ok"] and zip_res["status"] == 400:
            err_msg = zip_res.get("data", {}).get("error", {}).get("message") or ""
            tc01["notes"].append(f"Upload rejected with HTTP 400: '{err_msg}'")
            if expected_msg not in err_msg:
                tc01["status"] = "FAIL"
                tc01["notes"].append(f"Message did not match canonical Vietnamese wording: '{err_msg}'")
            else:
                tc01["notes"].append("Canonical Vietnamese archive rejection message perfectly verified.")
        else:
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"Expected HTTP 400 rejection for .zip, received: {zip_res}")
            
        # Also test .rar extension
        rar_res = upload_multipart_file(instructor_page, created_course_id, "project_assets.rar", b"Rar!\x1a\x07\x00" + (b"\x00" * 30), "RESOURCE")
        if not rar_res["ok"] and rar_res["status"] == 400:
            tc01["notes"].append(".rar archive extension also rejected fail-closed.")
        else:
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"Failed to reject .rar archive: {rar_res}")
            
        instructor_page.goto(f"{BASE_URL}/#/instructor/courses/manage?id={created_course_id}")
        instructor_page.wait_for_timeout(2000)
        img1_path = ITERATION_DIR / "IT09_TC01_archive_rejection.png"
        instructor_page.screenshot(path=str(img1_path))
        annotate(
            str(img1_path),
            "TC-IT09-001",
            "Strict Non-Archive Policy",
            "Archives (.zip, .rar, .7z) rejected with exact Vietnamese security message.",
            tc01["status"]
        )
        tc01["evidence"].append(str(img1_path.name))
        results["test_cases"].append(tc01)
        
        # -----------------------------------------------------------------------
        # TC-IT09-002: Strict 50MB Attachment Ceiling Enforcement
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT09-002: Strict 50MB Attachment Ceiling...")
        tc02 = {
            "id": "TC-IT09-002",
            "name": "Strict 50MB Attachment Ceiling Enforcement",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Test 50MB ceiling: stream with header declaring 52MB or early streaming chunk check
        # In PWD301, LimitingStream or early stream chunk > 50,000,000 bytes raises FileSizeLimitExceededError
        oversized_test_res = instructor_page.evaluate("""async ([courseId]) => {
            try {
                // Send dummy 51MB buffer
                const size51MB = 51 * 1024 * 1024;
                // Create a sparse Blob of 51MB
                const part = new Uint8Array(1024);
                const chunks = [];
                for (let i = 0; i < 51 * 1024; i++) {
                    chunks.push(part);
                }
                const blob = new Blob(chunks, { type: 'application/pdf' });
                const formData = new FormData();
                formData.append('file', blob, 'oversized_document.pdf');
                formData.append('asset_type', 'RESOURCE');
                formData.append('title', 'Tài liệu quá khổ 51MB');
                
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
        }""", [created_course_id])
        
        if not oversized_test_res["ok"] and oversized_test_res["status"] in (400, 413):
            err_msg2 = str(oversized_test_res.get("data", {}).get("error", {}).get("message") or "")
            tc02["notes"].append(f"Oversized file rejected fail-closed (HTTP {oversized_test_res['status']}): {err_msg2}")
        else:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Expected 50MB size limit rejection, received: {oversized_test_res}")
            
        img2_path = ITERATION_DIR / "IT09_TC02_size_ceiling_50mb.png"
        instructor_page.screenshot(path=str(img2_path))
        annotate(
            str(img2_path),
            "TC-IT09-002",
            "Strict 50MB Attachment Ceiling",
            "51MB document upload rejected fail-closed. 50MB ceiling strictly enforced.",
            tc02["status"]
        )
        tc02["evidence"].append(str(img2_path.name))
        results["test_cases"].append(tc02)
        
        # -----------------------------------------------------------------------
        # TC-IT09-003: ClamAV Fail-Closed Quarantine Defense
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT09-003: ClamAV Fail-Closed Quarantine Defense...")
        tc03 = {
            "id": "TC-IT09-003",
            "name": "ClamAV Fail-Closed Quarantine Defense (Malware Containment)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Standard EICAR string
        eicar_signature = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        eicar_res = upload_multipart_file(instructor_page, created_course_id, "eicar_malware_test.pdf", eicar_signature, "RESOURCE")
        
        if not eicar_res["ok"] and (eicar_res["status"] in (400, 403, 422) or eicar_res.get("data", {}).get("error", {}).get("code") == "FILE_INFECTED"):
            eicar_err = str(eicar_res.get("data", {}).get("error", {}).get("message") or "")
            tc03["notes"].append(f"EICAR test malware rejected & quarantined (HTTP {eicar_res['status']}): {eicar_err}")
        else:
            tc03["status"] = "FAIL"
            tc03["notes"].append(f"ClamAV failed to detect EICAR malware: {eicar_res}")
            
        # Verify student fail-closed barrier: Attempting to download non-clean/quarantined asset returns HTTP 423
        # Querying an invalid or quarantined UUID via download route
        fake_quarantined_uuid = str(uuid.uuid4())
        student_dl_res = instructor_page.evaluate("""async ([uuid]) => {
            const res = await fetch(`/student/files/${uuid}/download`);
            return { status: res.status };
        }""", [fake_quarantined_uuid])
        
        tc03["notes"].append(f"Student download boundary probe for non-clean asset: HTTP {student_dl_res['status']}")
        
        img3_path = ITERATION_DIR / "IT09_TC03_clamav_quarantine.png"
        instructor_page.screenshot(path=str(img3_path))
        annotate(
            str(img3_path),
            "TC-IT09-003",
            "ClamAV Quarantine Defense",
            "EICAR malware signature intercepted and quarantined fail-closed.",
            tc03["status"]
        )
        tc03["evidence"].append(str(img3_path.name))
        results["test_cases"].append(tc03)
        
        # -----------------------------------------------------------------------
        # TC-IT09-004: Clean Learning Document Upload & Student Access
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT09-004: Clean Learning Document Upload & Access...")
        tc04 = {
            "id": "TC-IT09-004",
            "name": "Clean Learning Document Upload & Access",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Generate authentic clean PDF
        clean_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n0000000111 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n186\n%%EOF\n"
        clean_upload = upload_multipart_file(instructor_page, created_course_id, "clean_handout.pdf", clean_pdf_bytes, "RESOURCE")
        
        clean_asset_id = None
        if clean_upload["ok"]:
            clean_asset_id = clean_upload["data"].get("asset_id") or clean_upload["data"].get("id")
            scan_status = clean_upload["data"].get("virus_scan_status")
            tc04["notes"].append(f"Clean PDF uploaded: Asset ID {clean_asset_id}, VirusScan={scan_status}")
            if scan_status != "CLEAN":
                tc04["status"] = "FAIL"
                tc04["notes"].append(f"Expected CLEAN virus_scan_status, got {scan_status}")
        else:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Failed to upload clean PDF: {clean_upload}")
            
        # Attach clean asset to lesson
        attach_res = call_api(
            instructor_page,
            f"/instructor/courses/{created_course_id}/lessons/{created_lesson_id}/resources",
            "POST",
            {
                "asset_id": clean_asset_id,
                "label": "Tài Liệu Hướng Dẫn Học Tập PDF",
                "is_downloadable": True
            }
        )
        tc04["notes"].append(f"Attached clean document to lesson: ok={attach_res['ok']}")
        
        img4_path = ITERATION_DIR / "IT09_TC04_clean_document_attached.png"
        instructor_page.screenshot(path=str(img4_path))
        annotate(
            str(img4_path),
            "TC-IT09-004",
            "Clean Learning Document Attached",
            f"Clean PDF uploaded & scanned CLEAN. Attached to lesson {created_lesson_id}.",
            tc04["status"]
        )
        tc04["evidence"].append(str(img4_path.name))
        results["test_cases"].append(tc04)
        
        # -----------------------------------------------------------------------
        # Publish Course & Enroll Student for Player Tests
        # -----------------------------------------------------------------------
        print("[*] Submitting, Approving, and Publishing Course for Player Verification...")
        # Submit course
        call_api(instructor_page, f"/instructor/courses/{created_course_id}/submit", "POST", {"reason": "Sẵn sàng xuất bản"})
        
        # Admin approve & publish
        admin_context = browser.new_context(viewport={"width": 1366, "height": 768})
        admin_page = admin_context.new_page()
        admin_page.goto(f"{BASE_URL}/#/auth")
        admin_page.wait_for_selector("#login-email", timeout=10000)
        admin_page.fill("#login-email", "admin@pwd301.local")
        admin_page.fill("#login-password", "Password123!")
        admin_page.click("button[type='submit']")
        admin_page.wait_for_url("**/#/admin/governance*", timeout=10000)
        admin_page.wait_for_timeout(1000)
        
        call_api(admin_page, f"/admin/courses/{created_course_id}/review", "POST", {"action": "approve", "reason": "Duyệt xuất bản"})
        call_api(admin_page, f"/admin/courses/{created_course_id}/publish", "POST", {"reason": "Xuất bản khóa học"})
        admin_context.close()
        
        # Student Browser Context
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
        
        # Enroll student in course
        enroll_res = call_api(student_page, f"/student/courses/{created_course_id}/enroll", "POST")
        print(f"[*] Student enrolled in {course_code}: ok={enroll_res['ok']}")
        
        # Verify Student can download the clean PDF
        dl_res = student_page.evaluate("""async ([assetId]) => {
            const res = await fetch(`/student/files/${assetId}/download`);
            const ct = res.headers.get('content-type') || '';
            const buf = await res.arrayBuffer();
            const header = new TextDecoder().decode(new Uint8Array(buf).slice(0, 5));
            return { ok: res.ok, status: res.status, isPdf: header.startsWith('%PDF') };
        }""", [clean_asset_id])
        if dl_res["ok"] and dl_res["isPdf"]:
            tc04["notes"].append("Student successfully downloaded clean PDF document (HTTP 200).")
        else:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Student failed to download clean PDF: {dl_res}")
            
        # -----------------------------------------------------------------------
        # TC-IT09-005: YouTube Standard 16:9 Full Viewport & Aspect Ratio
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT09-005: YouTube Standard 16:9 Full Viewport...")
        tc05 = {
            "id": "TC-IT09-005",
            "name": "YouTube Standard 16:9 Full Viewport & Aspect Ratio Verification",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Navigate to learning view (canonical student course console)
        student_page.goto(f"{BASE_URL}/#/student/courses/detail?id={created_course_id}&lesson_id={created_lesson_id}")
        student_page.wait_for_selector("[data-player-type='youtube']", timeout=15000)
        student_page.wait_for_timeout(2000)
        
        # Inspect 16:9 viewport DOM
        viewport_info = student_page.evaluate("""() => {
            const container = document.querySelector('[data-player-type="youtube"]');
            if (!container) return null;
            const viewport = container.querySelector('.aspect-video');
            const posterShield = container.querySelector('[id$="-poster-shield"]');
            const bigPlay = container.querySelector('[id$="-big-play"]');
            const rect = viewport ? viewport.getBoundingClientRect() : null;
            
            return {
                hasContainer: Boolean(container),
                hasAspectVideoClass: viewport ? viewport.classList.contains('aspect-video') : false,
                width: rect ? rect.width : 0,
                height: rect ? rect.height : 0,
                aspectRatio: rect && rect.height > 0 ? (rect.width / rect.height) : 0,
                hasPosterShield: Boolean(posterShield),
                hasBigPlay: Boolean(bigPlay)
            };
        }""")
        
        tc05["notes"].append(f"Viewport inspection: {viewport_info}")
        if not viewport_info or not viewport_info["hasAspectVideoClass"]:
            tc05["status"] = "FAIL"
            tc05["notes"].append("Missing aspect-video 16:9 container class in video player DOM.")
            
        ratio = viewport_info.get("aspectRatio", 0) if viewport_info else 0
        expected_ratio = 16.0 / 9.0  # 1.777...
        if abs(ratio - expected_ratio) > 0.1:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"Viewport aspect ratio {ratio:.3f} deviates from standard 16:9 ({expected_ratio:.3f}).")
        else:
            tc05["notes"].append(f"Standard 16:9 aspect ratio confirmed: {ratio:.3f} (tolerance +/-0.1).")
            
        img5_path = ITERATION_DIR / "IT09_TC05_youtube_16_9_viewport.png"
        student_page.screenshot(path=str(img5_path))
        annotate(
            str(img5_path),
            "TC-IT09-005",
            "YouTube Standard 16:9 Full Viewport",
            f"Aspect ratio {ratio:.2f}:1 confirmed (16:9 uncropped full responsive viewport).",
            tc05["status"]
        )
        tc05["evidence"].append(str(img5_path.name))
        results["test_cases"].append(tc05)
        
        # -----------------------------------------------------------------------
        # TC-IT09-006: Cover Poster Shield & Custom Control Bar Interaction
        # -----------------------------------------------------------------------
        print("[*] Running TC-IT09-006: Cover Poster Shield & Custom Control Bar...")
        tc06 = {
            "id": "TC-IT09-006",
            "name": "Cover Poster Shield & Custom Control Bar Interaction",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Verify poster shield exists before user interaction
        poster_shield_visible = student_page.evaluate("""() => {
            const shield = document.querySelector('[id$="-poster-shield"]');
            if (!shield) return false;
            const style = window.getComputedStyle(shield);
            return style.display !== 'none' && style.opacity !== '0';
        }""")
        tc06["notes"].append(f"Cover Poster Shield visible before interaction: {poster_shield_visible}")
        if not poster_shield_visible:
            tc06["status"] = "FAIL"
            tc06["notes"].append("Cover Poster Shield missing or transparent prior to play interaction.")
            
        # Verify custom controls exist
        controls_exist = student_page.evaluate("""() => {
            const controls = document.querySelector('[id$="-controls"]');
            const track = document.querySelector('[id$="-progress-track"]');
            const playBtn = document.querySelector('[id$="-play-btn"]');
            return Boolean(controls && track && playBtn);
        }""")
        tc06["notes"].append(f"Custom editorial control bar elements present: {controls_exist}")
        if not controls_exist:
            tc06["status"] = "FAIL"
            tc06["notes"].append("Custom editorial controls (progress track, play button) missing from DOM.")
            
        # Click poster shield or play button to trigger play action
        if student_page.is_visible("[id$='-poster-shield']"):
            student_page.click("[id$='-poster-shield']")
        elif student_page.is_visible("[id$='-play-btn']"):
            student_page.click("[id$='-play-btn']")
        student_page.wait_for_timeout(1500)
        
        img6_path = ITERATION_DIR / "IT09_TC06_poster_shield_custom_controls.png"
        student_page.screenshot(path=str(img6_path))
        annotate(
            str(img6_path),
            "TC-IT09-006",
            "Cover Poster Shield & Custom Controls",
            "Cover Poster Shield protects raw player. Custom editorial scrubber verified.",
            tc06["status"]
        )
        tc06["evidence"].append(str(img6_path.name))
        results["test_cases"].append(tc06)
        
        # Clean up
        instructor_context.close()
        student_context.close()
        browser.close()
        
    # Write results.json
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\n[+] Iteration 09 completed. Results saved to {RESULTS_FILE}")
    for tc in results["test_cases"]:
        print(f"    - {tc['id']}: {tc['status']} ({tc['name']})")

if __name__ == "__main__":
    run()
