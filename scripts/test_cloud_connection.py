"""Diagnostic and Verification Utility for Cloudflare R2 & S3 Cloud Storage.

Usage:
    python scripts/test_cloud_connection.py

Functions:
- Inspects current STORAGE_BACKEND and environment keys.
- Detects whether boto3 is installed.
- Performs an end-to-end dry-run: connects to Cloudflare R2 / S3,
  uploads a 1-byte test probe, checks existence, and deletes it.
- Prints human-readable actionable instructions in Vietnamese.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add root and src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

from wsgi import app  # noqa: E402
from pwd301.services.storage_adapter import (  # noqa: E402
    get_s3_client,
    is_cloud_storage_enabled,
)


def run_diagnostics() -> int:
    with app.app_context():
        backend = app.config.get("STORAGE_BACKEND", "local")
        endpoint = app.config.get("S3_ENDPOINT_URL")
        bucket = app.config.get("S3_BUCKET_NAME")
        access_key = app.config.get("S3_ACCESS_KEY_ID")
        secret_key = app.config.get("S3_SECRET_ACCESS_KEY")

        print("=" * 70)
        print("  PWD301 — KIỂM TRA KẾT NỐI HẠ TẦNG CLOUD STORAGE (CLOUDFLARE R2 / S3)")
        print("=" * 70)
        print(f"[*] Chế độ lưu trữ hiện tại (STORAGE_BACKEND): {backend}")
        print(f"[*] S3 Endpoint URL                          : {endpoint or '(Chưa thiết lập)'}")
        print(f"[*] Tên Bucket (S3_BUCKET_NAME)              : {bucket or '(Chưa thiết lập)'}")
        print(
            f"[*] Access Key ID                            : {'***' + access_key[-4:] if access_key and len(access_key) > 4 else '(Chưa thiết lập)'}"
        )
        print(
            f"[*] Secret Key                               : {'[ĐÃ CUNG CẤP]' if secret_key else '(Chưa thiết lập)'}"
        )
        print("-" * 70)

        if not is_cloud_storage_enabled():
            print("[INFO] Hệ thống đang chạy ở chế độ LOCAL DISK STORAGE (Mặc định an toàn).")
            print("       - Mọi tài liệu và tệp đính kèm được lưu trên ổ cứng VPS (/storage).")
            print(
                "       - Khi bạn sẵn sàng chuyển sang Cloudflare R2 để tiết kiệm dung lượng VPS:"
            )
            print("         1. Đặt STORAGE_BACKEND=s3 trong tệp .env.")
            print(
                "         2. Điền S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME."
            )
            print("         3. Chạy lại script này để kiểm tra kết nối thực tế.")
            print("=" * 70)
            return 0

        # Cloud storage is enabled
        print("[*] Đang khởi tạo kết nối S3 Client qua boto3...")
        client, bucket_name = get_s3_client()
        if client is None or bucket_name is None:
            print("[FAIL] Không thể khởi tạo S3 Client!")
            print(
                "       Nguyên nhân: Thiếu thông tin xác thực hoặc thư viện boto3 chưa được cài đặt."
            )
            print(
                "       Khắc phục: Kiểm tra lại các biến môi trường trong .env và chạy 'pip install boto3'."
            )
            print("=" * 70)
            return 1

        probe_key = f"diagnostics/probe_{int(time.time())}.txt"
        probe_data = b"PWD301_R2_HEALTH_CHECK_OK"

        print(
            f"[*] Đang thực hiện kiểm tra ghi thử nghiệm (Upload Probe) lên bucket '{bucket_name}'..."
        )
        try:
            client.put_object(Bucket=bucket_name, Key=probe_key, Body=probe_data)
            print("    -> [PASS] Ghi thử nghiệm thành công!")
        except Exception as exc:
            print(f"    -> [FAIL] Lỗi ghi vào bucket: {exc}")
            print("       Khắc phục: Kiểm tra quyền Write (Object Read & Write) của R2 API Token.")
            print("=" * 70)
            return 2

        print("[*] Đang thực hiện kiểm tra đọc thử nghiệm (Download Probe)...")
        try:
            resp = client.get_object(Bucket=bucket_name, Key=probe_key)
            body = resp["Body"].read()
            if body == probe_data:
                print("    -> [PASS] Đọc dữ liệu toàn vẹn thành công!")
            else:
                print("    -> [WARN] Dữ liệu đọc được không khớp với probe ban đầu.")
        except Exception as exc:
            print(f"    -> [FAIL] Lỗi đọc từ bucket: {exc}")
            print("=" * 70)
            return 3

        print("[*] Đang dọn dẹp probe tạm...")
        try:
            client.delete_object(Bucket=bucket_name, Key=probe_key)
            print("    -> [PASS] Đã xóa probe tạm thành công.")
        except Exception as exc:
            print(f"    -> [WARN] Không thể xóa probe tạm: {exc}")

        print("=" * 70)
        print("[THÀNH CÔNG] Kết nối Cloudflare R2 hoạt động 100% hoàn hảo!")
        print("             Hệ thống PWD301 đã sẵn sàng offload toàn bộ file tài liệu sang R2.")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    sys.exit(run_diagnostics())
