"""File management and document import models for PWD301.

Implements canonical schema tables from sql/006_files_import.sql:
- file_blobs
- file_assets
- file_revisions
- file_scan_results
- lesson_resources
- question_revision_resources
- document_import_jobs
- import_questions
- import_duplicate_candidates
- import_question_resources
"""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from pwd301.extensions import Base, db
from pwd301.models.types import (
    GUID,
    BigIntPK,
    Binary32,
    NVarCharMax,
    RowVersion,
    UTCDateTime,
    utc_now,
)


class FileBlob(Base):
    """Physical deduplicated storage blob mapping to 'file_blobs' table.

    *Lưu ý kiến trúc: Model này sử dụng cơ chế Soft-delete (deleted_at).
    Do DB áp dụng mặc định NO ACTION cho Foreign Keys, tầng Application Service
    phải tự chịu trách nhiệm xử lý cascade data (ẩn/xóa dữ liệu con) bằng code Python.*
    """

    __tablename__ = "file_blobs"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    sha256 = db.Column(Binary32, nullable=False, unique=True)
    size_bytes = db.Column(sa.BigInteger, nullable=False)
    detected_mime_type = db.Column(sa.Unicode(150), nullable=False)
    storage_key = db.Column(sa.Unicode(500), nullable=False, unique=True)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="PRESENT",
        server_default=sa.text("'PRESENT'"),
    )
    reference_count = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    deleted_at = db.Column(UTCDateTime, nullable=True)

    __table_args__ = (
        sa.CheckConstraint("size_bytes > 0", name="ck_file_blobs_1"),
        sa.CheckConstraint("status IN ('PRESENT','DELETING','DELETED')", name="ck_file_blobs_2"),
        sa.CheckConstraint("reference_count >= 0", name="ck_file_blobs_3"),
    )

    @property
    def sha256_hex(self) -> str:
        """Return SHA-256 hash as hexadecimal string."""
        if isinstance(self.sha256, (bytes, bytearray)):
            return self.sha256.hex()
        return str(self.sha256)

    @property
    def sha256_hash(self) -> str:
        """Alias for sha256_hex conforming to task description."""
        return self.sha256_hex

    @property
    def mime_type(self) -> str:
        """Alias for detected_mime_type conforming to task description."""
        return self.detected_mime_type

    @mime_type.setter
    def mime_type(self, value: str) -> None:
        self.detected_mime_type = value

    @property
    def storage_path(self) -> str:
        """Alias for storage_key conforming to task description."""
        return self.storage_key

    @storage_path.setter
    def storage_path(self, value: str) -> None:
        self.storage_key = value


