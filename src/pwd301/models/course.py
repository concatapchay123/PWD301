"""Course and learning domain models for PWD301.

Implements canonical schema tables from sql/002_course_learning.sql:
- courses
- course_prerequisites
- course_completion_rules
- course_change_requests
- lessons
- enrollments
- enrollment_periods
- enrollment_events
- lesson_progress
- course_completion_summaries
"""

from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import relationship, validates

from pwd301.extensions import Base, db
from pwd301.models.types import (
    GUID,
    BigIntPK,
    NVarCharMax,
    RowVersion,
    UTCDateTime,
    utc_now,
)


class Course(Base):
    """Course catalog and lifecycle model mapping to 'courses' table.

    *Lưu ý kiến trúc: Model này sử dụng cơ chế Soft-delete (deleted_at).
    Do DB áp dụng mặc định NO ACTION cho Foreign Keys, tầng Application Service
    phải tự chịu trách nhiệm xử lý cascade data (ẩn/xóa dữ liệu con) bằng code Python.*
    """

    __tablename__ = "courses"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    course_code = db.Column(sa.Unicode(50), nullable=False)
    course_code_normalized = db.Column(
        sa.Unicode(50),
        nullable=False,
    )
    title = db.Column(sa.Unicode(200), nullable=False)
    title_normalized = db.Column(
        sa.Unicode(200),
        nullable=False,
    )
    description = db.Column(NVarCharMax, nullable=True)
    category = db.Column(sa.Unicode(100), nullable=True)
    difficulty = db.Column(sa.String(20), nullable=True)
    owner_instructor_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_courses_owner_instructor_id"),
        nullable=True,
    )
    thumbnail_file_asset_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "file_assets.id",
            name="fk_courses_thumbnail_file_asset_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    status = db.Column(
        sa.String(32),
        nullable=False,
        default="DRAFT",
        server_default=sa.text("'DRAFT'"),
    )
    capacity = db.Column(sa.Integer, nullable=True)
    storage_quota_bytes = db.Column(sa.BigInteger, nullable=True)
    published_at = db.Column(UTCDateTime, nullable=True)
    approved_at = db.Column(UTCDateTime, nullable=True)
    approved_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_courses_approved_by_user_id"),
        nullable=True,
    )
    first_student_enrolled_at = db.Column(UTCDateTime, nullable=True)
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
        sa.ForeignKey("users.id", name="fk_courses_deleted_by_user_id"),
        nullable=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('DRAFT','SUBMITTED_FOR_REVIEW','APPROVED','PUBLISHED','ARCHIVED','TRASH')",
            name="ck_courses_1",
        ),
        sa.CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('BEGINNER','INTERMEDIATE','ADVANCED')",
            name="ck_courses_2",
        ),
        sa.CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_courses_3"),
        sa.CheckConstraint(
            "storage_quota_bytes IS NULL OR storage_quota_bytes > 0",
            name="ck_courses_4",
        ),
        sa.Index("ix_courses_catalog", "status", "category", "difficulty", "title"),
        sa.Index("ix_courses_owner", "owner_instructor_id", "status"),
        sa.Index(
            "ux_courses_course_code_active",
            "course_code_normalized",
            unique=True,
            mssql_where=sa.text("deleted_at IS NULL"),
            sqlite_where=sa.text("deleted_at IS NULL"),
        ),
        sa.Index(
            "ux_courses_title_active",
            "title_normalized",
            unique=True,
            mssql_where=sa.text("deleted_at IS NULL"),
            sqlite_where=sa.text("deleted_at IS NULL"),
        ),
    )

    owner_instructor = relationship(
        "User",
        foreign_keys=[owner_instructor_id],
        back_populates="courses",
    )
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_user_id])
    completion_rule = relationship(
        "CourseCompletionRule",
        uselist=False,
        back_populates="course",
        cascade="all, delete-orphan",
    )
    lessons = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.position",
    )
    enrollments = relationship("Enrollment", back_populates="course")

    @validates("course_code")
    def _validate_course_code(self, key: str, value: str | None) -> str | None:
        if value is not None:
            self.course_code_normalized = value.strip().upper()
        return value

    @validates("course_code_normalized")
    def _validate_course_code_normalized(self, key: str, value: str | None) -> str | None:
        if value is not None:
            return value.strip().upper()
        return value

    @validates("title")
    def _validate_title(self, key: str, value: str | None) -> str | None:
        if value is not None:
            self.title_normalized = value.strip().lower()
        return value

    @validates("title_normalized")
    def _validate_title_normalized(self, key: str, value: str | None) -> str | None:
        if value is not None:
            return value.strip().lower()
        return value


