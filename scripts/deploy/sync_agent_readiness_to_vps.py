# -*- coding: utf-8 -*-
"""Synchronize Agent Readiness fixes to VPS server (103.28.33.20) and verify live public endpoints."""

import os
import sys
import time
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
REMOTE_BASE = "/opt/apps/pwd301"

FRONTEND_FILES = [
    "index.html",
    "about.html",
    "contact.html",
    "privacy.html",
    "llms.txt",
    "llms-full.txt",
    "sitemap.xml",
    "robots.txt",
]


def sync_to_vps():
    print("=" * 80)
    print(f"BẮT ĐẦU ĐỒNG BỘ AGENT READINESS LÊN VPS: {VPS_HOST}")
    print("=" * 80)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"1. Kết nối SSH tới {VPS_HOST}...")
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=20)
    print("   -> Kết nối SSH thành công!")

    sftp = ssh.open_sftp()

    # 1. Upload Frontend Files
    print("\n2. Tải các tệp tin Frontend mới lên /opt/apps/pwd301/frontend/...")
    local_frontend = Path("source_code/frontend")
    for fname in FRONTEND_FILES:
        local_path = local_frontend / fname
        remote_path = f"{REMOTE_BASE}/frontend/{fname}"
        if local_path.is_file():
            size = local_path.stat().st_size
            sftp.put(str(local_path), remote_path)
            print(f"   ✓ {fname} -> {remote_path} ({size:,} bytes)")
        else:
            print(f"   ! Cảnh báo: không tìm thấy {local_path}")

    # 2. Upload Backend Routes (adjusted for pwd301 package on VPS)
    print("\n3. Chuẩn bị và đồng bộ routes.py cho gói pwd301...")
    with open("source_code/backend/blueprints/frontend/routes.py", "r", encoding="utf-8") as f:
        routes_content = f.read()

    # Adapt imports for VPS pwd301 module structure
    vps_routes_content = (
        routes_content.replace("import backend\nfrom backend.blueprints.frontend import frontend_bp",
                              "import pwd301\nfrom pwd301.blueprints.frontend import frontend_bp")
                      .replace("backend.__version__", "pwd301.__version__")
    )

    temp_routes = Path("backups/routes_vps_temp.py")
    temp_routes.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_routes, "w", encoding="utf-8", newline="\n") as f:
        f.write(vps_routes_content)

    remote_routes = f"{REMOTE_BASE}/src/pwd301/blueprints/frontend/routes.py"
    sftp.put(str(temp_routes), remote_routes)
    print(f"   ✓ routes.py đồng bộ thành công -> {remote_routes}")

    # 3. Update __init__.py on VPS with Markdown 404 handler
    print("\n4. Đồng bộ 404 Markdown negotiation trong __init__.py...")
    with open("source_code/backend/__init__.py", "r", encoding="utf-8") as f:
        init_content = f.read()

    # In case there are backend references in __init__.py
    vps_init_content = (
        init_content.replace("from backend", "from pwd301")
                    .replace("import backend", "import pwd301")
    )
    temp_init = Path("backups/init_vps_temp.py")
    with open(temp_init, "w", encoding="utf-8", newline="\n") as f:
        f.write(vps_init_content)

    remote_init = f"{REMOTE_BASE}/src/pwd301/__init__.py"
    sftp.put(str(temp_init), remote_init)
    print(f"   ✓ __init__.py đồng bộ thành công -> {remote_init}")

    sftp.close()

    # 4. Restart containers
    print("\n5. Khởi động lại web và proxy containers...")
    stdin, stdout, stderr = ssh.exec_command("docker restart pwd301-production-web-1 pwd301-production-proxy-1")
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(f"   Containers restarted: {out}")
    if err:
        print(f"   [ERR] {err}")

    print("   -> Đợi Gunicorn và Caddy khởi động ổn định (7 giây)...")
    time.sleep(7)

    # 5. Check container health
    stdin, stdout, stderr = ssh.exec_command("docker compose -f /opt/apps/pwd301/deploy/compose.production.yml ps")
    print("\n6. Trạng thái containers trên VPS:")
    print(stdout.read().decode().strip())

    ssh.close()

    # 6. Verify live public endpoints
    print("\n" + "=" * 80)
    print("7. XÁC MINH TRỰC TIẾP PUBLIC ENDPOINTS TRÊN HTTPS://PPTQ.ID.VN")
    print("=" * 80)

    session = requests.Session()

    # Test 1: Homepage Markdown negotiation
    r_md = session.get("https://pptq.id.vn/", headers={"Accept": "text/markdown"}, timeout=15)
    print(f"\n[Test 1] GET / (Accept: text/markdown)")
    print(f"  Status: {r_md.status_code}")
    print(f"  Content-Type: {r_md.headers.get('Content-Type')}")
    print(f"  Vary: {r_md.headers.get('Vary')}")
    print(f"  Body length: {len(r_md.text)} chars")
    assert r_md.status_code == 200, f"Expected 200, got {r_md.status_code}"
    assert "text/markdown" in r_md.headers.get("Content-Type", ""), "Expected text/markdown"
    assert "Accept" in r_md.headers.get("Vary", ""), "Expected Vary to contain Accept"
    assert "# PPTQ LMS" in r_md.text, "Body must contain '# PPTQ LMS'"
    print("  -> ✓ THÀNH CÔNG: Trang chủ đã phản hồi Markdown chuẩn xác với Vary: Accept!")

    # Test 2: Homepage HTML negotiation
    r_html = session.get("https://pptq.id.vn/", headers={"Accept": "text/html"}, timeout=15)
    print(f"\n[Test 2] GET / (Accept: text/html)")
    print(f"  Status: {r_html.status_code}")
    print(f"  Content-Type: {r_html.headers.get('Content-Type')}")
    print(f"  Vary: {r_html.headers.get('Vary')}")
    assert r_html.status_code == 200
    assert "text/html" in r_html.headers.get("Content-Type", "")
    assert "Accept" in r_html.headers.get("Vary", "")
    assert "PPTQ LMS - Nền Tảng Học Trực Tuyến" in r_html.text
    assert 'application/ld+json' in r_html.text
    print("  -> ✓ THÀNH CÔNG: Trang chủ trả về HTML đầy đủ H1, JSON-LD và Vary: Accept!")

    # Test 3: Agent-friendly 404 Markdown
    probe_url = "https://pptq.id.vn/__ora-404-probe-gr9m15ae"
    r_404 = session.get(probe_url, headers={"Accept": "text/markdown"}, timeout=15)
    print(f"\n[Test 3] GET {probe_url} (Accept: text/markdown)")
    print(f"  Status: {r_404.status_code}")
    print(f"  Content-Type: {r_404.headers.get('Content-Type')}")
    print(f"  Vary: {r_404.headers.get('Vary')}")
    print(f"  Body preview:\n{r_404.text[:200]}...")
    assert r_404.status_code == 404, f"Expected 404, got {r_404.status_code}"
    assert "text/markdown" in r_404.headers.get("Content-Type", ""), "Expected text/markdown"
    assert "Accept" in r_404.headers.get("Vary", ""), "Expected Vary to contain Accept"
    assert "/llms.txt" in r_404.text or "llms.txt" in r_404.text
    print("  -> ✓ THÀNH CÔNG: 404 trả về đúng mã HTTP 404 và thân Markdown hướng dẫn!")

    # Test 4: llms.txt
    r_llms = session.get("https://pptq.id.vn/llms.txt", timeout=15)
    print(f"\n[Test 4] GET /llms.txt")
    print(f"  Status: {r_llms.status_code}")
    print(f"  Content-Type: {r_llms.headers.get('Content-Type')}")
    assert r_llms.status_code == 200
    assert "When to Use This" in r_llms.text
    print("  -> ✓ THÀNH CÔNG: /llms.txt phục vụ chỉ dẫn Agent rõ ràng với mục 'When to Use This'!")

    # Test 5: sitemap.xml
    r_sitemap = session.get("https://pptq.id.vn/sitemap.xml", timeout=15)
    print(f"\n[Test 5] GET /sitemap.xml")
    print(f"  Status: {r_sitemap.status_code}")
    print(f"  Content-Type: {r_sitemap.headers.get('Content-Type')}")
    assert r_sitemap.status_code == 200
    assert "https://pptq.id.vn/about" in r_sitemap.text
    print("  -> ✓ THÀNH CÔNG: /sitemap.xml hợp lệ liệt kê đầy đủ các trang tin cậy!")

    # Test 6: Trust Anchor Pages
    print("\n[Test 6] Trust Anchor Pages (/about, /contact, /privacy)")
    for p in ["/about", "/contact", "/privacy"]:
        rp = session.get(f"https://pptq.id.vn{p}", headers={"Accept": "text/html"}, timeout=15)
        rp_md = session.get(f"https://pptq.id.vn{p}", headers={"Accept": "text/markdown"}, timeout=15)
        print(f"  - {p}: HTML Status {rp.status_code} ({len(rp.text)} chars), MD Status {rp_md.status_code} ({len(rp_md.text)} chars)")
        assert rp.status_code == 200 and len(rp.text) >= 500
        assert rp_md.status_code == 200 and len(rp_md.text) >= 500

    print("  -> ✓ THÀNH CÔNG: Toàn bộ 3 trang tin cậy đã hoạt động hoàn hảo trên server production!")

    print("\n" + "=" * 80)
    print("HOÀN TẤT ĐỒNG BỘ VÀ XÁC MINH 100% TRÊN MÁY CHỦ VPS PPTQ.ID.VN!")
    print("=" * 80)


if __name__ == "__main__":
    sync_to_vps()