class FileAsset(Base):
    """Logical course-scoped file identity mapping to 'file_assets' table.

    *Lưu ý kiến trúc: Model này sử dụng cơ chế Soft-delete (deleted_at).
    Do DB áp dụng mặc định NO ACTION cho Foreign Keys, tầng Application Service
    phải tự chịu trách nhiệm xử lý cascade data (ẩn/xóa dữ liệu con) bằng code Python.*
    """

    __tablename__ = "file_assets"

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
        sa.ForeignKey("courses.id", name="fk_file_assets_course_id"),
        nullable=False,
    )
    created_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_file_assets_created_by_user_id"),
        nullable=False,
    )
    asset_type = db.Column(sa.String(24), nullable=False)
    display_name = db.Column(sa.Unicode(255), nullable=False)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    retention_until = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    updated_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)
    deleted_at = db.Column(UTCDateTime, nullable=True)
    restore_until = db.Column(UTCDateTime, nullable=True)
    deleted_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_file_assets_deleted_by_user_id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "asset_type IN ('RESOURCE','QUESTION_IMAGE','COURSE_IMAGE','IMPORT_SOURCE',"
            "'EXPORT','OTHER')",
            name="ck_file_assets_1",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','ACTIVE','REPLACED','TRASH','HISTORICAL')",
            name="ck_file_assets_2",
        ),
        sa.Index("ix_file_assets_course", "course_id", "status"),
    )

    course = relationship("Course", foreign_keys=[course_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_user_id])
    revisions = relationship(
        "FileRevision",
        foreign_keys="FileRevision.file_asset_id",
        back_populates="file_asset",
        cascade="all, delete-orphan",
        order_by="FileRevision.revision_no",
    )
    current_revision = relationship(
        "FileRevision",
        primaryjoin=(
            "and_(FileAsset.id == foreign(FileRevision.file_asset_id), "
            "FileRevision.is_current == True)"
        ),
        uselist=False,
        viewonly=True,
    )

    @property
    def filename(self) -> str:
        """Alias for display_name conforming to task description."""
        return self.display_name

    @filename.setter
    def filename(self, value: str) -> None:
        self.display_name = value

    @property
    def owner_id(self) -> int:
        """Alias for created_by_user_id conforming to task description."""
        return self.created_by_user_id

    @owner_id.setter
    def owner_id(self, value: int) -> None:
        self.created_by_user_id = value

    def _effective_revision(self) -> Any:
        """Resolve current revision or fallback to latest available revision."""
        if self.current_revision is not None:
            return self.current_revision
        if self.revisions:
            return self.revisions[-1]
        return None

    @property
    def original_filename(self) -> str:
        """Original uploaded filename or fallback to display_name."""
        rev = self._effective_revision()
        if rev and getattr(rev, "original_filename", None):
            return rev.original_filename
        return self.display_name

    @property
    def original_file_name(self) -> str:
        """Alias for original_filename."""
        return self.original_filename

    @property
    def file_name(self) -> str:
        """Alias for display_name."""
        return self.display_name

    @property
    def size_bytes(self) -> int:
        """Total size in bytes from effective revision."""
        rev = self._effective_revision()
        if rev and getattr(rev, "size_bytes", None) is not None:
            return rev.size_bytes
        return 0

    @property
    def file_size_bytes(self) -> int:
        """Alias for size_bytes."""
        return self.size_bytes

    @property
    def mime_type(self) -> str:
        """Detected or declared MIME type from effective revision."""
        rev = self._effective_revision()
        if rev:
            return (
                getattr(rev, "detected_mime_type", None)
                or getattr(rev, "declared_mime_type", None)
                or "application/octet-stream"
            )
        return "application/octet-stream"

    @property
    def detected_mime_type(self) -> str:
        """Alias for mime_type."""
        return self.mime_type

    @property
    def virus_scan_status(self) -> str:
        """Consolidated virus scan status ('CLEAN', 'INFECTED', 'PENDING', 'BLOCKED').

        Enforces Fail-Closed invariant: a file is only CLEAN when both the
        logical FileAsset and its effective FileRevision are strictly ACTIVE.
        """
        rev = self._effective_revision()
        rev_status = getattr(rev, "status", None) if rev else None

        # 1. Blocked or error states
        if self.status == "BLOCKED" or rev_status == "BLOCKED":
            return "BLOCKED"
        if (
            rev
            and getattr(rev, "scan_results", None)
            and any(getattr(sr, "status", None) == "ERROR" for sr in rev.scan_results)
        ):
            return "BLOCKED"

        # 2. Infected or rejected states
        if self.status in ("REJECTED", "INFECTED") or rev_status in ("REJECTED", "INFECTED"):
            return "INFECTED"

        # 3. Unresolved, scanning, validating, or quarantined states
        if (
            rev is None
            or self.status in ("PENDING", "QUARANTINED", "VALIDATING", "SCANNING")
            or rev_status in ("PENDING", "QUARANTINED", "VALIDATING", "SCANNING")
        ):
            return "PENDING"

        # 4. Clean only if BOTH are strictly ACTIVE
        if self.status == "ACTIVE" and rev_status == "ACTIVE":
            return "CLEAN"

        # 5. Fail-closed fallback
        return "PENDING"

    @property
    def is_video(self) -> bool:
        """Determine if asset represents a playable video file."""
        mime = (self.mime_type or "").lower()
        if mime.startswith("video/"):
            return True
        name = (self.original_filename or "").lower()
        return any(name.endswith(ext) for ext in (".mp4", ".webm", ".mkv", ".mov", ".avi"))

    @property
    def is_pdf(self) -> bool:
        """Determine if asset represents a PDF document."""
        mime = (self.mime_type or "").lower()
        if mime == "application/pdf":
            return True
        name = (self.original_filename or "").lower()
        return name.endswith(".pdf")


