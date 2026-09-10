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

    lesson = relationship("Lesson", foreign_keys=[lesson_id])
    file_asset = relationship("FileAsset", foreign_keys=[file_asset_id])

    @property
    def public_id(self) -> uuid.UUID:
        """Synthetic public UUIDv5 identifier conforming to ADR-002."""
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.lesson_resource.{self.id}")


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
