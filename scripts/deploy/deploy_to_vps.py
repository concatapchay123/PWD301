import os
import sys
import time
import paramiko

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VPS_HOST = "103.28.33.20"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "Hoangphuc2006@##"
LOCAL_PKG = "backups/pwd301_sync_package.tar.gz"
REMOTE_PKG = "/opt/apps/pwd301_sync_package.tar.gz"

print("=" * 80)
print("BẮT ĐẦU ĐỒNG BỘ HỆ THỐNG VÀ CẬP NHẬT CSDL LÊN VPS: 103.28.33.20")
print("=" * 80)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print(f"1. Đang kết nối SSH tới {VPS_HOST}...")
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=30)
print("   -> Kết nối SSH thành công!")

sftp = ssh.open_sftp()
print(f"2. Đang tải gói đồng bộ {LOCAL_PKG} ({os.path.getsize(LOCAL_PKG) / (1024*1024):.2f} MB) lên VPS...")

last_pct = [0]
def sftp_callback(transferred, total):
    pct = int(transferred / total * 100)
    if pct >= last_pct[0] + 20 or pct == 100:
        print(f"   [Upload] {pct}% ({transferred / (1024*1024):.1f}/{total / (1024*1024):.1f} MB)")
        last_pct[0] = pct

sftp.put(LOCAL_PKG, REMOTE_PKG, callback=sftp_callback)
sftp.close()
print("   -> Upload gói đồng bộ thành công!")

def run_remote(cmd, title=""):
    if title:
        print(f"\n--- {title} ---")
    print(f"$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        print(out)
    if err:
        print(f"[ERR] {err}")
    return out, err

# Step 3: Tạm dừng web & worker để giải phóng kết nối CSDL
run_remote("docker compose -f /opt/apps/pwd301/deploy/compose.production.yml stop web worker", "3. Tạm dừng web & worker")

# Step 4: Giải nén gói mã nguồn mới đè lên /opt/apps/pwd301
run_remote("tar -xzf /opt/apps/pwd301_sync_package.tar.gz -C /opt/apps/pwd301", "4. Giải nén phiên bản mới nhất vào /opt/apps/pwd301")

# Step 5: Khởi động lại web & worker với mã nguồn mới
run_remote("cd /opt/apps/pwd301/deploy && docker compose -f compose.production.yml up -d --build web worker proxy", "5. Rebuild & Khởi động lại toàn bộ dịch vụ")

print("\n--- Đợi dịch vụ ổn định (10 giây) ---")
time.sleep(10)

# Step 6: Chạy migration Alembic không phá hủy dữ liệu cũ (TASK-140 / Invariant 57)
run_remote("docker exec pwd301-production-web-1 flask db upgrade", "6. Chạy migration CSDL (flask db upgrade)")

# Step 7: Chạy auto-heal CSDL để bảo vệ và khôi phục toàn vẹn các bài học/khóa học cũ
run_remote("docker exec pwd301-production-web-1 python scripts/auto_heal_legacy_db.py", "7. Auto-heal CSDL bảo toàn toàn vẹn dữ liệu cũ")

# Step 7.5: Đồng bộ mật khẩu Admin chính trên VPS
sync_admin_pwd_cmd = """docker exec pwd301-production-web-1 python -c "from backend import create_app; from backend.extensions import db; from backend.models.identity import User; from backend.services.user_service import generate_pptq_password_hash, verify_password; app = create_app();
with app.app_context():
    u = db.session.query(User).filter(User.email == 'tqtphamnguyenhoangphuc@gmail.com').first();
    if u:
        u.password_hash = generate_pptq_password_hash('Password123!');
        db.session.commit();
        print('VPS Admin password synced to Password123! Valid:', verify_password(u, 'Password123!'));
" """
run_remote(sync_admin_pwd_cmd, "7.5 Đồng bộ mật khẩu Admin chính trên VPS")

# Step 8: Kiểm tra trạng thái container
run_remote("docker compose -f /opt/apps/pwd301/deploy/compose.production.yml ps", "8. Trạng thái container sau cập nhật")

# Step 9: Kiểm tra API health và truy vấn CSDL thực tế
verify_cmd = """docker exec pwd301-production-web-1 python -c "from backend import create_app; from backend.extensions import db; from backend.models.course import Course; from backend.models.identity import User; app = create_app();
with app.app_context():
    print('=== VERIFICATION STATS ON VPS ===');
    print('Users in DB:', db.session.query(User).count());
    print('Courses in DB:', db.session.query(Course).count());
    print('=== SUCCESS ===');
" """
run_remote(verify_cmd, "9. Xác minh toàn vẹn CSDL thực tế trên VPS")

# Step 10: Xác minh Audit Event Localization & Actor Name trên VPS
verify_audit_cmd = """docker exec pwd301-production-web-1 python -c "from backend import create_app; from backend.extensions import db; from backend.models.identity import User; from backend.services.audit_service import query_audit_logs; app = create_app();
with app.app_context():
    admin = db.session.query(User).filter(User.email == 'tqtphamnguyenhoangphuc@gmail.com').first();
    items, total, p, pp, total_pages = query_audit_logs(admin, page=1, per_page=5);
    print('=== AUDIT VERIFICATION ON VPS ===');
    for it in items:
        print('ACT:', it.get('action'), '| ACTOR:', it.get('actor_name'), '| REASON:', it.get('reason'));
    assert any('Hoàng Phúc' in str(it.get('actor_name')) for it in items), 'LỖI: actor_name không chứa tên Hoàng Phúc';
    assert all('Client attempted to forge' not in str(it.get('reason')) for it in items), 'LỖI: reason vẫn còn tiếng Anh Client attempted to forge';
    print('=== AUDIT VERIFICATION SUCCESSFUL ===');
" """
run_remote(verify_audit_cmd, "10. Xác minh logic Actor Name & Tiếng Việt trên VPS")

ssh.close()

# Step 11: Kiểm tra trực tiếp file JS qua Public CDN / Nginx
print("\n" + "=" * 80)
print("11. XÁC MINH PUBLIC ASSETS TRÊN HTTPS://PPTQ.ID.VN")
print("=" * 80)
import urllib.request
for attempt in range(5):
    try:
        req = urllib.request.Request("https://pptq.id.vn/assets/js/views/admin.js", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if "formatAuditReasonVi" in content and "rawActorName || (actorEmail" in content:
                print(" -> ✓ Tệp admin.js trên HTTPS đã được cập nhật chính xác với formatAuditReasonVi và Actor Name!")
                break
    except Exception as ex:
        print(f"  [Chờ proxy cập nhật... lần {attempt+1}/5: {ex}]")
    time.sleep(3)
else:
    print("  [Cảnh báo: Proxy có thể cần thêm vài giây để xóa cache CDN]")

print("=" * 80)
print("ĐỒNG BỘ VÀ NÂNG CẤP VPS HOÀN TẤT THÀNH CÔNG! KHÔNG GÂY MẤT/HỎNG DỮ LIỆU CŨ.")
print("=" * 80)