class FileRevision(Base):
    """Versioned file instance mapping to 'file_revisions' table."""

    __tablename__ = "file_revisions"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    file_asset_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("file_assets.id", name="fk_file_revisions_file_asset_id"),
        nullable=False,
    )
    revision_no = db.Column(sa.Integer, nullable=False)
    is_current = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    blob_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("file_blobs.id", name="fk_file_revisions_blob_id", ondelete="SET NULL"),
        nullable=True,
    )
    original_filename = db.Column(sa.Unicode(255), nullable=False)
    declared_mime_type = db.Column(sa.Unicode(150), nullable=True)
    detected_mime_type = db.Column(sa.Unicode(150), nullable=True)
    size_bytes = db.Column(sa.BigInteger, nullable=False)
    status = db.Column(
        sa.String(24),
        nullable=False,
        default="QUARANTINED",
        server_default=sa.text("'QUARANTINED'"),
    )
    uploaded_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_file_revisions_uploaded_by_user_id"),
        nullable=False,
    )
    quarantine_key = db.Column(sa.Unicode(500), nullable=True)
    security_checks_completed_at = db.Column(UTCDateTime, nullable=True)
    activated_at = db.Column(UTCDateTime, nullable=True)
    replaced_at = db.Column(UTCDateTime, nullable=True)
    recovery_until = db.Column(UTCDateTime, nullable=True)
    rejection_reason = db.Column(sa.Unicode(1000), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "file_asset_id", "revision_no", name="uq_file_revisions_file_asset_id_revision_no_1"
        ),
        sa.CheckConstraint("revision_no > 0", name="ck_file_revisions_1"),
        sa.CheckConstraint("size_bytes > 0", name="ck_file_revisions_2"),
        sa.CheckConstraint(
            "status IN ('QUARANTINED','VALIDATING','SCANNING','SAFE','ACTIVE',"
            "'REJECTED','REPLACED','RECOVERY','DELETED')",
            name="ck_file_revisions_3",
        ),
        sa.Index("ix_file_revisions_status", "status", "created_at"),
        sa.Index(
            "ux_file_revisions_active",
            "file_asset_id",
            unique=True,
            mssql_where=sa.text("status='ACTIVE'"),
            sqlite_where=sa.text("status='ACTIVE'"),
        ),
        sa.Index(
            "uq_file_revisions_current",
            "file_asset_id",
            unique=True,
            mssql_where=sa.text("is_current = 1"),
            sqlite_where=sa.text("is_current = 1"),
        ),
        sa.Index(
            "ix_file_revisions_recovery",
            "recovery_until",
            "status",
            mssql_where=sa.text("recovery_until IS NOT NULL"),
            sqlite_where=sa.text("recovery_until IS NOT NULL"),
        ),
    )

    file_asset = relationship("FileAsset", foreign_keys=[file_asset_id], back_populates="revisions")
    blob = relationship("FileBlob", foreign_keys=[blob_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])
    scan_results = relationship(
        "FileScanResult",
        back_populates="file_revision",
        cascade="all, delete-orphan",
    )

    @property
    def public_id(self) -> uuid.UUID:
        """Synthetic public UUIDv5 identifier conforming to ADR-002."""
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.file_revision.{self.id}")


class FileScanResult(Base):
    """Malware and integrity verification record mapping to 'file_scan_results' table."""

    __tablename__ = "file_scan_results"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    file_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("file_revisions.id", name="fk_file_scan_results_file_revision_id"),
        nullable=False,
    )
    scan_type = db.Column(sa.String(24), nullable=False)
    engine = db.Column(sa.Unicode(100), nullable=False)
    engine_version = db.Column(sa.Unicode(100), nullable=True)
    status = db.Column(sa.String(16), nullable=False)
    details_json = db.Column(NVarCharMax, nullable=True)
    started_at = db.Column(UTCDateTime, nullable=True)
    completed_at = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "scan_type IN ('FILE_VALIDATION','MALWARE','STRUCTURE',"
            "'RESOURCE_LIMIT','CONTENT_SECURITY')",
            name="ck_file_scan_results_1",
        ),
        sa.CheckConstraint("status IN ('PASS','FAIL','ERROR')", name="ck_file_scan_results_2"),
        sa.CheckConstraint(
            "details_json IS NULL OR ISJSON(details_json)=1", name="ck_file_scan_results_3"
        ),
        sa.Index("ix_file_scan_results_revision", "file_revision_id", "status"),
    )

    file_revision = relationship("FileRevision", back_populates="scan_results")


