"""Deep verification script testing live container authentication and real hardware telemetry."""

import json
import re
import sys
import requests

sys.stdout.reconfigure(encoding="utf-8")

s = requests.Session()

# 1. Fetch login page
r_login_page = s.get("http://localhost:5000/auth/login")
assert r_login_page.status_code == 200, (
    f"Expected 200 on login page, got {r_login_page.status_code}"
)
csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', r_login_page.text)
csrf_token = csrf_match.group(1) if csrf_match else ""

# 2. Authenticate as System Administrator
r_login = s.post(
    "http://localhost:5000/auth/login",
    data={"email": "admin@pwd301.local", "password": "Password123!", "csrf_token": csrf_token},
    allow_redirects=True,
)
print("Login status:", r_login.status_code, "URL:", r_login.url)
if r_login.status_code != 200:
    print("Login body snippet:", r_login.text[:500])
assert "/admin" in r_login.url or r_login.status_code == 200, (
    f"Expected redirect to admin, got {r_login.url}"
)


# 3. GET /admin/telemetry
r_telem = s.get("http://localhost:5000/admin/telemetry")
print("GET /admin/telemetry status:", r_telem.status_code)
assert r_telem.status_code == 200
telem_data = r_telem.json()
print("Telemetry JSON:")
print(json.dumps(telem_data, indent=2, ensure_ascii=False))

# Assert real hardware telemetry structure
assert telem_data["status"] == "HEALTHY"
assert "Docker" in telem_data["node_label"]
assert telem_data["cpu"]["cores"] >= 1
assert len(telem_data["cpu"]["model"]) > 0
assert (
    "Intel" in telem_data["cpu"]["model"]
    or "AMD" in telem_data["cpu"]["model"]
    or "vCPU" in telem_data["cpu"]["model"]
)
assert telem_data["memory"]["total_gb"] > 0
assert telem_data["disk"]["total_gb"] > 0
assert telem_data["network"]["bytes_sent"] >= 0
assert len(telem_data["uptime"]) > 0

# 4. GET /admin/dashboard
r_dash = s.get("http://localhost:5000/admin/dashboard")
print("GET /admin/dashboard status:", r_dash.status_code)
assert r_dash.status_code == 200
html = r_dash.text

# Check rendered HTML
assert (
    "Trung tâm Điều hành & Quản trị Hệ thống" in html
    or "Trung tâm Điều hành &amp; Quản trị Hệ thống" in html
)
assert "Vi xử lý CPU" in html
assert "Bộ nhớ RAM" in html
assert "Lưu trữ Ổ đĩa" in html
assert "Lưu lượng Mạng" in html

patterns = [
    r'id="telem-node-label">([^<]+)<',
    r'id="telem-hostname">([^<]+)<',
    r'id="telem-cpu-cores">([^<]+)<',
    r'id="telem-cpu-percent">([^<]+)<',
    r'id="telem-ram-label">([^<]+)<',
    r'id="telem-disk-label">([^<]+)<',
    r'id="telem-net-total">([^<]+)<',
]

for pat in patterns:
    m = re.search(pat, html)
    assert m, f"Pattern {pat} not found in HTML"
    print(f"  Rendered DOM element {pat} ==> {m.group(1).strip()}")

print("\nALL LIVE CONTAINER VERIFICATIONS PASSED!")
