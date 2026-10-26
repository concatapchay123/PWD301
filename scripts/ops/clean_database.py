"""Standalone Production Database and Storage Cleaning Tool for PWD301.

Usage:
    python scripts/clean_database.py [--no-keep-baseline] [--no-clean-storage] [-y]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure src is on sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR))

from backend import create_app
from backend.extensions import db
from backend.services.database_cleanup_service import clean_database


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Hard delete all test data from database and storage for production deployment."
    )
    parser.add_argument(
        "--no-keep-baseline",
        action="store_true",
        help="Leave database completely empty without seeding baseline roles and admin.",
    )
    parser.add_argument(
        "--no-clean-storage",
        action="store_true",
        help="Skip cleaning physical storage files and temporary upload files.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Bypass interactive confirmation prompt.",
    )
    args = parser.parse_args()

    app_env = os.environ.get("APP_ENV", "development")
    app = create_app(app_env)

    with app.app_context():
        db_url = db.engine.url.render_as_string(hide_password=True)
        print("=" * 70)
        print("PWD301 PRODUCTION DATABASE & STORAGE CLEANING UTILITY")
        print("=" * 70)
        print(f"Target Database Engine: {db_url}")
        print(f"Keep Baseline Roles & Admin: {not args.no_keep_baseline}")
        print(f"Clean Storage & Caches: {not args.no_clean_storage}")
        print("-" * 70)

        if not args.yes:
            confirm = input(
                "Are you sure you want to PERMANENTLY hard-delete all test data? (y/N): "
            ).strip().lower()
            if confirm not in ("y", "yes"):
                print("Database cleanup aborted by user.")
                return 1

        print("\n[1/3] Executing database hard cleanup...")
        report = clean_database(
            session=db.session,
            engine=db.engine,
            keep_baseline=not args.no_keep_baseline,
            clean_storage=not args.no_clean_storage,
        )

        print("[2/3] Verification of database cleanup:")
        print(f"  - Target tables scanned: {report['tables_targeted']}")
        print(f"  - Total test records deleted: {report['total_records_deleted']}")
        print(f"  - Identity sequences reseeded: {report['identities_reseeded']}")

        if report.get("deleted_records"):
            print("  - Summary of deleted records per table:")
            for tbl, count in sorted(report["deleted_records"].items(), key=lambda x: -x[1]):
                print(f"      * {tbl}: {count}")

        if report.get("baseline_summary"):
            b = report["baseline_summary"]
            print("\n[3/3] Baseline Initialization:")
            print(f"  - System Roles created: {b['roles_created']}")
            print(f"  - Existing Roles: {b['roles_existing']}")
            print(f"  - Root Admin Account created: {b['admin_created']}")
            print(f"  - Admin Roles assigned: {b['admin_roles_assigned']}")

        if report.get("storage_summary"):
            s = report["storage_summary"]
            print("\nStorage Cleanup Summary:")
            print(f"  - Orphaned Blobs deleted: {s['blobs_deleted']}")
            print(f"  - Sample media deleted: {s['sample_files_deleted']}")
            print(f"  - Quarantine tmp files deleted: {s['quarantine_deleted']}")
            print(f"  - Export files deleted: {s['exports_deleted']}")
            print(f"  - Rate limit cache deleted: {s['rate_limits_deleted']}")
            print(f"  - Dev SQLite databases deleted: {s['sqlite_dbs_deleted']}")
            print(f"  - Total files deleted: {s['total_files_deleted']} ({s['bytes_freed']} bytes freed)")

        print("\n" + "=" * 70)
        print("DATABASE & STORAGE SUCCESSFULLY CLEANED FOR PRODUCTION DEPLOYMENT!")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    sys.exit(main())