@sa.event.listens_for(Course, "before_insert")
@sa.event.listens_for(Course, "before_update")
def _normalize_course_fields(
    mapper: sa.orm.Mapper[Any],
    connection: sa.Connection,
    target: Course,
) -> None:
    if target.course_code is not None:
        target.course_code_normalized = target.course_code.strip().upper()
    if target.title is not None:
        target.title_normalized = target.title.strip().lower()


class CoursePrerequisite(Base):
    """Course dependency graph junction mapping to 'course_prerequisites' table."""

    __tablename__ = "course_prerequisites"

    course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_course_prerequisites_course_id"),
        primary_key=True,
    )
    prerequisite_course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "courses.id",
            name="fk_course_prerequisites_prerequisite_course_id",
        ),
        primary_key=True,
    )
    created_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_course_prerequisites_created_by_user_id"),
        nullable=False,
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint("course_id <> prerequisite_course_id", name="ck_course_prerequisites_1"),
        sa.Index("ix_course_prereq_reverse", "prerequisite_course_id", "course_id"),
    )

    course = relationship(
        "Course",
        foreign_keys=[course_id],
        backref=sa.orm.backref("prerequisite_links", cascade="all, delete-orphan"),
    )
    prerequisite_course = relationship(
        "Course",
        foreign_keys=[prerequisite_course_id],
        backref=sa.orm.backref("dependent_links", cascade="all, delete-orphan"),
    )
    created_by = relationship("User", foreign_keys=[created_by_user_id])


class CourseCompletionRule(Base):
    """Course completion threshold criteria mapping to 'course_completion_rules' table."""

    __tablename__ = "course_completion_rules"

    course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_course_completion_rules_course_id"),
        primary_key=True,
    )
    require_all_required_lessons = db.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("1"),
    )
    require_required_assessments = db.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("1"),
    )
    minimum_progress_percent = db.Column(sa.Numeric(5, 2), nullable=True)
    updated_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_course_completion_rules_updated_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
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
        sa.CheckConstraint(
            "minimum_progress_percent IS NULL OR "
            "(minimum_progress_percent >= 0 AND minimum_progress_percent <= 100)",
            name="ck_course_completion_rules_1",
        ),
    )

    course = relationship("Course", back_populates="completion_rule")
    updated_by = relationship("User", foreign_keys=[updated_by_user_id])


