"""Operations, analytics, health, and backup models for PWD301.

Implements canonical schema tables from sql/009_operations.sql:
- background_jobs
- system_alerts
- backup_runs
- grade_exports
- analytics_snapshots
- system_health_snapshots
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from pwd301.extensions import Base, db
from pwd301.models.types import (
    GUID,
    BigIntPK,
    NVarCharMax,
    RowVersion,
    UTCDateTime,
    utc_now,
)


class BackgroundJob(Base):
    """General asynchronous worker queue model mapping to 'background_jobs' table."""

    __tablename__ = "background_jobs"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    job_key = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWID()"),
    )
    job_type = db.Column(sa.String(48), nullable=False)
    dedupe_key = db.Column(sa.Unicode(200), nullable=True)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="QUEUED",
        server_default=sa.text("'QUEUED'"),
    )
    priority = db.Column(
        sa.Integer,
        nullable=False,
        default=100,
        server_default=sa.text("100"),
    )
    attempt_count = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    max_attempts = db.Column(
        sa.Integer,
        nullable=False,
        default=5,
        server_default=sa.text("5"),
    )
    available_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    claimed_at = db.Column(UTCDateTime, nullable=True)
    lease_expires_at = db.Column(UTCDateTime, nullable=True)
    completed_at = db.Column(UTCDateTime, nullable=True)
    payload_json = db.Column(NVarCharMax, nullable=True)
    last_error = db.Column(sa.Unicode(2000), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "job_type IN ('FILE_SCAN','IMPORT','REGRADE','KNOWLEDGE_INDEX',"
            "'EMAIL','CLEANUP','ANALYTICS','BACKUP','EXPORT')",
            name="ck_background_jobs_1",
        ),
        sa.CheckConstraint(
            "status IN ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELLED')",
            name="ck_background_jobs_2",
        ),
        sa.CheckConstraint("priority >= 0", name="ck_background_jobs_3"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_background_jobs_4"),
        sa.CheckConstraint("max_attempts > 0", name="ck_background_jobs_5"),
        sa.CheckConstraint(
            "payload_json IS NULL OR ISJSON(payload_json)=1", name="ck_background_jobs_6"
        ),
        sa.Index("ix_background_jobs_poll", "status", "available_at", "priority"),
    )


class SystemAlert(Base):
    """System-level operations alert incident mapping to 'system_alerts' table."""

    __tablename__ = "system_alerts"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    alert_type = db.Column(sa.String(48), nullable=False)
    severity = db.Column(sa.String(16), nullable=False)
    status = db.Column(
        sa.String(16),
        nullable=False,
        default="OPEN",
        server_default=sa.text("'OPEN'"),
    )
    source_type = db.Column(sa.String(32), nullable=True)
    source_id = db.Column(sa.BigInteger, nullable=True)
    message = db.Column(sa.Unicode(2000), nullable=False)
    acknowledged_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_system_alerts_acknowledged_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    acknowledged_at = db.Column(UTCDateTime, nullable=True)
    resolved_at = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "severity IN ('INFO','WARN','HIGH','CRITICAL')", name="ck_system_alerts_1"
        ),
        sa.CheckConstraint(
            "status IN ('OPEN','ACKNOWLEDGED','RESOLVED')", name="ck_system_alerts_2"
        ),
        sa.Index("ix_system_alerts_status", "status", "severity", "created_at"),
    )

    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_user_id])


class BackupRun(Base):
    """Database/filesystem backup operation audit mapping to 'backup_runs' table."""

    __tablename__ = "backup_runs"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    backup_type = db.Column(sa.String(20), nullable=False)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="RUNNING",
        server_default=sa.text("'RUNNING'"),
    )
    started_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_backup_runs_started_by_user_id", ondelete="SET NULL"),
        nullable=True,
    )
    storage_location = db.Column(sa.Unicode(500), nullable=False)
    database_backup_name = db.Column(sa.Unicode(255), nullable=True)
    file_manifest_name = db.Column(sa.Unicode(255), nullable=True)
    started_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    completed_at = db.Column(UTCDateTime, nullable=True)
    verified_at = db.Column(UTCDateTime, nullable=True)
    restore_tested_at = db.Column(UTCDateTime, nullable=True)
    last_error = db.Column(sa.Unicode(2000), nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "backup_type IN ('AUTOMATIC','MANUAL','RESTORE_DRILL')",
            name="ck_backup_runs_1",
        ),
        sa.CheckConstraint("status IN ('RUNNING','SUCCEEDED','FAILED')", name="ck_backup_runs_2"),
        sa.Index("ix_backup_runs_time", "started_at", "status"),
    )

    started_by = relationship("User", foreign_keys=[started_by_user_id])


class GradeExport(Base):
    """Export request for course grades mapping to 'grade_exports' table."""

    __tablename__ = "grade_exports"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_grade_exports_course_id"),
        nullable=False,
    )
    requested_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_grade_exports_requested_by_user_id"),
        nullable=False,
    )
    background_job_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "background_jobs.id",
            name="fk_grade_exports_background_job_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    file_asset_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("file_assets.id", name="fk_grade_exports_file_asset_id", ondelete="SET NULL"),
        nullable=True,
    )
    filters_json = db.Column(NVarCharMax, nullable=False)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="QUEUED",
        server_default=sa.text("'QUEUED'"),
    )
    row_count = db.Column(sa.Integer, nullable=True)
    expires_at = db.Column(UTCDateTime, nullable=False)
    completed_at = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "filters_json IS NOT NULL AND ISJSON(filters_json)=1",
            name="ck_grade_exports_1",
        ),
        sa.CheckConstraint(
            "status IN ('QUEUED','PROCESSING','READY','FAILED','EXPIRED')",
            name="ck_grade_exports_2",
        ),
        sa.CheckConstraint("row_count IS NULL OR row_count >= 0", name="ck_grade_exports_3"),
        sa.Index("ix_grade_exports_course", "course_id", "status"),
    )

    course = relationship("Course", foreign_keys=[course_id])
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])


class AnalyticsSnapshot(Base):
    """Aggregated analytical metric cache snapshot mapping to 'analytics_snapshots'."""

    __tablename__ = "analytics_snapshots"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    scope_type = db.Column(sa.String(16), nullable=False)
    scope_id = db.Column(sa.BigInteger, nullable=True)
    metric_code = db.Column(sa.String(64), nullable=False)
    value_number = db.Column(sa.Numeric(18, 6), nullable=True)
    value_json = db.Column(NVarCharMax, nullable=True)
    as_of_at = db.Column(UTCDateTime, nullable=False)
    expires_at = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "scope_type IN ('SYSTEM','COURSE','ASSESSMENT')", name="ck_analytics_snapshots_1"
        ),
        sa.CheckConstraint(
            "value_json IS NULL OR ISJSON(value_json)=1", name="ck_analytics_snapshots_2"
        ),
        sa.Index(
            "ix_analytics_scope_metric",
            "scope_type",
            "scope_id",
            "metric_code",
            "as_of_at",
        ),
    )


class SystemHealthSnapshot(Base):
    """Component healthcheck observation mapping to 'system_health_snapshots'."""

    __tablename__ = "system_health_snapshots"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    component = db.Column(sa.String(32), nullable=False)
    status = db.Column(sa.String(16), nullable=False)
    latency_ms = db.Column(sa.Integer, nullable=True)
    details_json = db.Column(NVarCharMax, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "component IN ('WEB','DB','WORKER','CLAMAV','GEMINI','STORAGE','BACKUP')",
            name="ck_system_health_snapshots_1",
        ),
        sa.CheckConstraint(
            "status IN ('HEALTHY','DEGRADED','DOWN','UNKNOWN')",
            name="ck_system_health_snapshots_2",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0", name="ck_system_health_snapshots_3"
        ),
        sa.CheckConstraint(
            "details_json IS NULL OR ISJSON(details_json)=1",
            name="ck_system_health_snapshots_4",
        ),
        sa.Index("ix_system_health_time", "component", "created_at"),
    )
