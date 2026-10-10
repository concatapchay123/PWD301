"""Explicit staging-only storage maintenance. No production-data migration."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def validate_target(database_url: str, confirmed: bool) -> None:
    from scripts.test_database_guard import require_disposable_database

    if not confirmed or not database_url:
        raise RuntimeError("An explicitly confirmed staging database is required.")
    require_disposable_database(database_url)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["inventory", "dry-run", "migrate", "verify", "prune", "reconcile"]
    )
    parser.add_argument("--database-url", default=os.environ.get("STAGING_DATABASE_URL"))
    parser.add_argument("--after-id", type=int, default=0)
    parser.add_argument("--confirm-staging", action="store_true")
    parser.add_argument("--delete-orphans", action="store_true")
    args = parser.parse_args()
    try:
        validate_target(args.database_url, args.confirm_staging)
    except (RuntimeError, ValueError):
        parser.error(
            "Use STAGING_DATABASE_URL targeting confirmed pwd301_test_* and PWD301_TEST_DB_DISPOSABLE=1."
        )
    if (
        args.action not in ("inventory", "dry-run")
        and "staging" not in os.environ.get("S3_BUCKET_NAME", "").lower()
    ):
        parser.error("An isolated bucket with staging in its name is required.")
    from pwd301 import create_app
    from pwd301.services.storage_maintenance_service import maintain_storage, reconcile_storage

    app = create_app(
        "development",
        config_override={
            "SQLALCHEMY_DATABASE_URI": args.database_url,
            "STORAGE_MAINTENANCE_STAGING": True,
        },
    )
    with app.app_context():
        if args.action == "reconcile":
            result = reconcile_storage(delete_orphans=args.delete_orphans)
        else:
            result = maintain_storage(args.action, after_id=args.after_id)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
