"""Test script to verify HTTP login for all 4 admin accounts."""
import sys
import requests

accounts = [
    ("vinhphu2020.nt@gmail.com", "Vĩnh Phú"),
    ("danglyquan@gmail.com", "Đặng Lý Quân"),
    ("tqtphamnguyenhoangphuc@gmail.com", "Hoàng Phúc"),
    ("callmewin06@gmail.com", "Hữu Thắng"),
]

print("=== KIỂM THỬ ĐĂNG NHẬP 4 TÀI KHOẢN ADMIN ===")
all_passed = True

for email, expected_name in accounts:
    s = requests.Session()
    r = s.get("http://localhost:5000/auth/login")
    csrf = r.cookies.get("csrf_token")
    payload = {"email": email, "password": "Password123!"}
    
    resp = s.post(
        "http://localhost:5000/auth/login",
        json=payload,
        headers={"X-CSRFToken": csrf},
    )
    data = resp.json()

    success = data.get("success")
    user_data = data.get("data", {}).get("user") or {}
    print(
        f"[{email}] Success: {success} | Name: '{user_data.get('display_name')}' "
        f"| Role: {user_data.get('primary_role')} | Sub-role: {user_data.get('admin_sub_role')} "
        f"| is_primary_admin: {user_data.get('is_primary_admin')}"
    )

    if not (
        success is True
        and user_data.get("display_name") == expected_name
        and user_data.get("primary_role") == "ADMIN"
        and user_data.get("admin_sub_role") == "ADMIN_PRIMARY"
        and user_data.get("is_primary_admin") is True
        and set(user_data.get("role_codes", [])) == {"ADMIN", "INSTRUCTOR", "STUDENT"}
    ):
        print(f"FAILED for {email}: {data}")
        all_passed = False

if all_passed:
    print("\n>>> TẤT CẢ 4 TÀI KHOẢN ĐĂNG NHẬP THÀNH CÔNG VỚI QUYỀN ADMIN_PRIMARY! <<<")
else:
    sys.exit(1)
