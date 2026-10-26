"""Production database and storage cleaning service for PWD301 platform.

Provides deterministic, fail-safe hard-deletion of all test/demonstration records,
audit events, notifications, file attachments, and session state to prepare
the system for a pristine production deployment.

Invariants strictly preserved:
- alembic_version table is never touched (schema migration state remains valid).
- Constraints and triggers are cleanly disabled during wipe and restored with verification.
- IDENTITY sequences are re-seeded to 0 so fresh records start from ID 1.
- Canonical system baseline roles (STUDENT, INSTRUCTOR, ADMIN) and root administrator
  are re-established via seed_baseline when keep_baseline is True.
- Disk storage artifacts (quarantine, orphan blobs, export files, dev sqlite/rate limits)
  are wiped while maintaining required directory structures.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session

from backend.extensions import db
from backend.seeds.baseline import seed_baseline

logger = logging.getLogger(__name__)


def clean_storage_artifacts(
    storage_root: Path | str | None = None,
    quarantine_root: Path | str | None = None,
    export_root: Path | str | None = None,
    instance_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Clean all physical storage artifacts, quarantine tmp files, exports, and dev caches.

    Args:
        storage_root: Path to storage directory (defaults to ./storage or env).
        quarantine_root: Path to quarantine directory (defaults to ./quarantine or env).
        export_root: Path to exports directory (defaults to ./exports or env).
        instance_dir: Path to instance directory (defaults to ./src/instance or ./instance).

    Returns:
        Summary dictionary with counts of files deleted and total bytes freed.
    """
    base_dir = Path.cwd()
    s_root = Path(storage_root or os.environ.get("FILE_STORAGE_ROOT", base_dir / "storage")).resolve()
    q_root = Path(quarantine_root or os.environ.get("FILE_QUARANTINE_ROOT", base_dir / "quarantine")).resolve()
    e_root = Path(export_root or os.environ.get("EXPORT_ROOT", base_dir / "exports")).resolve()
    
    inst_candidates = [
        Path(instance_dir).resolve() if instance_dir else None,
        (base_dir / "src" / "instance").resolve(),
        (base_dir / "instance").resolve(),
    ]
    inst_root = next((p for p in inst_candidates if p and p.exists()), (base_dir / "src" / "instance").resolve())

    summary: dict[str, Any] = {
        "blobs_deleted": 0,
        "sample_files_deleted": 0,
        "drm_hls_deleted": 0,
        "instructor_apps_deleted": 0,
        "quarantine_deleted": 0,
        "exports_deleted": 0,
        "rate_limits_deleted": 0,
        "sqlite_dbs_deleted": 0,
        "total_files_deleted": 0,
        "bytes_freed": 0,
    }

    # 1. Clean storage/blobs
    blobs_dir = s_root / "blobs"
    if blobs_dir.exists():
        for item in blobs_dir.rglob("*"):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    summary["blobs_deleted"] += 1
                    summary["total_files_deleted"] += 1
                    summary["bytes_freed"] += size
                except OSError:
                    pass
        shutil.rmtree(blobs_dir, ignore_errors=True)
    blobs_dir.mkdir(parents=True, exist_ok=True)

    # 2. Clean sample video/test files in storage
    if s_root.exists():
        for sample_file in s_root.glob("sample_*.mp4"):
            if sample_file.is_file():
                try:
                    size = sample_file.stat().st_size
                    sample_file.unlink()
                    summary["sample_files_deleted"] += 1
                    summary["total_files_deleted"] += 1
                    summary["bytes_freed"] += size
                except OSError:
                    pass

    # 3. Clean storage/drm_hls
    drm_dir = s_root / "drm_hls"
    if drm_dir.exists():
        for item in drm_dir.rglob("*"):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    summary["drm_hls_deleted"] += 1
                    summary["total_files_deleted"] += 1
                    summary["bytes_freed"] += size
                except OSError:
                    pass
        shutil.rmtree(drm_dir, ignore_errors=True)
    drm_dir.mkdir(parents=True, exist_ok=True)

    # 4. Clean storage/instructor_applications
    ia_dir = s_root / "instructor_applications"
    if ia_dir.exists():
        for item in ia_dir.rglob("*"):
            if item.is_file():
                try:
                    size = item.stat().st_size
                    summary["instructor_apps_deleted"] += 1
                    summary["total_files_deleted"] += 1
                    summary["bytes_freed"] += size
                except OSError:
                    pass
        shutil.rmtree(ia_dir, ignore_errors=True)
    ia_dir.mkdir(parents=True, exist_ok=True)

    # 5. Clean quarantine files (all temporary and bypass files)
    if q_root.exists():
        for q_file in q_root.rglob("*"):
            if q_file.is_file() and q_file.name != ".gitkeep":
                try:
                    size = q_file.stat().st_size
                    summary["quarantine_deleted"] += 1
                    summary["total_files_deleted"] += 1
                    summary["bytes_freed"] += size
                except OSError:
                    pass
        shutil.rmtree(q_root, ignore_errors=True)
    q_root.mkdir(parents=True, exist_ok=True)

    # 6. Clean export files
    if e_root.exists():
        for exp_file in e_root.rglob("*"):
            if exp_file.is_file() and exp_file.name != ".gitkeep":
                try:
                    size = exp_file.stat().st_size
                    summary["exports_deleted"] += 1
                    summary["total_files_deleted"] += 1
                    summary["bytes_freed"] += size
                except OSError:
                    pass
        shutil.rmtree(e_root, ignore_errors=True)
    e_root.mkdir(parents=True, exist_ok=True)

    # 7. Clean rate_limits in instance directory
    rl_dir = inst_root / "rate_limits"
    if rl_dir.exists():
        for rl_file in rl_dir.rglob("*"):
            if rl_file.is_file():
                try:
                    size = rl_file.stat().st_size
                    rl_file.unlink()
                    summary["rate_limits_deleted"] += 1
                    summary["total_files_deleted"] += 1
                    summary["bytes_freed"] += size
                except OSError as err:
                    logger.warning("Could not delete rate limit file %s: %s", rl_file, err)

    # 6. Clean dev SQLite database file if present
    for db_path in [inst_root / "test_sqlite.db", inst_root / "pwd301_dev.db"]:
        if db_path.exists() and db_path.is_file():
            try:
                size = db_path.stat().st_size
                db_path.unlink()
                summary["sqlite_dbs_deleted"] += 1
                summary["total_files_deleted"] += 1
                summary["bytes_freed"] += size
            except OSError as err:
                logger.warning("Could not delete sqlite db %s: %s", db_path, err)

    return summary


