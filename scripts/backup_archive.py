"""Create, encrypt, verify and archive a SQL backup using the existing backup service."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from flask import Flask

from pwd301 import create_app
from pwd301.extensions import db
from pwd301.models.identity import User
from pwd301.services.backup_cipher import _key, decrypt_backup
from pwd301.services.backup_archive_service import (
    archive_backup,
    prune_cloud_archives,
    prune_local_archives,
)
from pwd301.services.operations_service import create_database_backup
from pwd301.services.storage_adapter import get_s3_client


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decrypt", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    key = os.environ.get("BACKUP_ENCRYPTION_KEY", "")
    if args.decrypt:
        if args.output is None:
            parser.error("--output is required for authenticated decryption")
        decrypt_backup(args.decrypt, args.output, key)
        return
    # Check prerequisites before creating a physical artifact.
    if not key or not os.environ.get("BACKUP_BUCKET_NAME") or not os.environ.get("ADMIN_EMAIL"):
        raise ValueError(
            "Backup key, private backup bucket and administrator identity are required."
        )
    _key(key)  # Validate key material before creating any physical SQL backup.
    app = create_app("production")
    with app.app_context():
        actor = (
            db.session.query(User)
            .filter_by(email_normalized=os.environ["ADMIN_EMAIL"].lower())
            .one()
        )
        backup = create_database_backup(actor, backup_type="AUTOMATIC")
        backup_app = Flask("private-backup-storage")
        backup_app.config.update(app.config)
        backup_app.config.update(
            STORAGE_BACKEND="s3",
            S3_BUCKET_NAME=os.environ["BACKUP_BUCKET_NAME"],
            S3_ACCESS_KEY_ID=os.environ.get("BACKUP_S3_ACCESS_KEY_ID"),
            S3_SECRET_ACCESS_KEY=os.environ.get("BACKUP_S3_SECRET_ACCESS_KEY"),
        )
        with backup_app.app_context():
            client, _ = get_s3_client()
        if client is None:
            raise ValueError("Private S3 backup client is unavailable.")
        bucket = os.environ["BACKUP_BUCKET_NAME"]
        archive_backup(backup, key, client, bucket)
        # Local metadata/audit must commit before its physical files can be removed.
        local_removed = prune_local_archives(actor, key, client, bucket, db.session)
        cloud_removed = prune_cloud_archives(client, bucket, key)
        print(
            f"Encrypted backup and manifest archived/readback verified; local groups pruned: {local_removed}; cloud groups pruned: {cloud_removed}."
        )
        print("Restore drill is a separate gate. Manual/unarchived diagnostics are retained.")


if __name__ == "__main__":
    run()
