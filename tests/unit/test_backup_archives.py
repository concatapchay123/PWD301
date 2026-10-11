"""Backup archive safety tests with isolated files and an in-memory S3 boundary."""

import base64
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from pwd301.services.backup_cipher import decrypt_backup

KEY = base64.urlsafe_b64encode(b"k" * 32).decode()


class Cloud:
    def __init__(self):
        self.objects = {}
        self.deleted = []
        self.fail_manifest = False

    def upload_file(self, path, bucket, key, ExtraArgs=None):
        if self.fail_manifest and "manifest" in key:
            raise RuntimeError("isolated failure")
        self.objects[key] = (Path(path).read_bytes(), (ExtraArgs or {}).get("Metadata", {}))

    def get_object(self, Bucket, Key):
        data, metadata = self.objects[Key]
        return {"Body": io.BytesIO(data), "ContentLength": len(data), "Metadata": metadata}

    def head_object(self, Bucket, Key):
        data, metadata = self.objects[Key]
        return {"ContentLength": len(data), "Metadata": metadata}

    def get_paginator(self, name):
        return self

    def paginate(self, Bucket, Prefix):
        return [{"Contents": [{"Key": key} for key in self.objects if key.startswith(Prefix)]}]

    def delete_object(self, Bucket, Key):
        self.deleted.append(Key)
        self.objects.pop(Key, None)


def backup(tmp_path, stamp="20261009_010000", suffix="12345678"):
    source = tmp_path / f"pwd301_db_{stamp}_{suffix}.bak"
    source.write_bytes(b"isolated backup data")
    source.with_name(source.name + ".manifest.json").write_text(
        json.dumps(
            {
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "file_size": source.stat().st_size,
                "database_backup_name": source.name,
            }
        )
    )
    return SimpleNamespace(
        storage_location=str(source),
        public_id="backup-public-id",
        started_at=datetime.strptime(stamp, "%Y%m%d_%H%M%S"),
    )


def test_archive_includes_authenticated_encrypted_manifest(tmp_path):
    from pwd301.services.backup_archive_service import archive_backup

    item, cloud = backup(tmp_path), Cloud()
    result = archive_backup(item, KEY, cloud, "private-backup")
    assert len(cloud.objects) == 3
    manifest = next(key for key in cloud.objects if key.endswith(".manifest.json.encrypted"))
    encrypted = tmp_path / "cloud-manifest"
    encrypted.write_bytes(cloud.objects[manifest][0])
    plain = tmp_path / "verified-manifest"
    decrypt_backup(encrypted, plain, KEY)
    assert json.loads(plain.read_text())["database_backup_name"] == Path(item.storage_location).name
    assert result["daily_prefix"].startswith("daily/pwd301_db_")


def test_partial_group_is_never_completed(tmp_path):
    from pwd301.services.backup_archive_service import archive_backup

    item, cloud = backup(tmp_path), Cloud()
    cloud.fail_manifest = True
    with pytest.raises(RuntimeError):
        archive_backup(item, KEY, cloud, "private-backup")
    assert not any(key.endswith("/receipt.json") for key in cloud.objects)
    assert Path(item.storage_location).exists()


def test_cloud_retention_ignores_forged_and_unrelated_groups(tmp_path):
    from pwd301.services.backup_archive_service import archive_backup, prune_cloud_archives

    cloud = Cloud()
    cloud.objects["daily/unrelated/receipt.json"] = (b"{}", {})
    cloud.objects["daily/pwd301_db_20200101_010000_11111111.bak/receipt.json"] = (
        b'{"signature":"forged"}',
        {},
    )
    for day in range(1, 10):
        archive_backup(backup(tmp_path, f"202610{day:02d}_010000"), KEY, cloud, "private-backup")
    result = prune_cloud_archives(cloud, "private-backup", KEY)
    assert result["daily_deleted"] == 2
    assert len(cloud.deleted) == 6
    assert "daily/unrelated/receipt.json" in cloud.objects
    assert all("20200101" not in key for key in cloud.deleted)


def test_production_age_prune_preserves_unarchived_recovery_copy(app, tmp_path):
    from pwd301.extensions import db
    from pwd301.models.operations import BackupRun
    from pwd301.services.operations_service import _prune_expired_backups

    source = Path(app.config["FILE_BACKUP_ROOT"]) / "last-copy.bak"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"unarchived recovery evidence")
    item = BackupRun(
        backup_type="AUTOMATIC",
        status="SUCCEEDED",
        started_at=datetime(2000, 1, 1),
        storage_location=str(source),
    )
    db.session.add(item)
    db.session.commit()
    app.config["ENV"] = "production"
    assert _prune_expired_backups(db.session, 30) == 0
    assert source.exists()
    assert db.session.query(BackupRun).count() == 1


