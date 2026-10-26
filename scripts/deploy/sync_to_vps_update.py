# -*- coding: utf-8 -*-
"""Synchronize latest bugfix to VPS server and preserve existing courses."""

import os
import sys
import time
import tarfile
from pathlib import Path
import paramiko
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VPS_HOST = "103.28.33.20"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "Hoangphuc2006@##"
LOCAL_PKG = Path("backups/pwd301_sync_package.tar.gz")
REMOTE_PKG = "/opt/apps/pwd301_sync_package.tar.gz"


def build_package():
    print("=" * 80)
    print("1. ĐÓNG GÓI BẢN VÁ LỖI MÔ TẢ KHÓA HỌC")
    print("=" * 80)

    INCLUDE_DIRS = [
        "src",
        "frontend",
        "migrations",
        "deploy",
        "scripts",
    ]

    INCLUDE_FILES = [
        "requirements.txt",
        "AGENTS.md",
        "Dockerfile",
        "wsgi.py",
        "pyproject.toml",
    ]

    def filter_tar(tarinfo):
        name = tarinfo.name
        for pat in [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".git",
            "*.pyc",
            "course_data",
            "android_course_data",
            "qa-evidence",
            "qa-task",
            "screenshots",
        ]:
            if pat in name:
                return None
        return tarinfo

    LOCAL_PKG.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(LOCAL_PKG, "w:gz") as tar:
        for d in INCLUDE_DIRS:
            dp = Path(d)
            if dp.exists():
                print(f"  + Thư mục: {d}")
                tar.add(d, filter=filter_tar)
        for f in INCLUDE_FILES:
            fp = Path(f)
            if fp.exists():
                print(f"  + Tệp tin: {f}")
                tar.add(f)

    pkg_size_mb = LOCAL_PKG.stat().st_size / (1024 * 1024)
    print(f"-> Gói đồng bộ hoàn tất: {LOCAL_PKG} ({pkg_size_mb:.2f} MB)")
    return pkg_size_mb


