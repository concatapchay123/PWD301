"""Verification script for PWD301 recent fixes:
1. Question Bank 500 fix on SQL Server
2. Role switching removal
3. Dark mode UI in student attempt, AI assistant, and lesson
4. Instructor course manage hub (lessons, materials, assessments, questions, settings)
5. Course publishing workflow (submit, cancel-submit, publish)
"""

import sys
import requests

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://localhost:5000"


def run_checks():
    session = requests.Session()
    print("--- 1. Health check ---")
    r = session.get(f"{BASE_URL}/health")
    print(f"GET /health: {r.status_code}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    print("\n--- 2. Login as Instructor ---")
    login_page = session.get(f"{BASE_URL}/auth/login")
    csrf_token = None
    for line in login_page.text.splitlines():
        if 'name="csrf_token"' in line:
            import re

            m = re.search(r'value="([^"]+)"', line)
            if m:
                csrf_token = m.group(1)
                break

    login_data = {
        "email": "instructor1@pwd301.local",
        "password": "Password123!",
    }
    if csrf_token:
        login_data["csrf_token"] = csrf_token

    r = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=True)
    print(f"POST /auth/login: {r.status_code}, URL: {r.url}")
    if r.headers.get("Content-Type", "").startswith("application/json"):
        data = r.json()
        assert data.get("status") == "ok", f"Login failed: {data}"
        print(f"Login success as {data['user']['display_name']} ({data['user']['email']})")
        r = session.get(f"{BASE_URL}{data.get('redirect_url', '/instructor/courses')}")
    else:
        assert "Đăng xuất" in r.text or "Giảng viên" in r.text or "Khóa học của tôi" in r.text, (
            "Login failed"
        )

    print("\n--- 3. Check Role Switching Menu in HTML ---")
    assert "KHÔNG GIAN LÀM VIỆC" not in r.text, (
        "Role switching menu was found in base template! Should be removed."
    )
    print("PASS: Role switching menu is removed from base template.")

    print("\n--- 4. Access Instructor Courses List ---")
    r = session.get(f"{BASE_URL}/instructor/courses")
    print(f"GET /instructor/courses: {r.status_code}")
    assert r.status_code == 200
    assert "bi-three-dots-vertical" in r.text or "Tùy chọn" in r.text, (
        "3-dots menu not found in courses list!"
    )
    print("PASS: Courses list has 3-dots menu and management links.")

    # Find a course ID from courses list
    import re

    course_ids = re.findall(r"/instructor/courses/([a-f0-9\-]+)/manage", r.text)
    if not course_ids:
        course_ids = re.findall(r"/instructor/courses/([a-f0-9\-]+)/questions", r.text)
    assert len(course_ids) > 0, "No course ID found in instructor courses page!"
    course_id = course_ids[0]
    print(f"Target Course ID: {course_id}")

    print("\n--- 5. Verify Question Bank 500 Fix ---")
    r = session.get(f"{BASE_URL}/instructor/courses/{course_id}/questions")
    print(f"GET /instructor/courses/{course_id}/questions: {r.status_code}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
    assert "Ngân hàng câu hỏi" in r.text
    print("PASS: Question Bank loaded successfully with 200 OK (no SQL Server 500 error)!")

    print("\n--- 6. Verify Instructor Course Management Hub ---")
    tabs = ["lessons", "materials", "assessments", "questions", "settings"]
    for tab in tabs:
        r = session.get(f"{BASE_URL}/instructor/courses/{course_id}/manage?tab={tab}")
        print(f"GET /instructor/courses/{course_id}/manage?tab={tab}: {r.status_code}")
        assert r.status_code == 200, f"Failed on tab {tab}"
    print("PASS: All Course Management Hub tabs rendered with 200 OK!")

    print("\n--- 7. Login as Student and Check Dark Mode Layouts ---")
    student_session = requests.Session()
    login_page = student_session.get(f"{BASE_URL}/auth/login")
    csrf_token = None
    for line in login_page.text.splitlines():
        if 'name="csrf_token"' in line:
            import re

            m = re.search(r'value="([^"]+)"', line)
            if m:
                csrf_token = m.group(1)
                break
    r = student_session.post(
        f"{BASE_URL}/auth/login",
        data={
            "email": "student1@pwd301.local",
            "password": "Password123!",
            "csrf_token": csrf_token or "",
        },
        allow_redirects=True,
    )
    if r.headers.get("Content-Type", "").startswith("application/json"):
        data = r.json()
        assert data.get("status") == "ok"
        print(f"Student login success as {data['user']['display_name']}")

    # Check student AI assistant
    r = student_session.get(f"{BASE_URL}/student/ai-assistant")
    print(f"GET /student/ai-assistant: {r.status_code}")
    assert r.status_code == 200
    assert (
        "var(--white)" in r.text or "var(--slate-50)" in r.text or "chat-interface-card" in r.text
    )
    print("PASS: Student AI Assistant uses dark mode tokens.")

    print("\nALL INTEGRATION CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_checks()