class LessonResource(Base):
    """Attached resources for a lesson mapping to 'lesson_resources' table."""

    __tablename__ = "lesson_resources"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    lesson_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("lessons.id", name="fk_lesson_resources_lesson_id"),
        nullable=False,
    )
    file_asset_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("file_assets.id", name="fk_lesson_resources_file_asset_id"),
        nullable=False,
    )
    position = db.Column(
        sa.Integer,
        nullable=False,
        default=1,
        server_default=sa.text("1"),
    )
    label = db.Column(sa.Unicode(255), nullable=True)
    is_required = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "lesson_id", "file_asset_id", name="uq_lesson_resources_lesson_id_file_asset_id_1"
        ),
        sa.UniqueConstraint(
            "lesson_id", "position", name="uq_lesson_resources_lesson_id_position_2"
        ),
        sa.CheckConstraint("position > 0", name="ck_lesson_resources_1"),
    )

    lesson = relationship("Lesson", back_populates="resources", foreign_keys=[lesson_id])
    file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])

    @property
    def public_id(self) -> uuid.UUID:
        """Synthetic public UUIDv5 identifier conforming to ADR-002."""
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.lesson_resource.{self.id}")

    @property
    def title(self) -> str:
        """Resource display title from label or underlying file asset."""
        if self.label:
            return self.label
        if self.file_asset:
            return self.file_asset.display_name or self.file_asset.original_filename or "Resource"
        return "Resource"

    @property
    def file_name(self) -> str:
        """Original or display filename."""
        if self.file_asset:
            return self.file_asset.original_filename or self.file_asset.display_name or ""
        return ""

    @property
    def file_size_bytes(self) -> int:
        """Resource file size in bytes."""
        if self.file_asset:
            return self.file_asset.file_size_bytes
        return 0

    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        if self.file_asset and self.file_asset.mime_type:
            return self.file_asset.mime_type
        return "application/octet-stream"

    @property
    def is_video(self) -> bool:
        """Whether resource is a playable video file."""
        return bool(self.file_asset and self.file_asset.is_video)

    @property
    def is_pdf(self) -> bool:
        """Whether resource is a PDF document."""
        return bool(self.file_asset and self.file_asset.is_pdf)

    @property
    def resource_type(self) -> str:
        """Classified resource category: VIDEO, PDF, DOCX, PPTX, ARCHIVE, or DOCUMENT."""
        if self.is_video:
            return "VIDEO"
        if self.is_pdf:
            return "PDF"
        fn = (self.file_name or "").lower()
        mt = (self.mime_type or "").lower()
        if fn.endswith((".docx", ".doc")) or "word" in mt:
            return "DOCX"
        if fn.endswith((".pptx", ".ppt")) or "presentation" in mt or "powerpoint" in mt:
            return "PPTX"
        if fn.endswith((".zip", ".rar", ".tar", ".gz", ".7z")) or "zip" in mt or "compressed" in mt:
            return "ARCHIVE"
        return "DOCUMENT"

    @property
    def file_size_formatted(self) -> str:
        """Formatted human-readable file size."""
        size = self.file_size_bytes
        if not size:
            return "0 B"
        if size >= 1048576:
            return f"{size / (1024 * 1024):.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"


class QuestionRevisionResource(Base):
    """Attached images/assets for a question revision mapping to 'question_revision_resources'."""

    __tablename__ = "question_revision_resources"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    question_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_revisions.id",
            name="fk_question_revision_resources_question_revision_id",
        ),
        nullable=False,
    )
    file_asset_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("file_assets.id", name="fk_question_revision_resources_file_asset_id"),
        nullable=False,
    )
    position = db.Column(
        sa.Integer,
        nullable=False,
        default=1,
        server_default=sa.text("1"),
    )
    resource_role = db.Column(
        sa.String(20),
        nullable=False,
        default="IMAGE",
        server_default=sa.text("'IMAGE'"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "question_revision_id",
            "file_asset_id",
            name="uq_question_revision_resources_question_revision_id_file_asset_id_1",
        ),
        sa.CheckConstraint("position > 0", name="ck_question_revision_resources_1"),
        sa.CheckConstraint(
            "resource_role IN ('IMAGE','ATTACHMENT')", name="ck_question_revision_resources_2"
        ),
    )

    question_revision = relationship("QuestionRevision", foreign_keys=[question_revision_id])
    file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])

    @property
    def revision_id(self) -> int:
        """Alias for question_revision_id conforming to task description."""
        return self.question_revision_id

    @revision_id.setter
    def revision_id(self, value: int) -> None:
        self.question_revision_id = value

    @property
    def asset_id(self) -> int:
        """Alias for file_asset_id conforming to task description."""
        return self.file_asset_id

    @asset_id.setter
    def asset_id(self, value: int) -> None:
        self.file_asset_id = value


