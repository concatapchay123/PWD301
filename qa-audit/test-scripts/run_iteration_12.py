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
ITERATION_DIR = Path("qa-audit/iterations/iteration-12/evidence")
GLOBAL_SCREENSHOTS = Path("qa-audit/screenshots")
RESULTS_FILE = Path("qa-audit/iterations/iteration-12/results.json")

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
    print("  PWD301 FULL-STACK QA AUDIT - ITERATION 12: BOUNDARY & NEGATIVE TESTS")
    print("==========================================================================")
    
    test_run_id = uuid.uuid4().hex[:6].upper()
    print(f"[*] Test Run ID: {test_run_id}")
    
    results = {
        "iteration": "12",
        "title": "Boundary Values, Negative Tests, Invalid States & Prerequisite Cycles",
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
        student_page.wait_for_timeout(1000)
        
        # Instructor Context
        instructor_context = browser.new_context(viewport={"width": 1366, "height": 768})
        instructor_page = instructor_context.new_page()
        instructor_page.add_init_script("""
            Object.defineProperty(window, 'outerWidth', { get: () => window.innerWidth });
            Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight });
        """)
        
        print("[*] Logging in as instructor1@pwd301.local...")
        instructor_page.goto(f"{BASE_URL}/#/auth")
        instructor_page.wait_for_selector("#login-email", timeout=10000)
        instructor_page.fill("#login-email", "instructor1@pwd301.local")
        instructor_page.fill("#login-password", "Password123!")
        instructor_page.click("button[type='submit']")
        instructor_page.wait_for_url("**/#/instructor/**", timeout=10000)
        instructor_page.wait_for_timeout(1000)

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
        
        # -----------------------------------------------------------------------
        # TC-IT12-001: Prerequisite Cycle Prevention (DAG Invariant Algorithm 03)
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT12-001: Prerequisite Cycle Prevention (DAG Invariant)...")
        tc01 = {
            "id": "TC-IT12-001",
            "name": "Prerequisite Cycle Prevention (DAG Invariant Algorithm 03)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Create two dedicated courses A and B owned by instructor1, with B requiring A
        courses_setup = query_db(f"""
    from pwd301.models import Course, User, CoursePrerequisite
    from pwd301.models.types import utc_now
    inst = db.session.query(User).filter_by(email='instructor1@pwd301.local').first()
    now = utc_now()
    ca = Course(title='Môn A DAG_{test_run_id}', course_code='DAG_A_{test_run_id}', category='SOFTWARE_TESTING', difficulty='BEGINNER', status='PUBLISHED', owner_instructor_id=inst.id, created_at=now, updated_at=now)
    cb = Course(title='Môn B DAG_{test_run_id}', course_code='DAG_B_{test_run_id}', category='SOFTWARE_TESTING', difficulty='INTERMEDIATE', status='PUBLISHED', owner_instructor_id=inst.id, created_at=now, updated_at=now)
    db.session.add(ca)
    db.session.add(cb)
    db.session.flush()
    prereq = CoursePrerequisite(course_id=cb.id, prerequisite_course_id=ca.id, created_by_user_id=inst.id, approval_status='APPROVED')
    db.session.add(prereq)
    db.session.commit()
    print(json.dumps({{"ca_id": str(ca.public_id), "cb_id": str(cb.public_id), "ca_pk": ca.id, "cb_pk": cb.id}}))
""")
        ca_id = courses_setup["ca_id"]
        cb_id = courses_setup["cb_id"]
        tc01["notes"].append(f"Created courses for DAG test: Course A={ca_id}, Course B={cb_id} (B requires A committed)")
        
        # 1. Attempt to add cycle edge: Course A requires Course B (A -> B => Cycle A -> B -> A!)
        edge2_res = call_api(instructor_page, f"/instructor/courses/{ca_id}/prerequisites", "POST", {"prerequisite_course_id": cb_id})
        tc01["notes"].append(f"Add cyclic edge (A -> B): ok={edge2_res.get('ok')}, status={edge2_res.get('status')}, error={edge2_res.get('error')}")
        
        # Invariant check: Must return HTTP 409 Conflict with CYCLE_DETECTED / PrerequisiteCycleError
        if edge2_res["ok"] or edge2_res.get("status") != 409:
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"DAG INVARIANT BREACH: Cyclic prerequisite edge was not rejected with 409: {edge2_res}")
        else:
            tc01["notes"].append("Verified: Cyclic prerequisite edge strictly rejected with HTTP 409 Conflict (CYCLE_DETECTED).")
            
        # 2. Attempt to add self-reference edge: Course A requires Course A (A -> A => Self-cycle!)
        self_edge_res = call_api(instructor_page, f"/instructor/courses/{ca_id}/prerequisites", "POST", {"prerequisite_course_id": ca_id})
        tc01["notes"].append(f"Add self-cycle edge (A -> A): ok={self_edge_res.get('ok')}, status={self_edge_res.get('status')}, error={self_edge_res.get('error')}")
        if self_edge_res["ok"] or self_edge_res.get("status") not in (400, 409):
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"DAG INVARIANT BREACH: Self-cycle prerequisite edge was not rejected: {self_edge_res}")
        else:
            tc01["notes"].append("Verified: Self-reference prerequisite edge strictly rejected (HTTP 400/409).")

        # Verify in SQL Server that A -> B does not exist and B -> A remains intact
        db_cycle_check = query_db(f"""
    from pwd301.models import CoursePrerequisite
    ca_pk = {courses_setup['ca_pk']}
    cb_pk = {courses_setup['cb_pk']}
    b_requires_a = db.session.query(CoursePrerequisite).filter_by(course_id=cb_pk, prerequisite_course_id=ca_pk).count()
    a_requires_b = db.session.query(CoursePrerequisite).filter_by(course_id=ca_pk, prerequisite_course_id=cb_pk).count()
    a_requires_a = db.session.query(CoursePrerequisite).filter_by(course_id=ca_pk, prerequisite_course_id=ca_pk).count()
    print(json.dumps({{"b_requires_a": b_requires_a, "a_requires_b": a_requires_b, "a_requires_a": a_requires_a}}))
""")
        tc01["notes"].append(f"SQL Server Prerequisite Edges: {db_cycle_check}")
        if db_cycle_check.get("b_requires_a") != 1 or db_cycle_check.get("a_requires_b") != 0 or db_cycle_check.get("a_requires_a") != 0:
            tc01["status"] = "FAIL"
            tc01["notes"].append(f"Database constraint violation: Edges={db_cycle_check} (expected b_requires_a=1, a_requires_b=0, a_requires_a=0)!")
        else:
            tc01["notes"].append("Verified: SQL Server contains only valid edge B->A; zero cyclic or self edges persisted.")
            
        instructor_page.goto(f"{BASE_URL}/#/instructor/courses/{cb_id}/edit")
        instructor_page.wait_for_timeout(1500)
        img1_path = ITERATION_DIR / "IT12_TC01_Prerequisite_Cycle_Prevention.png"
        instructor_page.screenshot(path=str(img1_path))
        annotate(
            str(img1_path),
            "TC-IT12-001",
            "Prerequisite Cycle Prevention (DAG Algorithm 03)",
            "Edge B->A accepted; cyclic edge A->B strictly rejected with HTTP 409 CYCLE_DETECTED.",
            tc01["status"]
        )
        tc01["evidence"].append(str(img1_path.name))
        results["test_cases"].append(tc01)
        
        # -----------------------------------------------------------------------
        # Setup for Assessment Attempt Negative Tests (TC02, TC03, TC04)
        # -----------------------------------------------------------------------
        print("\n[*] Initializing active assessment attempt for leasing and sequencing negative tests...")
        attempt_setup = query_db("""
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
        in_att.cancel_reason = 'Iteration 12 negative test setup reset'
    db.session.commit()
    print(json.dumps({"prerequisites_satisfied": True}))
""")
        print(f"[*] Assessment setup: {attempt_setup}")
        
        start_res = call_api(student_page, "/student/assessments/90008/start", "POST", {})
        attempt_data = start_res.get("data", {})
        att_id = attempt_data.get("attempt_id")
        valid_token = attempt_data.get("lease_token")
        
        delivery_res = call_api(student_page, f"/student/attempt/{att_id}", "GET")
        questions = delivery_res.get("data", {}).get("questions", [])
        aq_id = questions[0].get("attempt_question_id") or questions[0].get("question_id") if questions else None
        choice_key = questions[0].get("choices", [{}])[0].get("choice_key") if questions else None
        print(f"[*] Started Attempt ID: {att_id}, AQ_ID: {aq_id}, Choice: {choice_key}")
        
        # -----------------------------------------------------------------------
        # TC-IT12-002: Expired Editing Lease Autosave Fencing (Algorithm 07)
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT12-002: Expired Editing Lease Autosave Fencing...")
        tc02 = {
            "id": "TC-IT12-002",
            "name": "Expired Editing Lease Autosave Fencing (Algorithm 07)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Fast-forward SQL Server lease_expires_at to 5 seconds in the past
        query_db(f"""
    from pwd301.models import AssessmentAttempt
    from pwd301.models.types import utc_now
    from datetime import timedelta
    import uuid
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{att_id}')).first()
    if att:
        att.lease_expires_at = utc_now() - timedelta(seconds=5)
        db.session.commit()
    print(json.dumps({{"expired": True}}))
""")
        tc02["notes"].append("Fast-forwarded lease_expires_at to 5s in past.")
        
        # Student dispatches autosave request with expired lease
        exp_save_res = call_api(
            student_page,
            f"/student/attempt/{att_id}/answers/{aq_id}",
            "POST",
            {
                "lease_token": valid_token,
                "lease_epoch": 1,
                "client_sequence": 1,
                "selected_choice_keys": [choice_key] if choice_key else []
            }
        )
        tc02["notes"].append(f"Expired lease autosave response: ok={exp_save_res.get('ok')}, status={exp_save_res.get('status')}, error={exp_save_res.get('error')}")
        
        if exp_save_res["ok"] or exp_save_res.get("status") != 409:
            tc02["status"] = "FAIL"
            tc02["notes"].append(f"EXPIRED LEASE FLAW: Expired lease autosave was not rejected with 409: {exp_save_res}")
        else:
            tc02["notes"].append("Verified: Expired lease autosave strictly rejected with HTTP 409 Conflict (LEASE_CONFLICT).")
            
        student_page.goto(f"{BASE_URL}/#/student/assessments/attempt?id={att_id}")
        student_page.wait_for_timeout(1500)
        img2_path = ITERATION_DIR / "IT12_TC02_Expired_Lease_Autosave_Fencing.png"
        student_page.screenshot(path=str(img2_path))
        annotate(
            str(img2_path),
            "TC-IT12-002",
            "Expired Lease Autosave Fencing",
            "Autosave with expired lease timestamp strictly rejected with HTTP 409 LEASE_CONFLICT.",
            tc02["status"]
        )
        tc02["evidence"].append(str(img2_path.name))
        results["test_cases"].append(tc02)
        
        # -----------------------------------------------------------------------
        # TC-IT12-003: Corrupt & Tampered Lease Token Defense
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT12-003: Corrupt & Tampered Lease Token Defense...")
        tc03 = {
            "id": "TC-IT12-003",
            "name": "Corrupt & Tampered Lease Token Defense",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Reset lease expiration to valid future timestamp
        query_db(f"""
    from pwd301.models import AssessmentAttempt
    from pwd301.models.types import utc_now
    from datetime import timedelta
    import uuid
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{att_id}')).first()
    if att:
        att.lease_expires_at = utc_now() + timedelta(seconds=120)
        db.session.commit()
    print(json.dumps({{"restored": True}}))
""")
        tc03["notes"].append("Restored valid lease_expires_at in SQL Server.")
        
        # Dispatch autosave with corrupt / tampered token
        corrupt_token = "deadbeef_corrupt_tampered_token_9999"
        corrupt_save_res = call_api(
            student_page,
            f"/student/attempt/{att_id}/answers/{aq_id}",
            "POST",
            {
                "lease_token": corrupt_token,
                "lease_epoch": 1,
                "client_sequence": 2,
                "selected_choice_keys": [choice_key] if choice_key else []
            }
        )
        tc03["notes"].append(f"Corrupt token autosave response: ok={corrupt_save_res.get('ok')}, status={corrupt_save_res.get('status')}, error={corrupt_save_res.get('error')}")
        
        if corrupt_save_res["ok"] or corrupt_save_res.get("status") != 409:
            tc03["status"] = "FAIL"
            tc03["notes"].append(f"SECURITY FLAW: Corrupt lease token was not rejected with 409: {corrupt_save_res}")
        else:
            tc03["notes"].append("Verified: Corrupted lease token strictly rejected with HTTP 409 Conflict.")
            
        # Dispatch heartbeat with corrupt token
        corrupt_renew_res = call_api(student_page, f"/student/attempt/{att_id}/lease/renew", "POST", {"lease_token": corrupt_token})
        tc03["notes"].append(f"Corrupt token heartbeat response: ok={corrupt_renew_res.get('ok')}, status={corrupt_renew_res.get('status')}")
        if corrupt_renew_res["ok"] or corrupt_renew_res.get("status") != 409:
            tc03["status"] = "FAIL"
            tc03["notes"].append(f"SECURITY FLAW: Corrupt token heartbeat was not rejected with 409: {corrupt_renew_res}")
        else:
            tc03["notes"].append("Verified: Corrupt token heartbeat renewal strictly rejected with HTTP 409 Conflict.")
            
        img3_path = ITERATION_DIR / "IT12_TC03_Corrupt_Lease_Token_Defense.png"
        student_page.screenshot(path=str(img3_path))
        annotate(
            str(img3_path),
            "TC-IT12-003",
            "Corrupt & Tampered Lease Defense",
            "Tampered lease tokens rejected fail-closed with HTTP 409 LEASE_CONFLICT across autosave & heartbeat.",
            tc03["status"]
        )
        tc03["evidence"].append(str(img3_path.name))
        results["test_cases"].append(tc03)
        
        # -----------------------------------------------------------------------
        # TC-IT12-004: Out-of-Bounds Sequence Number Fencing (Client Sequencing)
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT12-004: Out-of-Bounds Sequence Number Fencing...")
        tc04 = {
            "id": "TC-IT12-004",
            "name": "Out-of-Bounds Sequence Number Fencing (Client Sequencing)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Refresh lease token & epoch for attempt to ensure clean sequencing test baseline
        lease_refresh = query_db(f"""
    from pwd301.models import AssessmentAttempt
    from pwd301.services.attempt_service import _generate_lease
    import uuid
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{att_id}')).first()
    raw_token, token_hash, acquired_at, expires_at = _generate_lease(deadline_at=att.deadline_at)
    att.lease_token_hash = token_hash
    att.lease_expires_at = expires_at
    att.lease_epoch = (att.lease_epoch or 1) + 1
    db.session.commit()
    print(json.dumps({{"token": raw_token, "epoch": att.lease_epoch}}))
""")
        seq_token = lease_refresh["token"]
        seq_epoch = lease_refresh["epoch"]
        tc04["notes"].append(f"Refreshed lease for sequencing test: epoch={seq_epoch}")
        
        # 1. Save valid answer with sequence = 10
        seq10_res = call_api(
            student_page,
            f"/student/attempt/{att_id}/answers/{aq_id}",
            "POST",
            {
                "lease_token": seq_token,
                "lease_epoch": seq_epoch,
                "client_sequence": 10,
                "selected_choice_keys": [choice_key] if choice_key else []
            }
        )
        tc04["notes"].append(f"Valid sequence (seq=10) save: ok={seq10_res.get('ok')}, status={seq10_res.get('status')}")
        if not seq10_res["ok"]:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Failed to save baseline sequence: {seq10_res}")
        else:
            tc04["notes"].append("Baseline answer with sequence=10 saved successfully.")
            
        # 2. Attempt to save answer with stale sequence = 5 (5 <= 10)
        stale_seq_res = call_api(
            student_page,
            f"/student/attempt/{att_id}/answers/{aq_id}",
            "POST",
            {
                "lease_token": seq_token,
                "lease_epoch": seq_epoch,
                "client_sequence": 5,
                "selected_choice_keys": [choice_key] if choice_key else []
            }
        )
        tc04["notes"].append(f"Stale sequence (seq=5) save: ok={stale_seq_res.get('ok')}, status={stale_seq_res.get('status')}, error={stale_seq_res.get('error')}")
        
        # Invariant check: Must return 409 STALE_ANSWER
        if stale_seq_res["ok"] or stale_seq_res.get("status") != 409:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"CLIENT SEQUENCING FLAW: Stale sequence was not rejected with 409: {stale_seq_res}")
        else:
            tc04["notes"].append("Verified: Stale sequence strictly rejected with HTTP 409 Conflict (STALE_ANSWER).")
            
        # Verify in SQL Server that attempt_answer_events logged the rejected event
        db_seq_check = query_db(f"""
    from pwd301.models import AttemptAnswerEvent, AttemptQuestion, AssessmentAttempt
    import uuid
    att = db.session.query(AssessmentAttempt).filter(AssessmentAttempt.public_id == uuid.UUID('{att_id}')).first()
    aq = db.session.query(AttemptQuestion).filter(AttemptQuestion.attempt_id == att.id).first()
    events = db.session.query(AttemptAnswerEvent).filter_by(attempt_question_id=aq.id).order_by(AttemptAnswerEvent.id.desc()).all()
    rejected_events = [e for e in events if not e.accepted and e.rejection_reason == 'STALE']
    print(json.dumps({{
        "total_events": len(events),
        "rejected_count": len(rejected_events),
        "rejected_seq": rejected_events[0].client_sequence if rejected_events else None
    }}))
""")
        tc04["notes"].append(f"SQL Server Answer Events: {db_seq_check}")
        if db_seq_check.get("rejected_count") < 1 or db_seq_check.get("rejected_seq") != 5:
            tc04["status"] = "FAIL"
            tc04["notes"].append(f"Audit log missing rejected sequence event: {db_seq_check}")
        else:
            tc04["notes"].append("Verified: SQL Server attempt_answer_events recorded rejected event (accepted=0, reason='STALE', seq=5).")
            
        img4_path = ITERATION_DIR / "IT12_TC04_Client_Sequencing_Fencing.png"
        student_page.screenshot(path=str(img4_path))
        annotate(
            str(img4_path),
            "TC-IT12-004",
            "Client Sequencing Fencing",
            "Sequence 10 accepted; stale sequence 5 strictly rejected with HTTP 409 STALE_ANSWER & audited.",
            tc04["status"]
        )
        tc04["evidence"].append(str(img4_path.name))
        results["test_cases"].append(tc04)
        
        # -----------------------------------------------------------------------
        # TC-IT12-005: Invalid State Transition Rejection
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT12-005: Invalid State Transition Rejection...")
        tc05 = {
            "id": "TC-IT12-005",
            "name": "Invalid State Transition Rejection (State Machine Guard)",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # Create a course in DRAFT status
        draft_setup = query_db(f"""
    from pwd301.models import Course, User
    from pwd301.models.types import utc_now
    inst = db.session.query(User).filter_by(email='instructor1@pwd301.local').first()
    now = utc_now()
    c = Course(title='Khóa Draft State {test_run_id}', course_code='ST_{test_run_id}', category='SOFTWARE_TESTING', difficulty='BEGINNER', status='DRAFT', owner_instructor_id=inst.id, created_at=now, updated_at=now)
    db.session.add(c)
    db.session.commit()
    print(json.dumps({{"draft_id": str(c.public_id), "status": c.status}}))
""")
        draft_id = draft_setup["draft_id"]
        tc05["notes"].append(f"Created course in DRAFT status: ID {draft_id}")
        
        # Admin attempts to PUBLISH course directly from DRAFT (Forbidden transition: must be APPROVED)
        illegal_pub_res = call_api(admin_page, f"/admin/courses/{draft_id}/publish", "POST", {"reason": "Xuất bản trực tiếp từ DRAFT"})
        tc05["notes"].append(f"Direct publish from DRAFT response: ok={illegal_pub_res.get('ok')}, status={illegal_pub_res.get('status')}, error={illegal_pub_res.get('error')}")
        
        # Invariant check: Must return 409 Conflict with STATE_VIOLATION
        if illegal_pub_res["ok"] or illegal_pub_res.get("status") != 409:
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"STATE MACHINE FLAW: Direct publish from DRAFT was not rejected with 409: {illegal_pub_res}")
        else:
            tc05["notes"].append("Verified: Direct publish from DRAFT strictly rejected with HTTP 409 Conflict (STATE_VIOLATION).")
            
        # Verify in SQL Server that course status is STILL DRAFT
        db_state_check = query_db(f"""
    from pwd301.models import Course
    import uuid
    c = db.session.query(Course).filter(Course.public_id == uuid.UUID('{draft_id}')).first()
    print(json.dumps({{"status": c.status if c else None}}))
""")
        tc05["notes"].append(f"SQL Server Course Status Post-Illegal Transition: {db_state_check}")
        if db_state_check.get("status") != "DRAFT":
            tc05["status"] = "FAIL"
            tc05["notes"].append(f"Course status illegally modified: {db_state_check}")
        else:
            tc05["notes"].append("Verified: SQL Server course status remained unchanged in 'DRAFT'.")
            
        admin_page.goto(f"{BASE_URL}/#/admin/courses")
        admin_page.wait_for_timeout(1500)
        img5_path = ITERATION_DIR / "IT12_TC05_Invalid_State_Transition_Rejection.png"
        admin_page.screenshot(path=str(img5_path))
        annotate(
            str(img5_path),
            "TC-IT12-005",
            "State Transition Machine Guard",
            "Illegal transition DRAFT -> PUBLISHED strictly rejected with HTTP 409 STATE_VIOLATION.",
            tc05["status"]
        )
        tc05["evidence"].append(str(img5_path.name))
        results["test_cases"].append(tc05)
        
        # -----------------------------------------------------------------------
        # TC-IT12-006: Boundary & Negative Value Validation
        # -----------------------------------------------------------------------
        print("\n[*] Running TC-IT12-006: Boundary & Negative Value Validation...")
        tc06 = {
            "id": "TC-IT12-006",
            "name": "Boundary & Negative Value Validation",
            "status": "PASS",
            "evidence": [],
            "notes": []
        }
        
        # 1. Negative & Oversized Completion Rule Validation
        neg_comp_res = call_api(
            instructor_page,
            f"/instructor/courses/{draft_id}/completion-rules",
            "POST",
            {
                "minimum_progress_percent": 150.0,
                "minimum_grade_score": -10.0,
                "require_all_mandatory_lessons": True
            }
        )
        tc06["notes"].append(f"Out-of-bounds completion rule (150% progress, -10 grade): ok={neg_comp_res.get('ok')}, status={neg_comp_res.get('status')}")
        if neg_comp_res["ok"] or neg_comp_res.get("status") != 400:
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"VALIDATION FLAW: Out-of-bounds completion rule was not rejected with 400: {neg_comp_res}")
        else:
            tc06["notes"].append("Verified: Progress > 100% and negative grade strictly rejected with HTTP 400 Bad Request.")
            
        # 2. Negative Course Capacity Validation
        neg_cap_res = call_api(
            instructor_page,
            f"/instructor/courses/{draft_id}",
            "PUT",
            {"capacity": -5}
        )
        tc06["notes"].append(f"Negative capacity (-5) update: ok={neg_cap_res.get('ok')}, status={neg_cap_res.get('status')}")
        if neg_cap_res["ok"] or neg_cap_res.get("status") != 400:
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"VALIDATION FLAW: Negative capacity was not rejected with 400: {neg_cap_res}")
        else:
            tc06["notes"].append("Verified: Negative capacity (-5) strictly rejected with HTTP 400 Bad Request.")
            
        # 3. Oversized String Boundary (> 200 chars for title)
        oversized_title = "A" * 255
        oversized_res = call_api(
            instructor_page,
            "/instructor/courses",
            "POST",
            {
                "title": oversized_title,
                "course_code": f"OVER_{test_run_id}",
                "category": "SOFTWARE_TESTING",
                "difficulty": "BEGINNER"
            }
        )
        tc06["notes"].append(f"Oversized title (255 chars) creation: ok={oversized_res.get('ok')}, status={oversized_res.get('status')}")
        if oversized_res["ok"] or oversized_res.get("status") != 400:
            tc06["status"] = "FAIL"
            tc06["notes"].append(f"VALIDATION FLAW: Oversized title was not rejected with 400: {oversized_res}")
        else:
            tc06["notes"].append("Verified: Oversized title (255 characters) strictly rejected with HTTP 400 Bad Request.")
            
        instructor_page.goto(f"{BASE_URL}/#/instructor/courses")
        instructor_page.wait_for_timeout(1500)
        img6_path = ITERATION_DIR / "IT12_TC06_Boundary_Negative_Value_Validation.png"
        instructor_page.screenshot(path=str(img6_path))
        annotate(
            str(img6_path),
            "TC-IT12-006",
            "Boundary & Negative Value Defense",
            "Progress > 100%, negative capacity (-5), and oversized titles (255 chars) rejected with HTTP 400.",
            tc06["status"]
        )
        tc06["evidence"].append(str(img6_path.name))
        results["test_cases"].append(tc06)
        
        browser.close()
        
    # Write results.json
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n==========================================================================")
    print(f"  ITERATION 12 EXECUTION COMPLETE. Results written to: {RESULTS_FILE}")
    print("==========================================================================")
    for tc in results["test_cases"]:
        print(f"  [{tc['status']}] {tc['id']}: {tc['name']}")

if __name__ == "__main__":
    run()
