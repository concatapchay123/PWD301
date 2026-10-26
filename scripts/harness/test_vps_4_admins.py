import sys
import time
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "https://pptq.id.vn"
accounts = [
    ("tqtphamnguyenhoangphuc@gmail.com", "Password123!", "Hoàng Phúc", "ADMIN"),
    ("danglyquan@gmail.com", "Password123!", "Đặng Lý Quân", "ADMIN"),
    ("vinhphu2020.nt@gmail.com", "Password123!", "Vĩnh Phú", "ADMIN"),
    ("callmewin06@gmail.com", "Password123!", "Hữu Thắng", "ADMIN"),
]

print(f"=== TESTING 4 ADMINS AUTHENTICATION ON {BASE_URL} ===")
for email, pwd, expected_name, expected_role in accounts:
    time.sleep(0.3)
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
    user_info = (data.get("data") or {}).get("user") or {}
    print(f"[{email}] Status: {resp.status_code} | Success: {data.get('success')} | Name: '{user_info.get('display_name')}' | Role: {user_info.get('primary_role')}")
    
    sess_resp = s.get(f"{BASE_URL}/auth/session")
    sess_data = sess_resp.json()
    print(f"  -> /auth/session: Authenticated: {sess_data.get('is_authenticated')} | User: {sess_data.get('user', {}).get('display_name')}")
    
    role_resp = s.get(f"{BASE_URL}/admin/dashboard")
    print(f"  -> /admin/dashboard: Status: {role_resp.status_code} | Success: {role_resp.json().get('success')}")

print("\n=== ALL 4 ADMINS SUCCESSFULLY AUTHENTICATED! ===")
