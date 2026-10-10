"""Read-only deployment prerequisites, with secret presence only in output."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
from pathlib import Path

import psutil

if __package__:
    from .deployment_urls import validate_database_targets
else:
    from deployment_urls import validate_database_targets


def inspect_target(root: Path) -> dict[str, object]:
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage(root)
    required = (
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "DATABASE_URL",
        "MIGRATION_DATABASE_URL",
        "DB_PASSWORD",
        "APP_DB_PASSWORD",
        "MIGRATION_DB_PASSWORD",
        "ADMIN_EMAIL",
        "ADMIN_PASSWORD",
        "PWD301_DOMAIN",
        "S3_ENDPOINT_URL",
        "S3_REGION_NAME",
        "S3_BUCKET_NAME",
        "S3_ACCESS_KEY_ID",
        "S3_SECRET_ACCESS_KEY",
        "YOUTUBE_API_KEY",
        "BACKUP_BUCKET_NAME",
        "BACKUP_ENCRYPTION_KEY",
        "BACKUP_S3_ACCESS_KEY_ID",
        "BACKUP_S3_SECRET_ACCESS_KEY",
    )
    checks = {
        "linux_x64": platform.system() == "Linux" and platform.machine() in {"x86_64", "amd64"},
        "ram_8gib": memory.total >= 8_000_000_000,
        "two_cpu": (os.cpu_count() or 0) >= 2,
        "disk_40gb": disk.total >= 40_000_000_000,
        "free_disk_10gb": disk.free >= 10_000_000_000,
        "docker_available": shutil.which("docker") is not None,
        "storage_private_backend": os.environ.get("STORAGE_BACKEND") == "s3",
        "distinct_credentials": len(
            {os.environ.get(n) for n in ("DB_PASSWORD", "APP_DB_PASSWORD", "MIGRATION_DB_PASSWORD")}
        )
        == 3,
    }
    missing = [name for name in required if not os.environ.get(name)]
    try:
        validate_database_targets(os.environ)
        checks["database_targets_match"] = True
    except ValueError:
        checks["database_targets_match"] = False
    return {
        "ready": all(checks.values()) and not missing,
        "checks": checks,
        "missing_settings": missing,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv

        load_dotenv(args.env_file, override=False)
    result = inspect_target(args.root)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()
