"""Assessment attempt and regrading domain models for PWD301.

Implements canonical schema tables from sql/005_attempt_regrade.sql:
- assessment_attempts
- attempt_questions
- attempt_choice_snapshots
- attempt_answers
- attempt_answer_choices
- attempt_answer_events
- attempt_question_grades
- attempt_question_grade_history
- assessment_results
- assessment_result_history
- question_corrections
- regrade_jobs
- regrade_items
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


class AssessmentAttempt(Base):
    """Student attempt session mapping to canonical 'assessment_attempts' table."""

    __tablename__ = "assessment_attempts"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    assessment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessments.id", name="fk_assessment_attempts_assessment_id"),
        nullable=False,
    )
    enrollment_period_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "enrollment_periods.id",
            name="fk_assessment_attempts_enrollment_period_id",
        ),
        nullable=False,
    )
    student_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_assessment_attempts_student_user_id"),
        nullable=False,
    )
    attempt_number = db.Column(sa.Integer, nullable=False)
    status = db.Column(sa.String(28), nullable=False)
    started_at = db.Column(UTCDateTime, nullable=True)
    deadline_at = db.Column(UTCDateTime, nullable=True)
    submitted_at = db.Column(UTCDateTime, nullable=True)
    finalized_at = db.Column(UTCDateTime, nullable=True)
    graded_at = db.Column(UTCDateTime, nullable=True)
    submission_idempotency_key = db.Column(GUID, nullable=True)
    editor_session_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "auth_sessions.id",
            name="fk_assessment_attempts_editor_session_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    lease_token_hash = db.Column(Binary32, nullable=True)
    lease_acquired_at = db.Column(UTCDateTime, nullable=True)
    lease_expires_at = db.Column(UTCDateTime, nullable=True)
    last_heartbeat_at = db.Column(UTCDateTime, nullable=True)
    lease_epoch = db.Column(
        sa.Integer,
        nullable=False,
        default=1,
        server_default=sa.text("1"),
    )
    is_detail_purged = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    detail_purged_at = db.Column(UTCDateTime, nullable=True)
    cancel_reason = db.Column(sa.Unicode(1000), nullable=True)
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
            "assessment_id",
            "student_user_id",
            "attempt_number",
            name="uq_assessment_attempts_assessment_id_student_user_id_attempt_number_2",
        ),
        sa.CheckConstraint("attempt_number > 0", name="ck_assessment_attempts_1"),
        sa.CheckConstraint(
            "status IN ('CREATED','IN_PROGRESS','SUBMITTED','EXPIRED','CANCELLED',"
            "'PENDING_GRADING','GRADED')",
            name="ck_assessment_attempts_2",
        ),
        sa.CheckConstraint(
            "deadline_at IS NULL OR started_at IS NULL OR deadline_at >= started_at",
            name="ck_assessment_attempts_3",
        ),
        sa.Index(
            "ix_attempts_student_assessment",
            "student_user_id",
            "assessment_id",
            "attempt_number",
        ),
        sa.Index("ix_attempts_assessment_status", "assessment_id", "status", "started_at"),
        sa.Index("ix_attempts_period_status", "enrollment_period_id", "status"),
        sa.Index(
            "ix_attempts_lease_expiry",
            "lease_expires_at",
            "status",
            mssql_where=sa.text("status='IN_PROGRESS'"),
            sqlite_where=sa.text("status='IN_PROGRESS'"),
        ),
        sa.Index(
            "ux_attempt_submit_key",
            "submission_idempotency_key",
            unique=True,
            mssql_where=sa.text("submission_idempotency_key IS NOT NULL"),
            sqlite_where=sa.text("submission_idempotency_key IS NOT NULL"),
        ),
        sa.Index(
            "ux_attempt_single_active",
            "assessment_id",
            "student_user_id",
            unique=True,
            mssql_where=sa.text("status='IN_PROGRESS'"),
            sqlite_where=sa.text("status='IN_PROGRESS'"),
        ),
    )

    assessment = relationship("Assessment", back_populates="attempts")
    enrollment_period = relationship("EnrollmentPeriod", foreign_keys=[enrollment_period_id])
    student = relationship("User", foreign_keys=[student_user_id])
    editor_session = relationship("AuthSession", foreign_keys=[editor_session_id])
    attempt_questions = relationship(
        "AttemptQuestion",
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="AttemptQuestion.position",
    )
    result = relationship(
        "AssessmentResult",
        uselist=False,
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class AttemptQuestion(Base):
    """Frozen question presentation for an attempt mapping to 'attempt_questions' table."""

    __tablename__ = "attempt_questions"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    attempt_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessment_attempts.id", name="fk_attempt_questions_attempt_id"),
        nullable=False,
    )
    source_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("questions.id", name="fk_attempt_questions_source_question_id"),
        nullable=False,
    )
    source_question_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_revisions.id",
            name="fk_attempt_questions_source_question_revision_id",
        ),
        nullable=False,
    )
    section_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "assessment_sections.id",
            name="fk_attempt_questions_section_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    position = db.Column(sa.Integer, nullable=False)
    question_type_snapshot = db.Column(sa.String(24), nullable=False)
    content_snapshot = db.Column(NVarCharMax, nullable=False)
    explanation_snapshot = db.Column(NVarCharMax, nullable=True)
    points_assigned = db.Column(sa.Numeric(9, 4), nullable=False)
    choice_shuffle_applied = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    question_changed_after_start_at = db.Column(UTCDateTime, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "attempt_id", "position", name="uq_attempt_questions_attempt_id_position_1"
        ),
        sa.UniqueConstraint(
            "attempt_id",
            "source_question_id",
            name="uq_attempt_questions_attempt_id_source_question_id_2",
        ),
        sa.CheckConstraint("position > 0", name="ck_attempt_questions_1"),
        sa.CheckConstraint("points_assigned > 0", name="ck_attempt_questions_2"),
        sa.CheckConstraint(
            "question_type_snapshot IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE',"
            "'SHORT_ANSWER','ESSAY')",
            name="ck_attempt_questions_3",
        ),
        sa.Index("ix_attempt_questions_attempt", "attempt_id", "position"),
        sa.Index("ix_attempt_questions_source", "source_question_id", "attempt_id"),
    )

    attempt = relationship("AssessmentAttempt", back_populates="attempt_questions")
    source_question = relationship("Question", foreign_keys=[source_question_id])
    source_question_revision = relationship(
        "QuestionRevision",
        foreign_keys=[source_question_revision_id],
    )
    section = relationship("AssessmentSection", foreign_keys=[section_id])
    choice_snapshots = relationship(
        "AttemptChoiceSnapshot",
        back_populates="attempt_question",
        cascade="all, delete-orphan",
        order_by="AttemptChoiceSnapshot.position",
    )
    current_answer = relationship(
        "AttemptAnswer",
        uselist=False,
        back_populates="attempt_question",
        cascade="all, delete-orphan",
    )
    current_grade = relationship(
        "AttemptQuestionGrade",
        uselist=False,
        back_populates="attempt_question",
        cascade="all, delete-orphan",
    )


class AttemptChoiceSnapshot(Base):
    """Frozen multiple-choice presentation snapshot mapping to 'attempt_choice_snapshots'."""

    __tablename__ = "attempt_choice_snapshots"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    attempt_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "attempt_questions.id",
            name="fk_attempt_choice_snapshots_attempt_question_id",
        ),
        nullable=False,
    )
    source_choice_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_revision_choices.id",
            name="fk_attempt_choice_snapshots_source_choice_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    choice_key_snapshot = db.Column(GUID, nullable=False)
    content_snapshot = db.Column(NVarCharMax, nullable=False)
    position = db.Column(sa.Integer, nullable=False)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "attempt_question_id",
            "position",
            name="uq_attempt_choice_snapshots_attempt_question_id_position_1",
        ),
        sa.UniqueConstraint(
            "attempt_question_id",
            "choice_key_snapshot",
            name="uq_attempt_choice_snapshots_attempt_question_id_choice_key_snapshot_2",
        ),
        sa.CheckConstraint("position > 0", name="ck_attempt_choice_snapshots_1"),
        sa.Index("ix_attempt_choice_snapshots_question", "attempt_question_id", "position"),
    )

    attempt_question = relationship("AttemptQuestion", back_populates="choice_snapshots")
    source_choice = relationship("QuestionRevisionChoice", foreign_keys=[source_choice_id])


class AttemptAnswer(Base):
    """Current candidate answer mapping to canonical 'attempt_answers' table."""

    __tablename__ = "attempt_answers"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    attempt_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("attempt_questions.id", name="fk_attempt_answers_attempt_question_id"),
        nullable=False,
        unique=True,
    )
    answer_text = db.Column(NVarCharMax, nullable=True)
    answer_version = db.Column(
        sa.BigInteger,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    last_client_sequence = db.Column(
        sa.BigInteger,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    last_change_id = db.Column(GUID, nullable=True)
    saved_at = db.Column(UTCDateTime, nullable=True)
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint("answer_version >= 0", name="ck_attempt_answers_1"),
        sa.CheckConstraint("last_client_sequence >= 0", name="ck_attempt_answers_2"),
    )

    attempt_question = relationship("AttemptQuestion", back_populates="current_answer")
    selected_choices = relationship(
        "AttemptChoiceSnapshot",
        secondary="attempt_answer_choices",
        backref="selected_in_answers",
    )


class AttemptAnswerChoice(Base):
    """Junction table mapping selected choices to 'attempt_answer_choices'."""

    __tablename__ = "attempt_answer_choices"

    attempt_answer_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "attempt_answers.id",
            name="fk_attempt_answer_choices_attempt_answer_id",
        ),
        primary_key=True,
    )
    attempt_choice_snapshot_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "attempt_choice_snapshots.id",
            name="fk_attempt_answer_choices_attempt_choice_snapshot_id",
        ),
        primary_key=True,
    )


class AttemptAnswerEvent(Base):
    """Immutable sequence log for student autosave edits mapping to 'attempt_answer_events'."""

    __tablename__ = "attempt_answer_events"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    attempt_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "attempt_questions.id",
            name="fk_attempt_answer_events_attempt_question_id",
        ),
        nullable=False,
    )
    change_id = db.Column(GUID, nullable=False)
    client_sequence = db.Column(sa.BigInteger, nullable=False)
    server_answer_version = db.Column(sa.BigInteger, nullable=True)
    payload_json = db.Column(NVarCharMax, nullable=False)
    received_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    accepted = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    rejection_reason = db.Column(sa.String(40), nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "attempt_question_id",
            "change_id",
            name="uq_attempt_answer_events_attempt_question_id_change_id_1",
        ),
        sa.CheckConstraint("client_sequence >= 0", name="ck_attempt_answer_events_1"),
        sa.CheckConstraint(
            "payload_json IS NOT NULL AND ISJSON(payload_json)=1",
            name="ck_attempt_answer_events_2",
        ),
        sa.CheckConstraint(
            "rejection_reason IS NULL OR "
            "rejection_reason IN ('STALE','LEASE_INVALID','AFTER_DEADLINE','INVALID_PAYLOAD')",
            name="ck_attempt_answer_events_3",
        ),
        sa.Index("ix_attempt_answer_events_order", "attempt_question_id", "client_sequence"),
    )

    attempt_question = relationship("AttemptQuestion", foreign_keys=[attempt_question_id])


class AttemptQuestionGrade(Base):
    """Current evaluation score for an attempt question mapping to 'attempt_question_grades'."""

    __tablename__ = "attempt_question_grades"

    attempt_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "attempt_questions.id",
            name="fk_attempt_question_grades_attempt_question_id",
        ),
        primary_key=True,
    )
    awarded_points = db.Column(
        sa.Numeric(9, 4),
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    grading_status = db.Column(sa.String(20), nullable=False)
    grading_rule = db.Column(sa.String(32), nullable=False)
    graded_against_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_revisions.id",
            name="fk_attempt_question_grades_graded_against_revision_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    graded_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_attempt_question_grades_graded_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    graded_at = db.Column(UTCDateTime, nullable=True)
    manual_reason = db.Column(sa.Unicode(1000), nullable=True)
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint("awarded_points >= 0", name="ck_attempt_question_grades_1"),
        sa.CheckConstraint(
            "grading_status IN ('PENDING','AUTO_GRADED','MANUAL_GRADED','FULL_CREDIT')",
            name="ck_attempt_question_grades_2",
        ),
        sa.CheckConstraint(
            "grading_rule IN ('ORIGINAL','ANSWER_CORRECTION','CONTENT_FULL_CREDIT','MANUAL')",
            name="ck_attempt_question_grades_3",
        ),
        sa.Index(
            "ix_question_grades_pending",
            "grading_status",
            "graded_at",
            mssql_where=sa.text("grading_status='PENDING'"),
            sqlite_where=sa.text("grading_status='PENDING'"),
        ),
    )

    attempt_question = relationship("AttemptQuestion", back_populates="current_grade")
    graded_against_revision = relationship(
        "QuestionRevision",
        foreign_keys=[graded_against_revision_id],
    )
    graded_by_user = relationship("User", foreign_keys=[graded_by_user_id])


class AttemptQuestionGradeHistory(Base):
    """Audit trail of all grade evaluations mapping to 'attempt_question_grade_history'."""

    __tablename__ = "attempt_question_grade_history"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    attempt_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "attempt_questions.id",
            name="fk_attempt_question_grade_history_attempt_question_id",
        ),
        nullable=False,
    )
    old_points = db.Column(sa.Numeric(9, 4), nullable=True)
    new_points = db.Column(sa.Numeric(9, 4), nullable=False)
    reason_code = db.Column(sa.String(32), nullable=False)
    reason = db.Column(sa.Unicode(1000), nullable=True)
    actor_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_attempt_question_grade_history_actor_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    question_correction_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_corrections.id",
            name="fk_attempt_question_grade_history_question_correction_id",
            use_alter=True,
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

    __table_args__ = (
        sa.CheckConstraint("new_points >= 0", name="ck_attempt_question_grade_history_1"),
        sa.CheckConstraint(
            "reason_code IN ('INITIAL','AUTO_REGRADE','FULL_CREDIT','MANUAL_REVISION')",
            name="ck_attempt_question_grade_history_2",
        ),
        sa.Index("ix_attempt_grade_history_question", "attempt_question_id", "created_at"),
    )

    attempt_question = relationship("AttemptQuestion", foreign_keys=[attempt_question_id])
    actor = relationship("User", foreign_keys=[actor_user_id])
    question_correction = relationship(
        "QuestionCorrection",
        foreign_keys=[question_correction_id],
    )


class AssessmentResult(Base):
    """Aggregate result snapshot for an attempt mapping to 'assessment_results' table."""

    __tablename__ = "assessment_results"

    attempt_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessment_attempts.id", name="fk_assessment_results_attempt_id"),
        primary_key=True,
    )
    raw_score = db.Column(
        sa.Numeric(12, 4),
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    max_score = db.Column(sa.Numeric(12, 4), nullable=False)
    percent_score = db.Column(sa.Numeric(7, 4), nullable=True)
    passed = db.Column(sa.Boolean, nullable=True)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    released_at = db.Column(UTCDateTime, nullable=True)
    graded_at = db.Column(UTCDateTime, nullable=True)
    updated_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint("raw_score >= 0", name="ck_assessment_results_1"),
        sa.CheckConstraint("max_score > 0", name="ck_assessment_results_2"),
        sa.CheckConstraint(
            "percent_score IS NULL OR (percent_score >= 0 AND percent_score <= 100)",
            name="ck_assessment_results_3",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','FINAL','RELEASED')", name="ck_assessment_results_4"
        ),
        sa.Index("ix_assessment_results_status", "status", "attempt_id"),
    )

    attempt = relationship("AssessmentAttempt", back_populates="result")


class AssessmentResultHistory(Base):
    """Historical record of attempt score changes mapping to 'assessment_result_history'."""

    __tablename__ = "assessment_result_history"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    attempt_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessment_attempts.id", name="fk_assessment_result_history_attempt_id"),
        nullable=False,
    )
    old_score = db.Column(sa.Numeric(12, 4), nullable=True)
    new_score = db.Column(sa.Numeric(12, 4), nullable=False)
    old_percent = db.Column(sa.Numeric(7, 4), nullable=True)
    new_percent = db.Column(sa.Numeric(7, 4), nullable=True)
    reason_code = db.Column(sa.String(32), nullable=False)
    reason = db.Column(sa.Unicode(1000), nullable=False)
    actor_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_assessment_result_history_actor_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    regrade_job_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "regrade_jobs.id",
            name="fk_assessment_result_history_regrade_job_id",
            use_alter=True,
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

    __table_args__ = (
        sa.CheckConstraint("new_score >= 0", name="ck_assessment_result_history_1"),
        sa.CheckConstraint(
            "reason_code IN ('INITIAL','REGRADE','MANUAL','CORRECTION')",
            name="ck_assessment_result_history_2",
        ),
        sa.Index("ix_assessment_result_history_attempt", "attempt_id", "created_at"),
    )

    attempt = relationship("AssessmentAttempt", foreign_keys=[attempt_id])
    actor = relationship("User", foreign_keys=[actor_user_id])
    regrade_job = relationship("RegradeJob", foreign_keys=[regrade_job_id])


class QuestionCorrection(Base):
    """Correction incident triggering regrading mapping to 'question_corrections' table."""

    __tablename__ = "question_corrections"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("questions.id", name="fk_question_corrections_question_id"),
        nullable=False,
    )
    from_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("question_revisions.id", name="fk_question_corrections_from_revision_id"),
        nullable=False,
    )
    to_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("question_revisions.id", name="fk_question_corrections_to_revision_id"),
        nullable=False,
        unique=True,
    )
    correction_type = db.Column(sa.String(24), nullable=False)
    effective_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    reason = db.Column(sa.Unicode(1000), nullable=False)
    actor_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_question_corrections_actor_user_id"),
        nullable=False,
    )
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "correction_type IN ('ANSWER_ONLY','CONTENT_OR_CHOICES')",
            name="ck_question_corrections_1",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','RUNNING','APPLIED','FAILED','SUPERSEDED')",
            name="ck_question_corrections_2",
        ),
        sa.Index("ix_question_corrections_question", "question_id", "status"),
    )

    question = relationship("Question", foreign_keys=[question_id])
    from_revision = relationship("QuestionRevision", foreign_keys=[from_revision_id])
    to_revision = relationship("QuestionRevision", foreign_keys=[to_revision_id])
    actor = relationship("User", foreign_keys=[actor_user_id])


class RegradeJob(Base):
    """Batch regrading operation job mapping to canonical 'regrade_jobs' table."""

    __tablename__ = "regrade_jobs"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    question_correction_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_corrections.id",
            name="fk_regrade_jobs_question_correction_id",
        ),
        nullable=False,
        unique=True,
    )
    background_job_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "background_jobs.id",
            name="fk_regrade_jobs_background_job_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="QUEUED",
        server_default=sa.text("'QUEUED'"),
    )
    total_items = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    processed_items = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    changed_results = db.Column(
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
        sa.CheckConstraint(
            "status IN ('QUEUED','RUNNING','PARTIAL','COMPLETED','FAILED','CANCELLED')",
            name="ck_regrade_jobs_1",
        ),
        sa.CheckConstraint("total_items >= 0", name="ck_regrade_jobs_2"),
        sa.CheckConstraint("processed_items >= 0", name="ck_regrade_jobs_3"),
        sa.CheckConstraint("changed_results >= 0", name="ck_regrade_jobs_4"),
        sa.Index("ix_regrade_jobs_status", "status", "created_at"),
    )

    question_correction = relationship(
        "QuestionCorrection",
        foreign_keys=[question_correction_id],
    )
    items = relationship("RegradeItem", back_populates="regrade_job", cascade="all, delete-orphan")


class RegradeItem(Base):
    """Individual attempt affected by a regrade job mapping to 'regrade_items' table."""

    __tablename__ = "regrade_items"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    regrade_job_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("regrade_jobs.id", name="fk_regrade_items_regrade_job_id"),
        nullable=False,
    )
    attempt_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessment_attempts.id", name="fk_regrade_items_attempt_id"),
        nullable=False,
    )
    status = db.Column(
        sa.String(16),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    old_score = db.Column(sa.Numeric(12, 4), nullable=True)
    new_score = db.Column(sa.Numeric(12, 4), nullable=True)
    skip_reason = db.Column(sa.String(40), nullable=True)
    attempt_count = db.Column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    processed_at = db.Column(UTCDateTime, nullable=True)
    last_error = db.Column(sa.Unicode(2000), nullable=True)
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "regrade_job_id", "attempt_id", name="uq_regrade_items_regrade_job_id_attempt_id_1"
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','PROCESSING','COMPLETED','SKIPPED','FAILED')",
            name="ck_regrade_items_1",
        ),
        sa.CheckConstraint(
            "skip_reason IS NULL OR skip_reason IN ('DETAIL_PURGED','NOT_AFFECTED','CANCELLED')",
            name="ck_regrade_items_2",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_regrade_items_3"),
        sa.Index("ix_regrade_items_job_status", "regrade_job_id", "status"),
    )

    regrade_job = relationship("RegradeJob", foreign_keys=[regrade_job_id], back_populates="items")
    attempt = relationship("AssessmentAttempt", foreign_keys=[attempt_id])
