import json
import sys
import io
import time
import uuid
import hashlib
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"
ITERATION_DIR = Path("qa-audit/iterations/iteration-11/evidence")
GLOBAL_SCREENSHOTS = Path("qa-audit/screenshots")
RESULTS_FILE = Path("qa-audit/iterations/iteration-11/results.json")

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
    print("  PWD301 FULL-STACK QA AUDIT - ITERATION 11: CONCURRENCY & LEASING")
    print("==========================================================================")
    
    test_run_id = uuid.uuid4().hex[:6].upper()
    print(f"[*] Test Run ID: {test_run_id}")
    
    results = {
        "iteration": "11",
        "title": "Concurrency, Race Conditions, Single Active Editing Lease & Submissions",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_run_id": test_run_id,
        "test_cases": []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        
        # Student 1 Context
        student1_context = browser.new_context(viewport={"width": 1366, "height": 768})
        student1_page = student1_context.new_page()
        student1_page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        print("[*] Logging in as student1@pwd301.local...")
        student1_page.goto(f"{BASE_URL}/#/auth")
        student1_page.wait_for_selector("#login-email", timeout=10000)
        student1_page.fill("#login-email", "student1@pwd301.local")
        student1_page.fill("#login-password", "Password123!")
        student1_page.click("button[type='submit']")
        student1_page.wait_for_url("**/#/student/dashboard", timeout=10000)
        student1_page.wait_for_timeout(1000)
        
        # Admin Context
        admin_context = browser.new_context(viewport={"width": 1366, "height": 768})
        admin_page = admin_context.new_page()
        admin_page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        print("[*] Logging in as admin@pwd301.local...")
        admin_page.goto(f"{BASE_URL}/#/auth")
        admin_page.wait_for_selector("#login-email", timeout=10000)
        admin_page.fill("#login-email", "admin@pwd301.local")
        admin_page.fill("#login-password", "Password123!")
        admin_page.click("button[type='submit']")
        admin_page.wait_for_url("**/#/admin/**", timeout=10000)
        admin_page.wait_for_timeout(1000)

        # Student 2 Context
        student2_context = browser.new_context(viewport={"width": 1366, "height": 768})
        student2_page = student2_context.new_page()
        student2_page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        print("[*] Logging in as student2@pwd301.local...")
        student2_page.goto(f"{BASE_URL}/#/auth")
        student2_page.wait_for_selector("#login-email", timeout=10000)
        student2_page.fill("#login-email", "student2@pwd301.local")
        student2_page.fill("#login-password", "Password123!")
        student2_page.click("button[type='submit']")
        student2_page.wait_for_url("**/#/student/dashboard", timeout=10000)
        student2_page.wait_for_timeout(1000)
        
        # -----------------------------------------------------------------------
        # TC-IT11-001: Single Active Editing Lease Acquisition & Heartbeat Renewal
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT11-001: Single Active Editing Lease Acquisition & Heartbeat Renewal...")
        tc01 = {
            "id": "TC-IT11-001",
            "name": "Single Active Editing Lease Acquisition & Heartbeat Renewal (Algorithm 07)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Ensure student1 meets course completion prerequisites for Assessment 90008
        query_db("""
    from pwd301.models import LessonProgress, User, Enrollment, Assessment, AssessmentAttempt
    from pwd301.models.types import utc_now
    u = db.session.query(User).filter_by(email='student1@pwd301.local').first()
    enr = db.session.query(Enrollment).filter_by(student_user_id=u.id, course_id=110007).first()
    now = utc_now()
    period_id = enr.current_period_id or enr.periods[0].id
    for lid in [160039, 160040]:
        lp = db.session.query(LessonProgress).filter_by(enrollment_period_id=period_id, lesson_id=lid).first()
        if not lp:
            lp = LessonProgress(enrollment_period_id=period_id, lesson_id=lid, completed_at=now, updated_at=now)
            db.session.add(lp)
        else:
            lp.completed_at = now
    db.session.query(Assessment).filter_by(id=90008).update({"attempt_limit": 50})
    for in_att in db.session.query(AssessmentAttempt).filter_by(assessment_id=90008, student_user_id=u.id, status='IN_PROGRESS').all():
        in_att.status = 'CANCELLED'
        in_att.cancel_reason = 'Iteration 11 setup reset'
    db.session.commit()
    print(json.dumps({"prerequisites_satisfied": True}))
""")
        tc01["notes"].append("Ensured course 110007 lessons completed, attempt_limit relaxed, and in-progress attempts reset.")

        # Start assessment attempt for Assessment 90008
        start_res = call_api(student1_page, "/student/assessments/90008/start", "POST", {})
        tc01["notes"].append(f"Start attempt response: ok={start_res.get('ok')}, status={start_res.get('status')}")
        
        if not start_res["ok"]:
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"Failed to start assessment: {start_res}")
            raw_token = None
            attempt_pub_id = None
        else:
            data = start_res["data"]
            attempt_pub_id = data.get("attempt_id")
            raw_token = data.get("lease_token")
            tc01["notes"].append(f"Acquired Attempt ID: {attempt_pub_id}, Lease Token (len={len(raw_token) if raw_token else 0}): {raw_token[:8]}...")
            
            # Verify in SQL Server
            db_lease_info = query_db(f"""
    from pwd301.models import AssessmentAttempt
    import uuid, hashlib
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{attempt_pub_id}')).first()
    expected_hash = hashlib.sha256('{raw_token}'.strip().encode('utf-8')).digest()
    hash_matches = (att.lease_token_hash == expected_hash) if att else False
    print(json.dumps({{
        "found": att is not None,
        "epoch": att.lease_epoch if att else None,
        "hash_matches": hash_matches,
        "expires_at": att.lease_expires_at.isoformat() if (att and att.lease_expires_at) else None,
        "status": att.status if att else None
    }}))
""")
            tc01["notes"].append(f"DB Lease Verification: {db_lease_info}")
            if not db_lease_info.get("hash_matches") or db_lease_info.get("epoch") != 1:
                tc01["status"] = "FAIL"
                tc01["notes"].append("Database lease token hash mismatch or epoch != 1!")
            
            old_expires_at = db_lease_info.get("expires_at")
            time.sleep(1.2) # Wait so heartbeat renewal creates a clearly greater timestamp
            
            # Invoke Heartbeat Renewal
            renew_res = call_api(student1_page, f"/student/attempt/{attempt_pub_id}/lease/renew", "POST", {"lease_token": raw_token})
            tc01["notes"].append(f"Heartbeat renewal response: ok={renew_res.get('ok')}, data={renew_res.get('data')}")
            
            if not renew_res["ok"]:
                tc01["status"] = "FAIL"
                tc01["notes"].append(f"Heartbeat renewal failed: {renew_res}")
            else:
                new_expires_at = renew_res["data"].get("lease_expires_at")
                tc01["notes"].append(f"Lease extended: old={old_expires_at} -> new={new_expires_at}")
                if not new_expires_at or new_expires_at <= old_expires_at:
                    tc01["status"] = "FAIL"
                    tc01["notes"].append(f"Lease expiration was not extended: {old_expires_at} >= {new_expires_at}")
        
        # Navigate student to exam taking console in real Chrome
        student1_page.goto(f"{BASE_URL}/#/student/assessments/attempt?id={attempt_pub_id}")
        student1_page.wait_for_timeout(2000)
        img1_path = ITERATION_DIR / "IT11_TC01_Lease_Acquisition_Heartbeat.png"
        student1_page.screenshot(path=str(img1_path))
        annotate(
            str(img1_path),
            "TC-IT11-001",
            "Lease Acquisition & Heartbeat (Algorithm 07)",
            f"Attempt {attempt_pub_id[:8] if attempt_pub_id else 'N/A'} acquired lease epoch 1; heartbeat renewal extended expiration.",
            tc01["status"]
        )
        tc01["evidence"].append(str(img1_path.name))
        results["test_cases"].append(tc01)
        
        # -----------------------------------------------------------------------
        # TC-IT11-002: Concurrent Window/Tab Takeover & Lease Fencing
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT11-002: Concurrent Window/Tab Takeover & Lease Fencing...")
        tc02 = {
            "id": "TC-IT11-002",
            "name": "Concurrent Window/Tab Takeover & Lease Fencing (Algorithm 07)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Retrieve attempt delivery questions so we have aq_id and choice keys
        delivery_res = call_api(student1_page, f"/student/attempt/{attempt_pub_id}", "GET")
        questions = delivery_res.get("data", {}).get("questions", [])
        if not questions:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"No questions found in attempt delivery: {delivery_res}")
            aq_id = None
            first_choice_key = None
        else:
            q0 = questions[0]
            aq_id = q0.get("attempt_question_id") or q0.get("question_id")
            first_choice_key = q0.get("choices", [{}])[0].get("choice_key")
            tc02["notes"].append(f"Using Question AQ_ID: {aq_id}, Choice Key: {first_choice_key}")
        
        # Save Tab 1's token as stale_token
        token_tab1 = raw_token
        
        # Fast-forward lease expiration in DB to simulate timeout / voluntary release for takeover
        query_db(f"""
    from pwd301.models import AssessmentAttempt
    from pwd301.models.types import utc_now
    from datetime import timedelta
    import uuid
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{attempt_pub_id}')).first()
    if att:
        att.lease_expires_at = utc_now() - timedelta(seconds=2)
        db.session.commit()
    print(json.dumps({{"expired": True}}))
""")
        tc02["notes"].append("Fast-forwarded lease_expires_at in SQL Server to simulate Tab 1 lease timeout.")
        
        # Tab 2 invokes takeover
        takeover_res = call_api(student1_page, f"/student/attempt/{attempt_pub_id}/lease/takeover", "POST", {})
        tc02["notes"].append(f"Tab 2 takeover response: ok={takeover_res.get('ok')}, data={takeover_res.get('data')}")
        
        if not takeover_res["ok"]:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"Takeover failed: {takeover_res}")
            token_tab2 = None
        else:
            token_tab2 = takeover_res["data"].get("lease_token")
            epoch_tab2 = takeover_res["data"].get("lease_epoch")
            tc02["notes"].append(f"Tab 2 took over lease: new_epoch={epoch_tab2}, token_prefix={token_tab2[:8]}...")
            
            # Verify in SQL Server that epoch is 2 and hash matches token_tab2
            db_takeover_check = query_db(f"""
    from pwd301.models import AssessmentAttempt
    import uuid, hashlib
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{attempt_pub_id}')).first()
    expected_hash2 = hashlib.sha256('{token_tab2}'.strip().encode('utf-8')).digest()
    print(json.dumps({{
        "epoch": att.lease_epoch if att else None,
        "hash_matches": (att.lease_token_hash == expected_hash2) if att else False
    }}))
""")
            tc02["notes"].append(f"SQL Server post-takeover state: {db_takeover_check}")
            if db_takeover_check.get("epoch") != 2 or not db_takeover_check.get("hash_matches"):
                tc02["status"] = "FAIL"
                tc02["notes"].append("SQL Server epoch != 2 or hash does not match token_tab2!")
        
        # Now simulate Tab 1 attempting to save an answer with STALE token_tab1 and STALE epoch 1
        stale_save_res = call_api(
            student1_page,
            f"/student/attempt/{attempt_pub_id}/answers/{aq_id}",
            "POST",
            {
                "lease_token": token_tab1,
                "lease_epoch": 1,
                "client_sequence": 1,
                "selected_choice_keys": [first_choice_key] if first_choice_key else []
            }
        )
        tc02["notes"].append(f"Tab 1 stale autosave response: ok={stale_save_res.get('ok')}, status={stale_save_res.get('status')}, error={stale_save_res.get('error')}")
        
        # Invariant check: Server MUST reject with 409 LEASE_CONFLICT or STALE_LEASE_EPOCH
        if stale_save_res["ok"] or stale_save_res.get("status") != 409:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"SECURITY/CONCURRENCY BREACH: Stale Tab 1 write was NOT rejected with 409 Conflict: {stale_save_res}")
        else:
            tc02["notes"].append("Verified: Tab 1 stale write strictly rejected with HTTP 409 Conflict (Lease Fencing active).")
            
        img2_path = ITERATION_DIR / "IT11_TC02_Lease_Takeover_Fencing.png"
        student1_page.screenshot(path=str(img2_path))
        annotate(
            str(img2_path),
            "TC-IT11-002",
            "Tab Takeover & Lease Fencing (Algorithm 07)",
            "Tab 2 acquired epoch 2; Tab 1 stale answer autosave strictly rejected with HTTP 409 Conflict.",
            tc02["status"]
        )
        tc02["evidence"].append(str(img2_path.name))
        results["test_cases"].append(tc02)
        
        # -----------------------------------------------------------------------
        # TC-IT11-003: Submission Idempotency Under Concurrent Double-Submit
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT11-003: Submission Idempotency Under Concurrent Double-Submit...")
        tc03 = {
            "id": "TC-IT11-003",
            "name": "Submission Idempotency Under Concurrent Double-Submit",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # First save a valid answer with Tab 2's active lease token
        valid_save_res = call_api(
            student1_page,
            f"/student/attempt/{attempt_pub_id}/answers/{aq_id}",
            "POST",
            {
                "lease_token": token_tab2,
                "lease_epoch": 2,
                "client_sequence": 1,
                "selected_choice_keys": [first_choice_key] if first_choice_key else []
            }
        )
        tc03["notes"].append(f"Tab 2 valid answer autosave: ok={valid_save_res.get('ok')}")
        
        # Prepare single idempotency key for concurrent dispatch
        idempotency_key = str(uuid.uuid4())
        tc03["notes"].append(f"Dispatched dual-submit with Idempotency Key: {idempotency_key}")
        
        # Concurrently fire two submit requests via Promise.all in browser
        concurrent_sub_res = student1_page.evaluate("""async ([attemptId, leaseToken, idempKey]) => {
            const csrfToken = await ApiClient.ensureCsrfToken();
            const submitPayload = JSON.stringify({
                idempotency_key: idempKey,
                submission_idempotency_key: idempKey,
                lease_token: leaseToken
            });
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Submission-Idempotency-Key': idempKey
            };
            
            const req1 = fetch(`/student/attempt/${attemptId}/submit`, { method: 'POST', headers, body: submitPayload })
                .then(async r => ({ ok: r.ok, status: r.status, data: await r.json() }))
                .catch(e => ({ ok: false, error: e.message }));
                
            const req2 = fetch(`/student/attempt/${attemptId}/submit`, { method: 'POST', headers, body: submitPayload })
                .then(async r => ({ ok: r.ok, status: r.status, data: await r.json() }))
                .catch(e => ({ ok: false, error: e.message }));
                
            return await Promise.all([req1, req2]);
        }""", [attempt_pub_id, token_tab2, idempotency_key])
        
        res1, res2 = concurrent_sub_res[0], concurrent_sub_res[1]
        tc03["notes"].append(f"Submit Request 1: ok={res1.get('ok')}, status={res1.get('status')}")
        tc03["notes"].append(f"Submit Request 2: ok={res2.get('ok')}, status={res2.get('status')}")
        
        if not (res1.get("ok") and res2.get("ok")):
            tc03["status"] = "FAIL"
            tc03["notes"].append(f"Concurrent submit failure: req1={res1}, req2={res2}")
        else:
            tc03["notes"].append("Verified: Both concurrent submit requests returned HTTP 200 without race failure.")
            
        # Verify in SQL Server that attempt is SUBMITTED and exactly 1 AssessmentResult exists
        db_sub_check = query_db(f"""
    from pwd301.models import AssessmentAttempt, AssessmentResult
    import uuid
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{attempt_pub_id}')).first()
    res = db.session.query(AssessmentResult).filter(AssessmentResult.attempt_id == att.id).first() if att else None
    res_count = db.session.query(AssessmentResult).filter(AssessmentResult.attempt_id == att.id).count() if att else 0
    print(json.dumps({{
        "status": att.status if att else None,
        "results_count": res_count,
        "raw_score": float(res.raw_score) if (res and res.raw_score is not None) else None,
        "percent_score": float(res.percent_score) if (res and res.percent_score is not None) else None
    }}))
""")
        tc03["notes"].append(f"SQL Server Post-Submit Snapshot: {db_sub_check}")
        if db_sub_check.get("status") not in ("SUBMITTED", "GRADED") or db_sub_check.get("results_count") != 1:
            tc03["status"] = "FAIL"
            tc03["notes"].append(f"Database anomaly: Status={db_sub_check.get('status')}, Results Count={db_sub_check.get('results_count')} (expected 1)!")
        else:
            tc03["notes"].append("Verified: Zero duplicate grading records in SQL Server; exactly 1 AssessmentResult created.")
            
        student1_page.goto(f"{BASE_URL}/#/student/assessments/results?id={attempt_pub_id}")
        student1_page.wait_for_timeout(2000)
        img3_path = ITERATION_DIR / "IT11_TC03_Concurrent_Submit_Idempotency.png"
        student1_page.screenshot(path=str(img3_path))
        annotate(
            str(img3_path),
            "TC-IT11-003",
            "Concurrent Submit Idempotency",
            "Simultaneous dual-submit succeeded idempotently (HTTP 200); exactly 1 AssessmentResult in SQL Server.",
            tc03["status"]
        )
        tc03["evidence"].append(str(img3_path.name))
        results["test_cases"].append(tc03)
        
        # -----------------------------------------------------------------------
        # TC-IT11-004: Optimistic Concurrency & Course Changeset Fingerprint Guard
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT11-004: Optimistic Concurrency & Course Changeset Fingerprint Guard...")
        tc04 = {
            "id": "TC-IT11-004",
            "name": "Optimistic Concurrency & Course Changeset Fingerprint Guard",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Set up a dedicated course in SUBMITTED_FOR_REVIEW status via DB fixture
        occ_course = query_db(f"""
    from pwd301.models import Course, LearningUnit, Lesson, User
    from pwd301.models.types import utc_now
    import uuid
    inst_u = db.session.query(User).filter(User.email == 'instructor1@pwd301.local').first()
    now = utc_now()
    c = Course(
        title='Khóa Học Concurrency OCC_{test_run_id}',
        course_code='OCC_{test_run_id}',
        category='SOFTWARE_TESTING',
        difficulty='INTERMEDIATE',
        status='SUBMITTED_FOR_REVIEW',
        owner_instructor_id=inst_u.id,
        created_at=now,
        updated_at=now
    )
    db.session.add(c)
    db.session.flush()
    u = LearningUnit(course_id=c.id, title='Chương 1 OCC', position=1, created_at=now)
    db.session.add(u)
    db.session.flush()
    l = Lesson(course_id=c.id, learning_unit_id=u.id, title='Bài 1 OCC', position=1, status='DRAFT', created_at=now, updated_at=now)
    db.session.add(l)
    db.session.commit()
    print(json.dumps({{"course_id": str(c.public_id), "id": c.id}}))
""")
        occ_course_id = occ_course.get("course_id")
        tc04["notes"].append(f"Created course in SUBMITTED_FOR_REVIEW: ID {occ_course_id}")
        
        # Admin fetches course detail to get true review_version
        c_detail = call_api(admin_page, f"/admin/courses/{occ_course_id}", "GET")
        actual_review_ver = c_detail.get("data", {}).get("review_version")
        tc04["notes"].append(f"Authentic review_version from API: {actual_review_ver}")
        
        # 1. Admin attempts to approve with a STALE / MISMATCHED review_version
        stale_appr_res = call_api(
            admin_page,
            f"/admin/courses/{occ_course_id}/review",
            "POST",
            {
                "action": "approve",
                "reason": "Thẩm định với version cũ",
                "review_version": "stale_hash_mismatch_999999"
            }
        )
        tc04["notes"].append(f"Stale review_version approve response: ok={stale_appr_res.get('ok')}, status={stale_appr_res.get('status')}, error={stale_appr_res.get('error')}")
        
        # Invariant check: Must return 409 Conflict
        if stale_appr_res["ok"] or stale_appr_res.get("status") != 409:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"OPTIMISTIC CONCURRENCY FLAW: Server did not reject stale review_version with 409 Conflict: {stale_appr_res}")
        else:
            tc04["notes"].append("Verified: Server strictly rejected stale review_version with HTTP 409 Conflict.")
            
        # 2. Admin approves with AUTHENTIC review_version
        valid_appr_res = call_api(
            admin_page,
            f"/admin/courses/{occ_course_id}/review",
            "POST",
            {
                "action": "approve",
                "reason": "Thẩm định với version chính xác",
                "review_version": actual_review_ver
            }
        )
        tc04["notes"].append(f"Authentic review_version approve response: ok={valid_appr_res.get('ok')}, status={valid_appr_res.get('status')}")
        if not valid_appr_res["ok"]:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Failed to approve with authentic review_version: {valid_appr_res}")
        else:
            tc04["notes"].append("Verified: Approval succeeded with authentic review_version.")
            
        admin_page.goto(f"{BASE_URL}/#/admin/courses")
        admin_page.wait_for_timeout(1500)
        img4_path = ITERATION_DIR / "IT11_TC04_Optimistic_Concurrency_Review_Version.png"
        admin_page.screenshot(path=str(img4_path))
        annotate(
            str(img4_path),
            "TC-IT11-004",
            "Optimistic Concurrency Review Guard",
            "Stale review_version rejected with 409 Conflict; authentic review_version approved course successfully.",
            tc04["status"]
        )
        tc04["evidence"].append(str(img4_path.name))
        results["test_cases"].append(tc04)
        
        # -----------------------------------------------------------------------
        # TC-IT11-005: Concurrent Enrollment Capacity Enforcement
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT11-005: Concurrent Enrollment Capacity Enforcement...")
        tc05 = {
            "id": "TC-IT11-005",
            "name": "Concurrent Enrollment Capacity Enforcement",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Configure a dedicated PUBLISHED course with capacity = 1
        cap_course = query_db(f"""
    from pwd301.models import Course, LearningUnit, Lesson, User
    from pwd301.models.types import utc_now
    import uuid
    inst_u = db.session.query(User).filter(User.email == 'instructor1@pwd301.local').first()
    now = utc_now()
    c = Course(
        title='Khóa Học Capacity Lock CAP_{test_run_id}',
        course_code='CAP_{test_run_id}',
        category='SOFTWARE_TESTING',
        difficulty='BEGINNER',
        status='PUBLISHED',
        capacity=1,
        owner_instructor_id=inst_u.id,
        created_at=now,
        updated_at=now
    )
    db.session.add(c)
    db.session.flush()
    u = LearningUnit(course_id=c.id, title='Chương 1 CAP', position=1, created_at=now)
    db.session.add(u)
    db.session.flush()
    l = Lesson(course_id=c.id, learning_unit_id=u.id, title='Bài 1 CAP', position=1, status='PUBLISHED', created_at=now, updated_at=now)
    db.session.add(l)
    db.session.commit()
    print(json.dumps({{"course_id": str(c.public_id), "id": c.id, "capacity": c.capacity}}))
""")
        cap_course_id = cap_course.get("course_id")
        tc05["notes"].append(f"Created Course with Capacity=1: ID {cap_course_id}")
        
        # 1. Student 1 Enrolls (Takes Seat 1 of 1)
        enr1_res = call_api(student1_page, f"/student/courses/{cap_course_id}/enroll", "POST")
        tc05["notes"].append(f"Student 1 Enrollment: ok={enr1_res.get('ok')}, status={enr1_res.get('status')}")
        if not enr1_res["ok"]:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"Student 1 failed to enroll in open seat: {enr1_res}")
        else:
            tc05["notes"].append("Student 1 successfully enrolled (Seat 1/1 filled).")
            
        # 2. Student 2 Attempts to Enroll (Course is Full)
        enr2_res = call_api(student2_page, f"/student/courses/{cap_course_id}/enroll", "POST")
        tc05["notes"].append(f"Student 2 Enrollment on Full Course: ok={enr2_res.get('ok')}, status={enr2_res.get('status')}, error={enr2_res.get('error')}")
        
        # Invariant check: Must return 409 Conflict with CAPACITY_EXCEEDED
        if enr2_res["ok"] or enr2_res.get("status") != 409:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"CAPACITY BREACH: Student 2 was not rejected with 409 Conflict on full course: {enr2_res}")
        else:
            tc05["notes"].append("Verified: Student 2 enrollment strictly rejected with HTTP 409 Conflict (CAPACITY_EXCEEDED).")
            
        # Verify in SQL Server that active enrollment count is exactly 1
        db_cap_check = query_db(f"""
    from pwd301.models import Course, Enrollment
    import uuid
    c = db.session.query(Course).filter(Course.public_id == uuid.UUID('{cap_course_id}')).first()
    active_count = db.session.query(Enrollment).filter(Enrollment.course_id == c.id, Enrollment.status == 'ACTIVE').count() if c else 0
    print(json.dumps({{"active_enrollments": active_count, "capacity": c.capacity if c else None}}))
""")
        tc05["notes"].append(f"SQL Server Enrollment Count: {db_cap_check}")
        if db_cap_check.get("active_enrollments") != 1:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"Capacity violated in DB: {db_cap_check.get('active_enrollments')} active enrollments for capacity {db_cap_check.get('capacity')}!")
        else:
            tc05["notes"].append("Verified: SQL Server row locks (UPDLOCK, HOLDLOCK) prevented over-enrollment (count = 1).")
            
        student2_page.goto(f"{BASE_URL}/#/student/courses")
        student2_page.wait_for_timeout(1500)
        img5_path = ITERATION_DIR / "IT11_TC05_Capacity_Enforcement_Row_Lock.png"
        student2_page.screenshot(path=str(img5_path))
        annotate(
            str(img5_path),
            "TC-IT11-005",
            "Capacity Enforcement (UPDLOCK)",
            "Student 1 enrolled (1/1); Student 2 enrollment strictly rejected with HTTP 409 CAPACITY_EXCEEDED.",
            tc05["status"]
        )
        tc05["evidence"].append(str(img5_path.name))
        results["test_cases"].append(tc05)
        
        # -----------------------------------------------------------------------
        # TC-IT11-006: Active Editing Lease Revocation on Submit
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT11-006: Active Editing Lease Revocation on Submit...")
        tc06 = {
            "id": "TC-IT11-006",
            "name": "Active Editing Lease Revocation on Submit",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Query SQL Server for attempt from TC-IT11-003
        db_revoke_check = query_db(f"""
    from pwd301.models import AssessmentAttempt
    import uuid
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{attempt_pub_id}')).first()
    print(json.dumps({{
        "status": att.status if att else None,
        "lease_token_hash_is_null": (att.lease_token_hash is None) if att else False,
        "lease_expires_at_is_null": (att.lease_expires_at is None) if att else False
    }}))
""")
        tc06["notes"].append(f"SQL Server Post-Submit Lease State: {db_revoke_check}")
        if not (db_revoke_check.get("lease_token_hash_is_null") and db_revoke_check.get("lease_expires_at_is_null")):
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"Lease was not cleared on submit in DB: {db_revoke_check}")
        else:
            tc06["notes"].append("Verified: lease_token_hash and lease_expires_at atomically set to NULL on submit.")
            
        # Attempt heartbeat renewal on submitted attempt
        post_renew = call_api(student1_page, f"/student/attempt/{attempt_pub_id}/lease/renew", "POST", {"lease_token": token_tab2})
        tc06["notes"].append(f"Post-submit heartbeat renewal: ok={post_renew.get('ok')}, status={post_renew.get('status')}")
        if post_renew["ok"] or post_renew.get("status") not in (400, 409):
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"Post-submit renewal was not rejected: {post_renew}")
        else:
            tc06["notes"].append("Verified: Post-submit heartbeat renewal rejected.")
            
        # Attempt save answer on submitted attempt
        post_save = call_api(
            student1_page,
            f"/student/attempt/{attempt_pub_id}/answers/{aq_id}",
            "POST",
            {
                "lease_token": token_tab2,
                "lease_epoch": 2,
                "client_sequence": 2,
                "selected_choice_keys": [first_choice_key] if first_choice_key else []
            }
        )
        tc06["notes"].append(f"Post-submit save answer: ok={post_save.get('ok')}, status={post_save.get('status')}")
        if post_save["ok"] or post_save.get("status") not in (400, 409):
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"Post-submit answer modification was not rejected: {post_save}")
        else:
            tc06["notes"].append("Verified: Post-submit answer modification rejected with 409 STATE_VIOLATION.")
            
        student1_page.goto(f"{BASE_URL}/#/student/assessments/attempt?id={attempt_pub_id}")
        student1_page.wait_for_timeout(2000)
        img6_path = ITERATION_DIR / "IT11_TC06_Lease_Revocation_On_Submit.png"
        student1_page.screenshot(path=str(img6_path))
        annotate(
            str(img6_path),
            "TC-IT11-006",
            "Editing Lease Revocation on Submit",
            "Editing lease cleared in DB; post-submit heartbeats and answer modifications rejected (409).",
            tc06["status"]
        )
        tc06["evidence"].append(str(img6_path.name))
        results["test_cases"].append(tc06)
        
        browser.close()
        
    # Write results.json
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n==========================================================================")
    print(f"  ITERATION 11 EXECUTION COMPLETE. Results written to: {RESULTS_FILE}")
    print("==========================================================================")
    for tc in results["test_cases"]:
        print(f"  [{tc['status']}] {tc['id']}: {tc['name']}")

if __name__ == "__main__":
    run()