def test_weekly_retention_keeps_four_complete_sunday_groups(tmp_path):
    from datetime import timedelta

    from pwd301.services.backup_archive_service import archive_backup, prune_cloud_archives

    cloud = Cloud()
    for number in range(5):
        day = datetime(2026, 8, 30) + timedelta(weeks=number)
        archive_backup(
            backup(tmp_path, day.strftime("%Y%m%d_010000")), KEY, cloud, "private-backup"
        )
    result = prune_cloud_archives(cloud, "private-backup", KEY)
    assert result == {"daily_deleted": 0, "weekly_deleted": 1}
    assert all(key.startswith("weekly/") for key in cloud.deleted)


from tests import test_m1_file_access as fixtures

setup_roles = fixtures.setup_roles
admin_user = fixtures.admin_user


def _local_archives(app, count=5):
    from pwd301.extensions import db
    from pwd301.models.operations import BackupRun
    from pwd301.services.backup_archive_service import archive_backup

    root = Path(app.config["FILE_BACKUP_ROOT"])
    root.mkdir(parents=True, exist_ok=True)
    cloud, sources = Cloud(), []
    for number in range(1, count + 1):
        stub = backup(root, f"202610{number:02d}_010000")
        row = BackupRun(
            backup_type="AUTOMATIC",
            status="SUCCEEDED",
            started_at=stub.started_at,
            storage_location=stub.storage_location,
            database_backup_name=Path(stub.storage_location).name,
        )
        db.session.add(row)
        db.session.commit()
        archive_backup(row, KEY, cloud, "private-backup")
        sources.append(Path(row.storage_location))
    return cloud, sources


def test_local_retention_commits_audit_and_metadata_before_unlink(app, admin_user):
    from pwd301.extensions import db
    from pwd301.models.notification_audit import AuditEvent
    from pwd301.models.operations import BackupRun
    from pwd301.services.backup_archive_service import prune_local_archives

    cloud, sources = _local_archives(app)
    assert prune_local_archives(admin_user, KEY, cloud, "private-backup", db.session) == 3
    assert db.session.query(BackupRun).count() == 2
    assert all(source.exists() for source in sources[-2:])
    assert all(not source.exists() for source in sources[:3])
    assert (
        db.session.query(AuditEvent).filter_by(action="DATABASE_BACKUP_LOCAL_PRUNED").count() == 3
    )


def test_failed_metadata_commit_preserves_all_local_recovery_bytes(app, admin_user, monkeypatch):
    from pwd301.extensions import db
    from pwd301.services.backup_archive_service import prune_local_archives

    cloud, sources = _local_archives(app)

    def fail_commit():
        raise RuntimeError("isolated commit failure")

    monkeypatch.setattr(db.session, "commit", fail_commit)
    with pytest.raises(RuntimeError):
        prune_local_archives(admin_user, KEY, cloud, "private-backup", db.session)
    assert all(source.exists() for source in sources)


def test_successful_archive_releases_unreferenced_local_ciphertexts(tmp_path):
    from pwd301.services.backup_archive_service import archive_backup

    item, cloud = backup(tmp_path), Cloud()
    archive_backup(item, KEY, cloud, "private-backup")
    source = Path(item.storage_location)
    assert source.exists()
    assert source.with_name(source.name + ".manifest.json").exists()
    assert not source.with_name(source.name + ".encrypted").exists()
    assert not source.with_name(source.name + ".manifest.json.encrypted").exists()


def test_local_prune_preserves_files_referenced_by_another_backup_record(app, admin_user):
    from pwd301.extensions import db
    from pwd301.models.operations import BackupRun
    from pwd301.services.backup_archive_service import prune_local_archives

    cloud, sources = _local_archives(app)
    db.session.add(
        BackupRun(
            backup_type="MANUAL",
            status="SUCCEEDED",
            started_at=datetime(2026, 10, 1),
            storage_location=str(sources[0]),
            database_backup_name=sources[0].name,
        )
    )
    db.session.commit()
    prune_local_archives(admin_user, KEY, cloud, "private-backup", db.session)
    assert sources[0].exists()
    assert sources[0].with_name(sources[0].name + ".manifest.json").exists()


@pytest.mark.parametrize("failure", ["missing", "size", "metadata"])
def test_local_retention_keeps_recovery_bytes_when_cloud_group_is_damaged(app, admin_user, failure):
    from pwd301.extensions import db
    from pwd301.services.backup_archive_service import prune_local_archives

    cloud, sources = _local_archives(app)
    object_key = "daily/" + sources[0].name + "/" + sources[0].name + ".encrypted"
    data, metadata = cloud.objects[object_key]
    if failure == "missing":
        del cloud.objects[object_key]
    elif failure == "size":
        cloud.objects[object_key] = (data + b"damage", metadata)
    else:
        cloud.objects[object_key] = (data, {"sha256": "0" * 64})
    prune_local_archives(admin_user, KEY, cloud, "private-backup", db.session)
    assert sources[0].exists()
    assert sources[0].with_name(sources[0].name + ".manifest.json").exists()