class CourseChangeRequest(Base):
    """Staged course alteration proposals mapping to 'course_change_requests' table."""

    __tablename__ = "course_change_requests"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_course_change_requests_course_id"),
        nullable=False,
    )
    requested_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_course_change_requests_requested_by_user_id"),
        nullable=False,
    )
    change_type = db.Column(sa.String(32), nullable=False)
    target_type = db.Column(sa.String(32), nullable=False)
    target_id = db.Column(sa.BigInteger, nullable=True)
    proposed_payload_json = db.Column(NVarCharMax, nullable=False)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    reviewed_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_course_change_requests_reviewed_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    review_reason = db.Column(sa.Unicode(1000), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    reviewed_at = db.Column(UTCDateTime, nullable=True)
    applied_at = db.Column(UTCDateTime, nullable=True)
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "change_type IN ('COURSE_METADATA','LESSON_STRUCTURE','LESSON_CONTENT',"
            "'COMPLETION_RULE','PREREQUISITE','OTHER')",
            name="ck_course_change_requests_1",
        ),
        sa.CheckConstraint(
            "target_type IN ('COURSE','LESSON','RULE','PREREQUISITE')",
            name="ck_course_change_requests_2",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','APPROVED','REJECTED','CANCELLED','APPLIED')",
            name="ck_course_change_requests_3",
        ),
        sa.CheckConstraint("ISJSON(proposed_payload_json)=1", name="ck_course_change_requests_4"),
        sa.Index(
            "ix_course_changes_pending",
            "status",
            "created_at",
            mssql_where=sa.text("status='PENDING'"),
            sqlite_where=sa.text("status='PENDING'"),
        ),
        sa.Index("ix_course_changes_course", "course_id", "created_at"),
    )

    course = relationship("Course", foreign_keys=[course_id], backref="change_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])


class Lesson(Base):
    """Lesson content and sequence unit mapping to 'lessons' table.

    *Lưu ý kiến trúc: Model này sử dụng cơ chế Soft-delete (deleted_at).
    Do DB áp dụng mặc định NO ACTION cho Foreign Keys, tầng Application Service
    phải tự chịu trách nhiệm xử lý cascade data (ẩn/xóa dữ liệu con) bằng code Python.*
    """

    __tablename__ = "lessons"

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
        sa.ForeignKey("courses.id", name="fk_lessons_course_id"),
        nullable=False,
    )
    title = db.Column(sa.Unicode(200), nullable=False)
    summary = db.Column(sa.Unicode(1000), nullable=True)
    markdown_content = db.Column(NVarCharMax, nullable=False)
    position = db.Column(sa.Integer, nullable=False)
    estimated_duration_minutes = db.Column(sa.Integer, nullable=True)
    minimum_completion_seconds = db.Column(
        sa.Integer,
        nullable=False,
        default=30,
        server_default=sa.text("30"),
    )
    viewed_fraction_required = db.Column(
        sa.Numeric(5, 4),
        nullable=False,
        default=0.8000,
        server_default=sa.text("0.8000"),
    )
    required_for_periods_starting_at = db.Column(UTCDateTime, nullable=True)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="DRAFT",
        server_default=sa.text("'DRAFT'"),
    )
    published_at = db.Column(UTCDateTime, nullable=True)
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
        sa.ForeignKey("users.id", name="fk_lessons_deleted_by_user_id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        sa.UniqueConstraint("course_id", "position", name="uq_lessons_course_id_position_2"),
        sa.CheckConstraint("position > 0", name="ck_lessons_1"),
        sa.CheckConstraint(
            "estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0",
            name="ck_lessons_2",
        ),
        sa.CheckConstraint("minimum_completion_seconds >= 0", name="ck_lessons_3"),
        sa.CheckConstraint(
            "viewed_fraction_required >= 0 AND viewed_fraction_required <= 1",
            name="ck_lessons_4",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','PUBLISHED','HIDDEN','TRASH','HISTORICAL')",
            name="ck_lessons_5",
        ),
        sa.Index("ix_lessons_course_status_position", "course_id", "status", "position"),
    )

    course = relationship("Course", back_populates="lessons")
    deleted_by = relationship("User", foreign_keys=[deleted_by_user_id])