def sync_to_vps():
    build_package()

    print("\n" + "=" * 80)
    print(f"2. KẾT NỐI VÀ UPLOAD LÊN VPS ({VPS_HOST})")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=30)
    print(f"✓ Kết nối SSH thành công tới {VPS_HOST}")

    sftp = ssh.open_sftp()
    print("-> Đang tải gói cập nhật lên VPS...")
    last_pct = [0]
    def sftp_cb(transferred, total):
        pct = int(transferred / total * 100)
        if pct >= last_pct[0] + 25 or pct == 100:
            print(f"   [SFTP] {pct}% ({transferred / (1024*1024):.1f}/{total / (1024*1024):.1f} MB)")
            last_pct[0] = pct

    sftp.put(str(LOCAL_PKG), REMOTE_PKG, callback=sftp_cb)
    sftp.close()
    print("✓ Upload hoàn tất!")

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

    # Step 3: Tạm dừng web & worker
    run_remote("docker compose -f /opt/apps/pwd301/deploy/compose.production.yml stop web worker", "3. Tạm dừng web & worker")

    # Step 4: Giải nén mã nguồn mới nhất đè lên /opt/apps/pwd301
    run_remote("tar -xzf /opt/apps/pwd301_sync_package.tar.gz -C /opt/apps/pwd301", "4. Giải nén mã nguồn mới nhất")

    # Step 5: Khởi động lại dịch vụ
    run_remote("cd /opt/apps/pwd301/deploy && docker compose -f compose.production.yml up -d web worker proxy", "5. Khởi động lại dịch vụ web, worker, proxy")

    print("\n--- Đợi dịch vụ ổn định (10 giây) ---")
    time.sleep(10)

    # Step 6: Kiểm tra trạng thái containers
    run_remote("docker compose -f /opt/apps/pwd301/deploy/compose.production.yml ps", "6. Trạng thái containers")

    ssh.close()

    # Step 7: Kiểm tra xác minh kết quả trực tiếp qua HTTP Public API (với retry chờ Gunicorn khởi động)
    print("\n" + "=" * 80)
    print("7. XÁC MINH PUBLIC API VÀ MÔ TẢ KHÓA HỌC TRÊN PRODUCTION")
    print("=" * 80)

    resp = None
    for attempt in range(6):
        try:
            resp = requests.get("https://pptq.id.vn/api/courses", timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                break
        except Exception:
            pass
        print(f"  [Chờ backend khởi động... lần {attempt+1}/6]")
        time.sleep(3)

    data = resp.json()
    items = (data.get("data") or {}).get("items") or data.get("items") or []
    print(f"Số lượng khóa học trong Catalog: {len(items)}")
    for item in items:
        print(f"\n[Khóa học: {item.get('course_code')} - {item.get('title')}]")
        print(f" - Mô tả (Description): {repr(item.get('description'))}")
        print(f" - Thông tin liên hệ (Contact Info): {item.get('contact_info')}")
        print(f" - Video trailer: {item.get('trailer_url')}")

        desc = item.get("description") or ""
        assert "<!--" not in desc, f"LỖI: Mô tả khóa học {item.get('title')} vẫn còn chứa comment HTML: {desc}"
        assert "contact_info" not in desc, f"LỖI: Mô tả khóa học {item.get('title')} vẫn còn chứa text contact_info: {desc}"
        print(" -> ✓ MÔ TẢ ĐÃ ĐƯỢC TÁCH BẠCH HOÀN TOÀN SẠCH SẼ!")

    print("\n" + "=" * 80)
    print("8. XÁC MINH TOPBAR DEAD-CENTER & SECURITY TRÊN PRODUCTION")
    print("=" * 80)

    html_resp = requests.get("https://pptq.id.vn/", timeout=15)
    html_text = html_resp.text
    assert "@media (max-width: 1849px)" in html_text, "LỖI: index.html trên server chưa có media query 1849px"
    assert "absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2" in html_text, "LỖI: index.html trên server chưa có dead-center absolute"
    assert "topbar-admin-tier3" in html_text, "LỖI: index.html trên server chưa có topbar-admin-tier3"
    print(" -> ✓ TOPBAR DEAD-CENTER CSS & HTML ĐÃ ĐỒNG BỘ CHÍNH XÁC!")

    js_resp = requests.get("https://pptq.id.vn/assets/js/router.js", timeout=15)
    js_text = js_resp.text
    assert "CẢNH BÁO AN NINH: Phím tắt F12" in js_text, "LỖI: router.js trên server chưa có cảnh báo F12"
    assert "checkDevToolsActive" in js_text, "LỖI: router.js trên server chưa có checkDevToolsActive"
    assert "🛡" not in js_text, "LỖI: router.js trên server vẫn còn emoji khiên 🛡"
    print(" -> ✓ DEVTOOLS & F12 SECURITY SHIELD (KHÔNG CÒN KHIÊN) ĐÃ ĐỒNG BỘ CHÍNH XÁC TRONG ROUTER.JS!")

    va_resp = requests.get("https://pptq.id.vn/assets/js/components/video-armor.js", timeout=15)
    va_text = va_resp.text
    assert "🛡" not in va_text, "LỖI: video-armor.js trên server vẫn còn emoji khiên 🛡"
    assert '<span class="material-symbols-outlined text-[36px]">shield</span>' not in va_text, "LỖI: video-armor.js vẫn còn icon shield"
    print(" -> ✓ VIDEO-ARMOR.JS ĐÃ ĐƯỢC LOẠI BỎ TOÀN BỘ ICON KHIÊN THÀNH CÔNG!")

    admin_resp = requests.get("https://pptq.id.vn/assets/js/views/admin.js", timeout=15)
    admin_text = admin_resp.text
    assert "admin-courses-quick-nav" in admin_text, "LỖI: admin.js trên server chưa có admin-courses-quick-nav"
    assert "admin-governance-quick-hub" in admin_text, "LỖI: admin.js trên server chưa có admin-governance-quick-hub"
    assert "quick-jump-courses-btn" in admin_text, "LỖI: admin.js trên server chưa có quick-jump-courses-btn"
    print(" -> ✓ ADMIN.JS MENU TRUY CẬP NHANH & QUICK HUB ĐÃ ĐỒNG BỘ CHÍNH XÁC!")

    print("\n" + "=" * 80)
    print("ĐỒNG BỘ VÀ XÁC MINH BẢN VÁ LỖI HOÀN TẤT THÀNH CÔNG 100%!")
    print("=" * 80)


if __name__ == "__main__":
    sync_to_vps()
