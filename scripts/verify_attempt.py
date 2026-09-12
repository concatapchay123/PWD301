import sys
import re
import requests

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://localhost:5000"

def check_attempt():
    session = requests.Session()
    # Login as student
    p = session.get(f"{BASE_URL}/auth/login")
    m = re.search(r'name="csrf_token" value="([^"]+)"', p.text)
    csrf_token = m.group(1) if m else ""

    r = session.post(f"{BASE_URL}/auth/login", data={
        "email": "admin@pwd301.local",
        "password": "Password123!",
        "csrf_token": csrf_token,
    })
    print("Admin login status:", r.status_code)

    att_id = "a9148cca-9ffd-4617-a696-d5b411eddfd1"
    print("Testing IN_PROGRESS Attempt ID:", att_id)

    r = session.get(f"{BASE_URL}/student/attempt/{att_id}")
    print(f"GET /student/attempt/{att_id}: {r.status_code}")
    print("Attempt page snippet:", r.text[:300])
    # Verify attempt shell structure:
    assert 'class="attempt-container"' in r.text or 'attempt-container' in r.text, "Attempt container not found"
    assert 'attempt-shell' in r.text, "Attempt shell not found"
    assert 'attempt-main-column' in r.text, "Attempt main column not found"
    assert 'question-block' in r.text, "Question block not found"
    assert 'timer-card' in r.text, "Timer card not found"
    assert 'nav-palette-btn' in r.text, "Question palette not found"
    print("PASS: Attempt page rendered properly with questions and sidebar layout!")

if __name__ == "__main__":
    check_attempt()