class Enrollment(Base):
    """Student logical enrollment record mapping to 'enrollments' table."""

    __tablename__ = "enrollments"

    # Transient runtime flag indicating initial creation (not mapped to database)
    _is_new: bool = False

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    student_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_enrollments_student_user_id"),
        nullable=False,
    )
    course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_enrollments_course_id"),
        nullable=False,
    )
    status = db.Column(
        sa.String(24),
        nullable=False,
        default="ACTIVE",
        server_default=sa.text("'ACTIVE'"),
    )
    current_period_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "enrollment_periods.id",
            name="fk_enrollments_current_period_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    current_progress_percent = db.Column(
        sa.Numeric(5, 2),
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    enrolled_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    left_at = db.Column(UTCDateTime, nullable=True)
    completed_at = db.Column(UTCDateTime, nullable=True)
    detail_retention_due_at = db.Column(UTCDateTime, nullable=True)
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
            "student_user_id", "course_id", name="uq_enrollments_student_user_id_course_id_2"
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE','LEFT','COMPLETED','RETENTION_PENDING','DETAIL_PURGED')",
            name="ck_enrollments_1",
        ),
        sa.CheckConstraint(
            "current_progress_percent >= 0 AND current_progress_percent <= 100",
            name="ck_enrollments_2",
        ),
        sa.Index("ix_enrollments_course_status", "course_id", "status", "student_user_id"),
        sa.Index("ix_enrollments_student_status", "student_user_id", "status", "course_id"),
        sa.Index(
            "ix_enrollments_retention",
            "detail_retention_due_at",
            "status",
            mssql_where=sa.text("detail_retention_due_at IS NOT NULL"),
            sqlite_where=sa.text("detail_retention_due_at IS NOT NULL"),
        ),
    )

    student = relationship(
        "User",
        foreign_keys=[student_user_id],
        back_populates="enrollments",
    )
    course = relationship(
        "Course",
        foreign_keys=[course_id],
        back_populates="enrollments",
    )
    periods = relationship(
        "EnrollmentPeriod",
        back_populates="enrollment",
        foreign_keys="EnrollmentPeriod.enrollment_id",
        cascade="all, delete-orphan",
    )
    current_period = relationship(
        "EnrollmentPeriod",
        foreign_keys=[current_period_id],
        post_update=True,
    )


class EnrollmentPeriod(Base):
    """Learning period segment mapping to 'enrollment_periods' table."""

    __tablename__ = "enrollment_periods"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    enrollment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("enrollments.id", name="fk_enrollment_periods_enrollment_id"),
        nullable=False,
    )
    period_no = db.Column(sa.Integer, nullable=False)
    started_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    left_at = db.Column(UTCDateTime, nullable=True)
    completed_at = db.Column(UTCDateTime, nullable=True)
    retention_due_at = db.Column(UTCDateTime, nullable=True)
    detail_purged_at = db.Column(UTCDateTime, nullable=True)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="ACTIVE",
        server_default=sa.text("'ACTIVE'"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "enrollment_id", "period_no", name="uq_enrollment_periods_enrollment_id_period_no_1"
        ),
        sa.CheckConstraint("period_no > 0", name="ck_enrollment_periods_1"),
        sa.CheckConstraint(
            "status IN ('ACTIVE','LEFT','COMPLETED','PURGED')", name="ck_enrollment_periods_2"
        ),
        sa.Index(
            "ix_enrollment_periods_retention",
            "retention_due_at",
            "status",
            mssql_where=sa.text("retention_due_at IS NOT NULL"),
            sqlite_where=sa.text("retention_due_at IS NOT NULL"),
        ),
        sa.Index("ix_enrollment_periods_enrollment", "enrollment_id", "period_no"),
        sa.Index(
            "ux_enrollment_period_active",
            "enrollment_id",
            unique=True,
            mssql_where=sa.text("status='ACTIVE'"),
            sqlite_where=sa.text("status='ACTIVE'"),
        ),
    )

    enrollment = relationship(
        "Enrollment",
        foreign_keys=[enrollment_id],
        back_populates="periods",
    )


