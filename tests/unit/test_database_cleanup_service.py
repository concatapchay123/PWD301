"""Tests for production database and storage cleaning service."""

from __future__ import annotations

from pathlib import Path

from flask import Flask
from sqlalchemy import text

from backend.extensions import db
from backend.models.course import Course
from backend.models.identity import Role, User, UserRole
from backend.models.notification_audit import Notification
from backend.services.database_cleanup_service import (
    clean_database,
    clean_storage_artifacts,
)


def test_clean_storage_artifacts(tmp_path: Path) -> None:
    """Verify physical storage artifacts, quarantine tmp files, and rate limits are cleaned."""
    s_root = tmp_path / "storage"
    q_root = tmp_path / "quarantine"
    e_root = tmp_path / "exports"
    inst_root = tmp_path / "instance"

    # Setup directories
    (s_root / "blobs" / "0a" / "1b").mkdir(parents=True, exist_ok=True)
    blob_file = s_root / "blobs" / "0a" / "1b" / "dummy_blob_hash"
    blob_file.write_text("dummy blob content", encoding="utf-8")

    sample_mp4 = s_root / "sample_test.mp4"
    sample_mp4.write_text("mp4 header", encoding="utf-8")

    q_root.mkdir(parents=True, exist_ok=True)
    tmp_file = q_root / "upload_test123.tmp"
    tmp_file.write_text("quarantine content", encoding="utf-8")

    e_root.mkdir(parents=True, exist_ok=True)
    exp_file = e_root / "report.xlsx"
    exp_file.write_text("excel report", encoding="utf-8")

    (inst_root / "rate_limits").mkdir(parents=True, exist_ok=True)
    rl_file = inst_root / "rate_limits" / "ip_cache.json"
    rl_file.write_text("{}", encoding="utf-8")

    dev_db = inst_root / "test_sqlite.db"
    dev_db.write_text("sqlite", encoding="utf-8")

    summary = clean_storage_artifacts(
        storage_root=s_root,
        quarantine_root=q_root,
        export_root=e_root,
        instance_dir=inst_root,
    )

    assert summary["blobs_deleted"] == 1
    assert summary["sample_files_deleted"] == 1
    assert summary["quarantine_deleted"] == 1
    assert summary["exports_deleted"] == 1
    assert summary["rate_limits_deleted"] == 1
    assert summary["sqlite_dbs_deleted"] == 1
    assert summary["total_files_deleted"] == 6
    assert summary["bytes_freed"] > 0

    assert not blob_file.exists()
    assert not sample_mp4.exists()
    assert not tmp_file.exists()
    assert not exp_file.exists()
    assert not rl_file.exists()
    assert not dev_db.exists()

    # Directories must still exist ready for fresh use
    assert (s_root / "blobs").exists()
    assert q_root.exists()
    assert e_root.exists()


def test_clean_database_with_baseline(app: Flask) -> None:
    """Verify clean_database wipes test tables and establishes baseline roles and admin."""
    with app.app_context():
        report = clean_database(
            session=db.session,
            engine=db.engine,
            keep_baseline=True,
            clean_storage=False,
        )

        assert report["tables_targeted"] > 0
        assert report["baseline_summary"] is not None

        # Verify baseline roles and admin exist
        roles = db.session.query(Role).all()
        assert len(roles) == 3
        role_codes = {r.code for r in roles}
        assert role_codes == {"STUDENT", "INSTRUCTOR", "ADMIN"}

        admin_user = db.session.query(User).filter_by(email_normalized="admin@backend.local").one_or_none()
        assert admin_user is not None
        assert admin_user.status == "ACTIVE"

        admin_roles = db.session.query(UserRole).filter_by(user_id=admin_user.id).all()
        assert len(admin_roles) == 3

        # Verify operational tables are completely empty
        assert db.session.query(Course).count() == 0
        assert db.session.query(Notification).count() == 0


def test_clean_database_empty(app: Flask) -> None:
    """Verify clean_database without baseline leaves all application tables completely empty."""
    with app.app_context():
        report = clean_database(
            session=db.session,
            engine=db.engine,
            keep_baseline=False,
            clean_storage=False,
        )

        assert report["tables_targeted"] > 0
        assert report["baseline_summary"] is None

        # Application tables must be completely empty
        assert db.session.query(Role).count() == 0
        assert db.session.query(User).count() == 0
        assert db.session.query(UserRole).count() == 0
        assert db.session.query(Course).count() == 0

        # alembic_version must remain intact if present
        insp = db.inspect(db.engine)
        if "alembic_version" in insp.get_table_names():
            ver = db.session.execute(text("SELECT COUNT(*) FROM [alembic_version]")).scalar()
            assert ver >= 1