class DocumentImportJob(Base):
    """Document parsing workflow job mapping to 'document_import_jobs' table."""

    __tablename__ = "document_import_jobs"

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
        sa.ForeignKey("courses.id", name="fk_document_import_jobs_course_id"),
        nullable=False,
    )
    source_file_asset_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("file_assets.id", name="fk_document_import_jobs_source_file_asset_id"),
        nullable=False,
    )
    requested_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_document_import_jobs_requested_by_user_id"),
        nullable=False,
    )
    draft_assessment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "assessments.id",
            name="fk_document_import_jobs_draft_assessment_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    background_job_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "background_jobs.id",
            name="fk_document_import_jobs_background_job_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    document_type = db.Column(sa.String(8), nullable=False)
    status = db.Column(
        sa.String(24),
        nullable=False,
        default="QUEUED",
        server_default=sa.text("'QUEUED'"),
    )
    parser_version = db.Column(sa.Unicode(100), nullable=False)
    question_count = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    review_required_count = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    started_at = db.Column(UTCDateTime, nullable=True)
    completed_at = db.Column(UTCDateTime, nullable=True)
    last_error = db.Column(sa.Unicode(2000), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint("document_type IN ('DOCX','PDF')", name="ck_document_import_jobs_1"),
        sa.CheckConstraint(
            "status IN ('QUEUED','PROCESSING','REVIEW_REQUIRED','COMPLETED','FAILED','CANCELLED')",
            name="ck_document_import_jobs_2",
        ),
        sa.CheckConstraint("question_count >= 0", name="ck_document_import_jobs_3"),
        sa.CheckConstraint("review_required_count >= 0", name="ck_document_import_jobs_4"),
        sa.Index("ix_import_jobs_course", "course_id", "status"),
    )

    course = relationship("Course", foreign_keys=[course_id])
    source_file_asset = relationship("FileAsset", foreign_keys=[source_file_asset_id])
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    draft_assessment = relationship("Assessment", foreign_keys=[draft_assessment_id])
    questions = relationship(
        "ImportQuestion",
        back_populates="import_job",
        cascade="all, delete-orphan",
        order_by="ImportQuestion.ordinal",
    )

    @property
    def created_by(self) -> int:
        """Alias for requested_by_user_id conforming to task description."""
        return self.requested_by_user_id

    @created_by.setter
    def created_by(self, value: int) -> None:
        self.requested_by_user_id = value

    @property
    def asset_id(self) -> int:
        """Alias for source_file_asset_id conforming to task description."""
        return self.source_file_asset_id

    @asset_id.setter
    def asset_id(self, value: int) -> None:
        self.source_file_asset_id = value


class ImportQuestion(Base):
    """Parsed question draft from document import mapping to 'import_questions' table."""

    __tablename__ = "import_questions"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    import_job_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("document_import_jobs.id", name="fk_import_questions_import_job_id"),
        nullable=False,
    )
    ordinal = db.Column(sa.Integer, nullable=False)
    detected_type = db.Column(sa.String(24), nullable=True)
    content_text = db.Column(NVarCharMax, nullable=False)
    choices_json = db.Column(NVarCharMax, nullable=True)
    detected_answer_json = db.Column(NVarCharMax, nullable=True)
    explanation_text = db.Column(NVarCharMax, nullable=True)
    confidence_score = db.Column(sa.Numeric(5, 4), nullable=False)
    diagnostics_json = db.Column(NVarCharMax, nullable=True)
    review_state = db.Column(
        sa.String(20),
        nullable=False,
        default="READY",
        server_default=sa.text("'READY'"),
    )
    has_broken_resource = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    ai_suggested_answer_json = db.Column(NVarCharMax, nullable=True)
    ai_suggestion_model = db.Column(sa.Unicode(100), nullable=True)
    ai_suggestion_confirmed_at = db.Column(UTCDateTime, nullable=True)
    ai_suggestion_confirmed_by = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_import_questions_ai_suggestion_confirmed_by",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    approved_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "questions.id",
            name="fk_import_questions_approved_question_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    updated_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "import_job_id", "ordinal", name="uq_import_questions_import_job_id_ordinal_1"
        ),
        sa.CheckConstraint("ordinal > 0", name="ck_import_questions_1"),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1", name="ck_import_questions_2"
        ),
        sa.CheckConstraint(
            "review_state IN ('READY','NEEDS_REVIEW','INVALID','ACCEPTED','REJECTED','EDITED')",
            name="ck_import_questions_3",
        ),
        sa.CheckConstraint(
            "choices_json IS NULL OR ISJSON(choices_json)=1", name="ck_import_questions_4"
        ),
        sa.CheckConstraint(
            "detected_answer_json IS NULL OR ISJSON(detected_answer_json)=1",
            name="ck_import_questions_5",
        ),
        sa.CheckConstraint(
            "diagnostics_json IS NULL OR ISJSON(diagnostics_json)=1",
            name="ck_import_questions_6",
        ),
        sa.CheckConstraint(
            "ai_suggested_answer_json IS NULL OR ISJSON(ai_suggested_answer_json)=1",
            name="ck_import_questions_7",
        ),
        sa.Index("ix_import_questions_job", "import_job_id", "review_state"),
    )

    import_job = relationship("DocumentImportJob", back_populates="questions")
    ai_confirmed_by = relationship("User", foreign_keys=[ai_suggestion_confirmed_by])
    approved_question = relationship("Question", foreign_keys=[approved_question_id])

    @property
    def public_id(self) -> uuid.UUID:
        """Synthetic public UUIDv5 identifier conforming to ADR-002."""
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.import_question.{self.id}")