def clean_database(
    session: Session | scoped_session[Any] | None = None,
    engine: Engine | None = None,
    keep_baseline: bool = True,
    clean_storage: bool = True,
) -> dict[str, Any]:
    """Execute complete hard delete of all test/demonstration data from the database.

    Wipes all application tables while strictly preserving alembic_version.
    If keep_baseline is True, seeds canonical baseline roles and root administrator.
    If clean_storage is True, removes all test storage files and quarantine caches.

    Args:
        session: Active SQLAlchemy session (defaults to db.session).
        engine: SQLAlchemy Engine (defaults to session.bind or db.engine).
        keep_baseline: Whether to seed canonical baseline data after wiping.
        clean_storage: Whether to clean physical storage directories.

    Returns:
        Structured audit report detailing cleaned tables, deleted row counts,
        baseline status, and storage cleanup metrics.
    """
    sess = session if session is not None else db.session
    eng = engine if engine is not None else (sess.get_bind() if hasattr(sess, "get_bind") else db.engine)
    dialect_name = eng.dialect.name.lower()

    insp = sa.inspect(eng)
    all_tables = set(insp.get_table_names())
    target_tables = sorted([t for t in all_tables if t != "alembic_version"])

    audit_report: dict[str, Any] = {
        "engine": str(eng.url.render_as_string(hide_password=True)),
        "dialect": dialect_name,
        "tables_targeted": len(target_tables),
        "deleted_records": {},
        "total_records_deleted": 0,
        "identities_reseeded": 0,
        "baseline_summary": None,
        "storage_summary": None,
    }

    # Count rows before deletion
    with eng.connect() as probe_conn:
        for table in target_tables:
            try:
                count = probe_conn.execute(text(f"SELECT COUNT(*) FROM [{table}]")).scalar() or 0
                if count > 0:
                    audit_report["deleted_records"][table] = count
                    audit_report["total_records_deleted"] += count
            except Exception as probe_err:
                logger.warning("Could not probe count for table %s: %s", table, probe_err)

    if dialect_name == "mssql":
        # MSSQL: Disable constraints and triggers, delete, reseed identity, re-enable
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # 1. Disable constraints and triggers
            conn.execute(text("EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT all'"))
            conn.execute(text("EXEC sp_MSforeachtable 'ALTER TABLE ? DISABLE TRIGGER all'"))

            # 2. Delete all records from targeted tables
            for table in target_tables:
                conn.execute(text(f"DELETE FROM [{table}]"))

            # 3. Identify and reseed identity columns to 0
            ident_rows = conn.execute(text("""
                SELECT DISTINCT t.name AS table_name
                FROM sys.tables t
                JOIN sys.columns c ON t.object_id = c.object_id
                WHERE c.is_identity = 1
            """)).fetchall()
            ident_tables = [r[0] for r in ident_rows if r[0] != "alembic_version"]

            for it in ident_tables:
                try:
                    conn.execute(text(f"DBCC CHECKIDENT ('[{it}]', RESEED, 0)"))
                    audit_report["identities_reseeded"] += 1
                except Exception as id_err:
                    logger.debug("CHECKIDENT skipped for %s: %s", it, id_err)

            # 4. Enable triggers and re-validate constraints
            conn.execute(text("EXEC sp_MSforeachtable 'ALTER TABLE ? ENABLE TRIGGER all'"))
            conn.execute(text("EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT all'"))

    elif dialect_name == "sqlite":
        # SQLite: Disable foreign keys, delete tables, reset autoincrement sequences
        with eng.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF;"))
            for table in target_tables:
                conn.execute(text(f"DELETE FROM [{table}];"))
            try:
                conn.execute(text("DELETE FROM sqlite_sequence;"))
            except Exception:
                pass
            conn.execute(text("PRAGMA foreign_keys = ON;"))
            conn.commit()

    else:
        # Generic ANSI SQL fallback
        with eng.connect() as conn:
            for table in reversed(target_tables):
                conn.execute(text(f"DELETE FROM {table}"))
            conn.commit()

    # Re-seed baseline data if requested
    if keep_baseline:
        try:
            sess.rollback()
        except Exception:
            pass
        summary = seed_baseline(sess)
        audit_report["baseline_summary"] = summary

    # Clean physical storage artifacts if requested
    if clean_storage:
        audit_report["storage_summary"] = clean_storage_artifacts()

    return audit_report
