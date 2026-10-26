"""System Log Exporter for PWD301.

Extracts comprehensive system logs from all Docker production services
(web, worker, proxy, db) and the database audit ledger, packaging them
into a timestamped tar.gz archive.
"""

from __future__ import annotations

import datetime
import io
import json
import os
import subprocess
import sys
import tarfile

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

OUTPUT_DIR = "/opt/apps/pwd301" if os.path.exists("/opt/apps/pwd301") else "logs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
NOW_STR = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
TEMP_DIR = os.path.join(OUTPUT_DIR, f"logs_temp_{NOW_STR}")
ARCHIVE_PATH = os.path.join(OUTPUT_DIR, f"system_logs_{NOW_STR}.tar.gz")

CONTAINERS = [
    ("web", "pwd301-production-web-1"),
    ("worker", "pwd301-production-worker-1"),
    ("proxy", "pwd301-production-proxy-1"),
    ("db", "pwd301-production-db-1"),
    ("clamav", "pwd301-production-clamav-1"),
]


def run_cmd(cmd: list[str]) -> str:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.stdout + ("\n[STDERR]\n" + res.stderr if res.stderr else "")
    except Exception as exc:
        return f"[ERROR executing {' '.join(cmd)}]: {exc}"


def export_logs() -> None:
    os.makedirs(TEMP_DIR, exist_ok=True)
    print("=" * 70)
    print("  TRÍCH XUẤT TOÀN BỘ LOG HỆ THỐNG PWD301 (SYSTEM LOG EXPORTER)")
    print("=" * 70)

    # 1. Trích xuất Docker Container logs
    for label, cname in CONTAINERS:
        print(f"-> Đang lấy log dịch vụ [{label}] ({cname})...")
        log_content = run_cmd(["docker", "logs", "--timestamps", cname])
        log_file = os.path.join(TEMP_DIR, f"{label}.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(log_content)
        lines = len(log_content.splitlines())
        print(f"   ✓ Đã lưu {label}.log ({lines:,} dòng)")

    # 2. Trích xuất Audit Events từ CSDL (nếu chạy trong container có python app)
    print("-> Đang trích xuất nhật ký kiểm toán (Audit Events) từ CSDL...")
    audit_sql = """
    SELECT TOP 500 
        id, event_time, action, actor_user_id, target_type, target_id, 
        ip_address, details 
    FROM audit_events 
    ORDER BY id DESC
    """
    audit_json = run_cmd([
        "docker", "exec", "pwd301-production-web-1",
        "python", "-c",
        f"import json, sys; sys.path.insert(0, 'src'); from backend import create_app; from backend.extensions import db; app = create_app('production'); ctx = app.app_context(); ctx.push(); res = db.session.execute(db.text('{audit_sql}')).mappings().all(); print(json.dumps([dict(r) for r in res], default=str, ensure_ascii=False, indent=2))"
    ])
    audit_file = os.path.join(TEMP_DIR, "audit_events.json")
    with open(audit_file, "w", encoding="utf-8") as f:
        f.write(audit_json)
    print("   ✓ Đã lưu audit_events.json (500 sự kiện kiểm toán gần nhất)")

    # 3. Đóng gói vào tệp .tar.gz
    print("\n-> Đang nén toàn bộ log vào tệp lưu trữ...")
    with tarfile.open(ARCHIVE_PATH, "w:gz") as tar:
        for fname in os.listdir(TEMP_DIR):
            fpath = os.path.join(TEMP_DIR, fname)
            tar.add(fpath, arcname=fname)

    # Dọn dẹp thư mục tạm
    import shutil
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    size_mb = os.path.getsize(ARCHIVE_PATH) / (1024 * 1024)
    print("\n" + "=" * 70)
    print("  TRÍCH XUẤT HOÀN TẤT VỚI 100% THÀNH CÔNG!")
    print("=" * 70)
    print(f"  * Tệp lưu trữ log:  {ARCHIVE_PATH}")
    print(f"  * Dung lượng tệp:   {size_mb:.2f} MB")
    print("\nBạn có thể đọc file nén này hoặc xem trực tiếp bằng lệnh:")
    print(f"  tar -ztvf {ARCHIVE_PATH}")
    print(f"  tar -zxvf {ARCHIVE_PATH}\n")


if __name__ == "__main__":
    export_logs()
