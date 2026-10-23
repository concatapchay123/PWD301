import sys
import time
import requests

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://pptq.id.vn"
accounts = [
    ("vinhphu2020.nt@gmail.com", "Password123!", "Vĩnh Phú", "ADMIN"),
    ("danglyquan@gmail.com", "Password123!", "Đặng Lý Quân", "ADMIN"),
    ("tqtphamnguyenhoangphuc@gmail.com", "Password123!", "Hoàng Phúc", "ADMIN"),
    ("callmewin06@gmail.com", "Password123!", "Hữu Thắng", "ADMIN"),
    ("instructor@pwd301.local", "Pptq@Secure2026!", "Chuyên Gia Đào Tạo An Ninh Android", "INSTRUCTOR"),
    ("student1@pwd301.local", "Pptq@Secure2026!", "Nguyễn Văn An - Học Viên An Ninh", "STUDENT"),
    ("student2@pwd301.local", "Pptq@Secure2026!", "Trần Thị Bình - Học Viên Kiểm Thử", "STUDENT"),
]

print(f"=== TESTING AUTHENTICATION ON {BASE_URL} ===")
student_session = None

for email, pwd, expected_name, expected_role in accounts:
    time.sleep(0.5)
    s = requests.Session()
    r = s.get(f"{BASE_URL}/auth/login")
    csrf = r.cookies.get("csrf_token")
    headers = {
        "X-CSRFToken": csrf or "",
        "Referer": f"{BASE_URL}/",
        "Origin": BASE_URL,
    }
    resp = s.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": pwd},
        headers=headers,
    )
    data = resp.json()
    if resp.status_code != 200:
        print(f"[{email}] ERROR {resp.status_code}: {data}")
    user_info = (data.get("data") or {}).get("user") or {}
    print(f"[{email}] Status: {resp.status_code} | Success: {data.get('success')} | Name: '{user_info.get('display_name')}' | Role: {user_info.get('primary_role')}")
    
    sess_resp = s.get(f"{BASE_URL}/auth/session")
    sess_data = sess_resp.json()
    sess_user = sess_data.get("user") or {}
    print(f"  -> /auth/session Status: {sess_resp.status_code} | Authenticated: {sess_data.get('is_authenticated')} | User: {sess_user.get('email')} ({sess_user.get('display_name')})")
    
    # Test role-based endpoints
    if expected_role == "ADMIN":
        role_resp = s.get(f"{BASE_URL}/admin/dashboard")
        print(f"  -> /admin/dashboard Status: {role_resp.status_code} (Success: {role_resp.json().get('success')})")
        assert role_resp.status_code == 200, f"/admin/dashboard failed for {email}"
    elif expected_role == "INSTRUCTOR":
        role_resp = s.get(f"{BASE_URL}/instructor/dashboard")
        print(f"  -> /instructor/dashboard Status: {role_resp.status_code} (Success: {role_resp.json().get('success')})")
        assert role_resp.status_code == 200, f"/instructor/dashboard failed for {email}"
    elif expected_role == "STUDENT":
        role_resp = s.get(f"{BASE_URL}/student/dashboard")
        print(f"  -> /student/dashboard Status: {role_resp.status_code} (Success: {role_resp.json().get('success')})")
        assert role_resp.status_code == 200, f"/student/dashboard failed for {email}"
        if email == "student1@pwd301.local":
            student_session = s

    if not (data.get("success") is True and sess_data.get("is_authenticated") is True):
        print(f"FAILED for {email}: login={data}, session={sess_data}")
        sys.exit(1)

print("\n>>> ALL 7 ACCOUNTS LOGGED IN AND VERIFIED EMPIRICALLY! <<<")

print("\n=== VERIFYING COURSE STRUCTURE & CONTENT ON VPS ===")
c_resp = requests.get(f"{BASE_URL}/api/courses")
c_data = c_resp.json()
courses = c_data.get("data", {}).get("items", [])
print(f"Public Courses Count: {len(courses)}")
for c in courses:
    print(f"  - Course: {c.get('course_code')} | Title: {c.get('title')} | Price: {c.get('price')} VND | Status: {c.get('status')}")

master_course = next((c for c in courses if c.get("course_code") == "AND801"), None)
assert master_course is not None, "Course AND801 not found in public courses"
course_code = master_course.get("course_code")
course_id = master_course.get("course_id")
print(f"Course: {course_code} - {master_course.get('title')}")
print(f"Status: {master_course.get('status')} | Price: {master_course.get('price')} VND")

if student_session and course_id:
    detail_resp = student_session.get(f"{BASE_URL}/student/courses/{course_id}")
    detail_data = detail_resp.json().get("data", {})
    units = detail_data.get("learning_units", [])
    lessons = detail_data.get("lessons", [])
    assessments = detail_data.get("assessments", [])
    resources = detail_data.get("resources", [])
    
    print(f"Student Course Detail Status: {detail_resp.status_code}")
    print(f"  + Learning Units (Chapters): {len(units)}")
    print(f"  + Total Lessons: {len(lessons)}")
    print(f"  + Total Assessments: {len(assessments)}")
    print(f"  + Total eBook/PDF Resources: {len(resources)}")
    
    assert len(units) == 5, f"Expected 5 chapters, got {len(units)}"
    assert len(lessons) == 60, f"Expected 60 lessons, got {len(lessons)}"
    assert len(assessments) == 6, f"Expected 6 assessments, got {len(assessments)}"

    # Check first lesson detail
    first_lesson = lessons[0]
    lesson_id = first_lesson.get("public_id")
    l_resp = student_session.get(f"{BASE_URL}/student/courses/{course_id}/lessons/{lesson_id}")
    l_data = l_resp.json()
    lesson_obj = l_data.get("data") or {}
    print(f"\nLesson 1 Detail Status: {l_resp.status_code}")
    print(f"  + Title: {lesson_obj.get('title')}")
    print(f"  + Video URL: {lesson_obj.get('video_url')}")
    print(f"  + Estimated Duration: {lesson_obj.get('estimated_duration_minutes')} mins")

print("\n>>> ALL VERIFICATION STEPS PASSED WITH 100% SUCCESS! <<<")
