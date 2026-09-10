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

import datetime
import json
import uuid
from typing import Any

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

_BACKUP_UUID_PREFIX = b"\xba\xc0\x00\x00\x00\x00\x00\x00"
_HEALTH_UUID_PREFIX = b"\x7e\xa1\x00\x00\x00\x00\x00\x00"


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
        sa.Index(
            "ux_jobs_dedupe",
            "job_type",
            "dedupe_key",
            unique=True,
            mssql_where=sa.text("dedupe_key IS NOT NULL"),
            sqlite_where=sa.text("dedupe_key IS NOT NULL"),
        ),
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

    @property
    def public_id(self) -> uuid.UUID:
        """Deterministic public UUID adhering to ADR-002 Zero PK Leakage."""
        if self.id is None:
            return uuid.uuid4()
        return uuid.UUID(bytes=_BACKUP_UUID_PREFIX + self.id.to_bytes(8, byteorder="big"))

    @classmethod
    def resolve_id_from_public_id(cls, pub_id: str | uuid.UUID, session: Any = None) -> int | None:
        """Resolve internal BIGINT ID from public UUID without exposing raw PK."""
        try:
            u = uuid.UUID(str(pub_id)) if not isinstance(pub_id, uuid.UUID) else pub_id
            if u.bytes[:8] == _BACKUP_UUID_PREFIX:
                return int.from_bytes(u.bytes[8:], byteorder="big")
        except Exception:
            pass
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize backup metadata adhering strictly to ADR-002 (zero internal PKs)."""
        return {
            "backup_id": str(self.public_id),
            "backup_type": self.backup_type,
            "status": self.status,
            "storage_location": self.storage_location,
            "database_backup_name": self.database_backup_name,
            "file_manifest_name": self.file_manifest_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "restore_tested_at": (
                self.restore_tested_at.isoformat() if self.restore_tested_at else None
            ),
            "last_error": self.last_error,
            "started_by_user_id": str(self.started_by.public_id) if self.started_by else None,
        }


# Canonical model alias for operations backup engine
SystemBackup = BackupRun


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

    @property
    def public_id(self) -> uuid.UUID:
        """Deterministic public UUID adhering to ADR-002 Zero PK Leakage."""
        if self.id is None:
            return uuid.uuid4()
        return uuid.UUID(bytes=_HEALTH_UUID_PREFIX + self.id.to_bytes(8, byteorder="big"))

    @classmethod
    def resolve_id_from_public_id(cls, pub_id: str | uuid.UUID, session: Any = None) -> int | None:
        """Resolve internal BIGINT ID from public UUID without exposing raw PK."""
        try:
            u = uuid.UUID(str(pub_id)) if not isinstance(pub_id, uuid.UUID) else pub_id
            if u.bytes[:8] == _HEALTH_UUID_PREFIX:
                return int.from_bytes(u.bytes[8:], byteorder="big")
        except Exception:
            pass
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize system health snapshot adhering to ADR-002."""
        parsed_details = None
        if self.details_json:
            try:
                parsed_details = json.loads(self.details_json)
            except Exception:
                parsed_details = self.details_json
        return {
            "snapshot_id": str(self.public_id),
            "component": self.component,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "details": parsed_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


_MAINT_UUID_PREFIX = b"\xca\xfe\x00\x00\x00\x00\x00\x00"


class MaintenanceWindow:
    """System maintenance window representation backed by canonical 'system_alerts' table.

    Does not create an extra database table, preserving the 71 canonical tables architecture.
    """

    alert: SystemAlert | None
    public_id: uuid.UUID
    reason: str
    status: str
    started_by_user_id: int | None
    estimated_duration_minutes: int
    started_at: datetime.datetime | None
    estimated_end_at: datetime.datetime | None
    ended_at: datetime.datetime | None
    ended_by_user_id: int | None
    created_at: datetime.datetime | None
    id: int | None

    def __init__(
        self,
        alert: SystemAlert | None = None,
        *,
        public_id: uuid.UUID | None = None,
        reason: str = "",
        status: str = "ACTIVE",
        started_by_user_id: int | None = None,
        estimated_duration_minutes: int = 60,
        started_at: datetime.datetime | None = None,
        estimated_end_at: datetime.datetime | None = None,
        ended_at: datetime.datetime | None = None,
        ended_by_user_id: int | None = None,
        created_at: datetime.datetime | None = None,
    ) -> None:
        self.alert = alert
        if alert is not None:
            data: dict[str, Any] = {}
            if alert.message:
                try:
                    data = json.loads(alert.message)
                except Exception:
                    data = {"reason": alert.message}
            raw_pub = data.get("public_id")
            if raw_pub:
                try:
                    self.public_id = uuid.UUID(str(raw_pub))
                except Exception:
                    self.public_id = uuid.UUID(
                        bytes=_MAINT_UUID_PREFIX + alert.id.to_bytes(8, "big")
                    )
            else:
                self.public_id = uuid.UUID(bytes=_MAINT_UUID_PREFIX + alert.id.to_bytes(8, "big"))
            self.reason = data.get("reason", alert.message or "")
            self.status = (
                "ACTIVE"
                if alert.status == "OPEN"
                else ("COMPLETED" if alert.status == "RESOLVED" else "CANCELLED")
            )
            self.started_by_user_id = alert.acknowledged_by_user_id or data.get(
                "started_by_user_id"
            )
            self.estimated_duration_minutes = int(data.get("estimated_duration_minutes", 60))
            self.started_at = alert.acknowledged_at or alert.created_at
            raw_est = data.get("estimated_end_at")
            if raw_est:
                try:
                    self.estimated_end_at = datetime.datetime.fromisoformat(raw_est)
                except Exception:
                    self.estimated_end_at = (
                        self.started_at
                        + datetime.timedelta(minutes=self.estimated_duration_minutes)
                        if self.started_at
                        else None
                    )
            else:
                self.estimated_end_at = (
                    self.started_at + datetime.timedelta(minutes=self.estimated_duration_minutes)
                    if self.started_at
                    else None
                )
            self.ended_at = alert.resolved_at
            self.ended_by_user_id = data.get("ended_by_user_id")
            self.created_at = alert.created_at
            self.id = alert.id
        else:
            self.public_id = public_id or uuid.uuid4()
            self.reason = reason
            self.status = status
            self.started_by_user_id = started_by_user_id
            self.estimated_duration_minutes = estimated_duration_minutes
            self.started_at = started_at or utc_now()
            self.estimated_end_at = estimated_end_at or (
                self.started_at + datetime.timedelta(minutes=estimated_duration_minutes)
            )
            self.ended_at = ended_at
            self.ended_by_user_id = ended_by_user_id
            self.created_at = created_at or utc_now()
            self.id = None

    @classmethod
    def resolve_id_from_public_id(cls, pub_id: str | uuid.UUID, session: Any = None) -> int | None:
        """Resolve internal BIGINT ID from public UUID."""
        try:
            u = uuid.UUID(str(pub_id)) if not isinstance(pub_id, uuid.UUID) else pub_id
            u_bytes = u.bytes
            if u_bytes.startswith(_MAINT_UUID_PREFIX):
                return int.from_bytes(u_bytes[8:], "big")
            sess = session or db.session
            alerts = (
                sess.query(SystemAlert).filter(SystemAlert.alert_type == "MAINTENANCE_WINDOW").all()
            )
            for a in alerts:
                if a.message and str(u) in a.message:
                    return a.id
            return None
        except Exception:
            return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize maintenance window conforming to ADR-002 Zero PK Leakage."""
        return {
            "window_id": str(self.public_id),
            "reason": self.reason,
            "status": self.status,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "estimated_end_at": (
                self.estimated_end_at.isoformat() if self.estimated_end_at else None
            ),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "started_by_user_id": None,
            "ended_by_user_id": None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