class ImportDuplicateCandidate(Base):
    """Potential duplicates flagged during import mapping to 'import_duplicate_candidates'."""

    __tablename__ = "import_duplicate_candidates"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    import_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "import_questions.id",
            name="fk_import_duplicate_candidates_import_question_id",
        ),
        nullable=False,
    )
    candidate_import_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "import_questions.id",
            name="fk_import_duplicate_candidates_candidate_import_question_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    candidate_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "questions.id",
            name="fk_import_duplicate_candidates_candidate_question_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    similarity_score = db.Column(sa.Numeric(5, 4), nullable=False)
    decision = db.Column(
        sa.String(16),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    decided_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_import_duplicate_candidates_decided_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    decided_at = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "similarity_score >= 0 AND similarity_score <= 1",
            name="ck_import_duplicate_candidates_1",
        ),
        sa.CheckConstraint(
            "decision IN ('PENDING','KEEP','IGNORE','REJECT')",
            name="ck_import_duplicate_candidates_2",
        ),
        sa.CheckConstraint(
            "(candidate_import_question_id IS NOT NULL OR candidate_question_id IS NOT NULL)",
            name="ck_import_duplicate_candidates_3",
        ),
        sa.Index("ix_import_dup_question", "import_question_id", "decision"),
    )

    import_question = relationship("ImportQuestion", foreign_keys=[import_question_id])
    candidate_import_question = relationship(
        "ImportQuestion",
        foreign_keys=[candidate_import_question_id],
    )
    candidate_question = relationship("Question", foreign_keys=[candidate_question_id])
    decided_by = relationship("User", foreign_keys=[decided_by_user_id])

    @property
    def public_id(self) -> uuid.UUID:
        """Synthetic public UUIDv5 identifier conforming to ADR-002."""
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.import_duplicate_candidate.{self.id}")


class ImportQuestionResource(Base):
    """Extracted images for an imported question mapping to 'import_question_resources'."""

    __tablename__ = "import_question_resources"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    import_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "import_questions.id",
            name="fk_import_question_resources_import_question_id",
        ),
        nullable=False,
    )
    file_asset_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "file_assets.id",
            name="fk_import_question_resources_file_asset_id",
        ),
        nullable=False,
    )
    position = db.Column(
        sa.Integer,
        nullable=False,
        default=1,
        server_default=sa.text("1"),
    )
    status = db.Column(
        sa.String(16),
        nullable=False,
        default="READY",
        server_default=sa.text("'READY'"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "import_question_id",
            "file_asset_id",
            name="uq_import_question_resources_import_question_id_file_asset_id_1",
        ),
        sa.CheckConstraint("position > 0", name="ck_import_question_resources_1"),
        sa.CheckConstraint(
            "status IN ('READY','BROKEN','REJECTED')", name="ck_import_question_resources_2"
        ),
    )

    import_question = relationship("ImportQuestion", foreign_keys=[import_question_id])
    file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])