class EnrollmentEvent(Base):
    """Enrollment lifecycle audit trail mapping to 'enrollment_events' table."""

    __tablename__ = "enrollment_events"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    enrollment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("enrollments.id", name="fk_enrollment_events_enrollment_id"),
        nullable=False,
    )
    period_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "enrollment_periods.id",
            name="fk_enrollment_events_period_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    event_type = db.Column(sa.String(24), nullable=False)
    actor_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_enrollment_events_actor_user_id", ondelete="SET NULL"),
        nullable=True,
    )
    reason = db.Column(sa.Unicode(500), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "event_type IN ('ENROLLED','LEFT','REENROLLED','COMPLETED','DETAIL_PURGED')",
            name="ck_enrollment_events_1",
        ),
        sa.Index("ix_enrollment_events_enrollment", "enrollment_id", "created_at"),
    )

    enrollment = relationship("Enrollment", foreign_keys=[enrollment_id])
    period = relationship("EnrollmentPeriod", foreign_keys=[period_id])
    actor = relationship("User", foreign_keys=[actor_user_id])


class LessonProgress(Base):
    """Per-period lesson engagement tracking mapping to 'lesson_progress' table."""

    __tablename__ = "lesson_progress"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    enrollment_period_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("enrollment_periods.id", name="fk_lesson_progress_enrollment_period_id"),
        nullable=False,
    )
    lesson_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("lessons.id", name="fk_lesson_progress_lesson_id"),
        nullable=False,
    )
    seconds_spent = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    max_view_fraction = db.Column(
        sa.Numeric(5, 4),
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    last_activity_at = db.Column(UTCDateTime, nullable=True)
    completed_at = db.Column(UTCDateTime, nullable=True)
    completion_rule_snapshot_json = db.Column(NVarCharMax, nullable=True)
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
            "enrollment_period_id",
            "lesson_id",
            name="uq_lesson_progress_enrollment_period_id_lesson_id_1",
        ),
        sa.CheckConstraint("seconds_spent >= 0", name="ck_lesson_progress_1"),
        sa.CheckConstraint(
            "max_view_fraction >= 0 AND max_view_fraction <= 1", name="ck_lesson_progress_2"
        ),
        sa.CheckConstraint(
            "completion_rule_snapshot_json IS NULL OR ISJSON(completion_rule_snapshot_json)=1",
            name="ck_lesson_progress_3",
        ),
        sa.Index("ix_lesson_progress_period_complete", "enrollment_period_id", "completed_at"),
    )

    period = relationship("EnrollmentPeriod", foreign_keys=[enrollment_period_id])
    lesson = relationship("Lesson", foreign_keys=[lesson_id])


class CourseCompletionSummary(Base):
    """Durable completion & prerequisite status mapping to 'course_completion_summaries' table."""

    __tablename__ = "course_completion_summaries"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    student_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_course_completion_summaries_student_user_id"),
        nullable=False,
    )
    course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_course_completion_summaries_course_id"),
        nullable=False,
    )
    ever_completed = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    first_completed_at = db.Column(UTCDateTime, nullable=True)
    latest_completed_at = db.Column(UTCDateTime, nullable=True)
    final_aggregate_score = db.Column(sa.Numeric(9, 4), nullable=True)
    prerequisite_eligible = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    source_period_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "enrollment_periods.id",
            name="fk_course_completion_summaries_source_period_id",
            ondelete="SET NULL",
        ),
        nullable=True,
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
            "student_user_id",
            "course_id",
            name="uq_course_completion_summaries_student_user_id_course_id_1",
        ),
        sa.CheckConstraint(
            "final_aggregate_score IS NULL OR final_aggregate_score >= 0",
            name="ck_course_completion_summaries_1",
        ),
        sa.Index(
            "ix_completion_summary_student",
            "student_user_id",
            "prerequisite_eligible",
            "course_id",
        ),
    )

    student = relationship("User", foreign_keys=[student_user_id])
    course = relationship("Course", foreign_keys=[course_id])
    source_period = relationship("EnrollmentPeriod", foreign_keys=[source_period_id])
