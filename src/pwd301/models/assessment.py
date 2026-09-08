"""Assessment structure domain models for PWD301.

Implements canonical schema tables from sql/004_assessment.sql:
- assessments
- assessment_sections
- assessment_question_assignments
- assessment_blueprints
- assessment_blueprint_rules
- assessment_question_pool
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


class Assessment(Base):
    """Assessment configuration model mapping to canonical 'assessments' table."""

    __tablename__ = "assessments"

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
        sa.ForeignKey("courses.id", name="fk_assessments_course_id"),
        nullable=False,
    )
    creator_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_assessments_creator_user_id"),
        nullable=True,
    )
    title = db.Column(sa.Unicode(200), nullable=False)
    description = db.Column(NVarCharMax, nullable=True)
    assessment_type = db.Column(sa.String(20), nullable=False)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="DRAFT",
        server_default=sa.text("'DRAFT'"),
    )
    open_at = db.Column(UTCDateTime, nullable=True)
    close_at = db.Column(UTCDateTime, nullable=True)
    time_limit_minutes = db.Column(sa.Integer, nullable=True)
    attempt_limit = db.Column(sa.Integer, nullable=True)
    scoring_policy = db.Column(
        sa.String(20),
        nullable=False,
        default="HIGHEST",
        server_default=sa.text("'HIGHEST'"),
    )
    passing_percent = db.Column(sa.Numeric(5, 2), nullable=True)
    is_required_for_completion = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    shuffle_questions = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    shuffle_choices = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    score_release_policy = db.Column(
        sa.String(24),
        nullable=False,
        default="IMMEDIATE",
        server_default=sa.text("'IMMEDIATE'"),
    )
    answer_visibility_policy = db.Column(
        sa.String(32),
        nullable=False,
        default="AFTER_CLOSE",
        server_default=sa.text("'AFTER_CLOSE'"),
    )
    random_question_count = db.Column(sa.Integer, nullable=True)
    published_at = db.Column(UTCDateTime, nullable=True)
    first_attempt_started_at = db.Column(UTCDateTime, nullable=True)
    cancelled_at = db.Column(UTCDateTime, nullable=True)
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
    deleted_at = db.Column(UTCDateTime, nullable=True)
    restore_until = db.Column(UTCDateTime, nullable=True)
    deleted_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_assessments_deleted_by_user_id"),
        nullable=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "assessment_type IN ('PRACTICE','QUIZ','MIDTERM','FINAL','PLACEMENT')",
            name="ck_assessments_1",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','PUBLISHED','CANCELLED','ARCHIVED','TRASH')",
            name="ck_assessments_2",
        ),
        sa.CheckConstraint(
            "time_limit_minutes IS NULL OR time_limit_minutes > 0",
            name="ck_assessments_3",
        ),
        sa.CheckConstraint("attempt_limit IS NULL OR attempt_limit > 0", name="ck_assessments_4"),
        sa.CheckConstraint(
            "scoring_policy IN ('FIRST','LATEST','HIGHEST','AVERAGE')",
            name="ck_assessments_5",
        ),
        sa.CheckConstraint(
            "passing_percent IS NULL OR (passing_percent >= 0 AND passing_percent <= 100)",
            name="ck_assessments_6",
        ),
        sa.CheckConstraint(
            "score_release_policy IN ('IMMEDIATE','AFTER_CLOSE','INSTRUCTOR_RELEASE')",
            name="ck_assessments_7",
        ),
        sa.CheckConstraint(
            "answer_visibility_policy IN ('IMMEDIATE','AFTER_CLOSE','AFTER_ALL_ATTEMPTS','NEVER')",
            name="ck_assessments_8",
        ),
        sa.CheckConstraint(
            "random_question_count IS NULL OR random_question_count > 0",
            name="ck_assessments_9",
        ),
        sa.CheckConstraint(
            "open_at IS NULL OR close_at IS NULL OR open_at < close_at",
            name="ck_assessments_10",
        ),
        sa.Index("ix_assessments_course_status", "course_id", "status", "open_at", "close_at"),
        sa.Index("ix_assessments_pending_window", "status", "open_at", "close_at"),
    )

    course = relationship("Course", foreign_keys=[course_id], backref="assessments")
    creator = relationship("User", foreign_keys=[creator_user_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_user_id])
    sections = relationship(
        "AssessmentSection",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentSection.position",
    )
    question_assignments = relationship(
        "AssessmentQuestionAssignment",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentQuestionAssignment.position",
    )
    blueprints = relationship(
        "AssessmentBlueprint",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )
    question_pool = relationship(
        "AssessmentQuestionPool",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )
    attempts = relationship(
        "AssessmentAttempt",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class AssessmentSection(Base):
    """Section container inside an assessment mapping to 'assessment_sections' table."""

    __tablename__ = "assessment_sections"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    assessment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessments.id", name="fk_assessment_sections_assessment_id"),
        nullable=False,
    )
    title = db.Column(sa.Unicode(200), nullable=True)
    position = db.Column(sa.Integer, nullable=False)
    instructions = db.Column(NVarCharMax, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "assessment_id", "position", name="uq_assessment_sections_assessment_id_position_1"
        ),
        sa.CheckConstraint("position > 0", name="ck_assessment_sections_1"),
        sa.Index("ix_assessment_sections", "assessment_id", "position"),
    )

    assessment = relationship("Assessment", back_populates="sections")


class AssessmentQuestionAssignment(Base):
    """Fixed question assigned to assessment mapping to 'assessment_question_assignments' table."""

    __tablename__ = "assessment_question_assignments"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    assessment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessments.id", name="fk_assessment_question_assignments_assessment_id"),
        nullable=False,
    )
    section_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "assessment_sections.id",
            name="fk_assessment_question_assignments_section_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("questions.id", name="fk_assessment_question_assignments_question_id"),
        nullable=False,
    )
    position = db.Column(sa.Integer, nullable=False)
    points = db.Column(sa.Numeric(9, 4), nullable=False)
    is_mandatory = db.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("1"),
    )
    shuffle_choices_override = db.Column(sa.Boolean, nullable=True)
    source_type = db.Column(
        sa.String(20),
        nullable=False,
        default="BANK",
        server_default=sa.text("'BANK'"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "assessment_id",
            "question_id",
            name="uq_assessment_question_assignments_assessment_id_question_id_1",
        ),
        sa.CheckConstraint("position > 0", name="ck_assessment_question_assignments_1"),
        sa.CheckConstraint("points > 0", name="ck_assessment_question_assignments_2"),
        sa.CheckConstraint(
            "source_type IN ('MANUAL','BANK','IMPORT','AI')",
            name="ck_assessment_question_assignments_3",
        ),
        sa.Index("ix_assessment_assignments_position", "assessment_id", "position"),
    )

    assessment = relationship("Assessment", back_populates="question_assignments")
    section = relationship("AssessmentSection")
    question = relationship("Question")


class AssessmentBlueprint(Base):
    """Dynamic assessment generation blueprint mapping to 'assessment_blueprints' table."""

    __tablename__ = "assessment_blueprints"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    assessment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessments.id", name="fk_assessment_blueprints_assessment_id"),
        nullable=False,
    )
    name = db.Column(sa.Unicode(200), nullable=False)
    status = db.Column(
        sa.String(16),
        nullable=False,
        default="DRAFT",
        server_default=sa.text("'DRAFT'"),
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
            "assessment_id", "name", name="uq_assessment_blueprints_assessment_id_name_1"
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','READY','FROZEN')", name="ck_assessment_blueprints_1"
        ),
        sa.Index("ix_blueprints_assessment", "assessment_id", "status"),
    )

    assessment = relationship("Assessment", back_populates="blueprints")
    rules = relationship(
        "AssessmentBlueprintRule",
        back_populates="blueprint",
        cascade="all, delete-orphan",
        order_by="AssessmentBlueprintRule.position",
    )


class AssessmentBlueprintRule(Base):
    """Blueprint generation criteria rule mapping to 'assessment_blueprint_rules' table."""

    __tablename__ = "assessment_blueprint_rules"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    blueprint_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "assessment_blueprints.id",
            name="fk_assessment_blueprint_rules_blueprint_id",
        ),
        nullable=False,
    )
    section_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "assessment_sections.id",
            name="fk_assessment_blueprint_rules_section_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    lesson_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "lessons.id",
            name="fk_assessment_blueprint_rules_lesson_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    difficulty = db.Column(sa.String(20), nullable=True)
    question_type = db.Column(sa.String(24), nullable=True)
    question_count = db.Column(sa.Integer, nullable=False)
    points_each = db.Column(sa.Numeric(9, 4), nullable=False)
    position = db.Column(
        sa.Integer,
        nullable=False,
        default=1,
        server_default=sa.text("1"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "blueprint_id",
            "position",
            name="uq_assessment_blueprint_rules_blueprint_id_position_1",
        ),
        sa.CheckConstraint("question_count > 0", name="ck_assessment_blueprint_rules_1"),
        sa.CheckConstraint("points_each > 0", name="ck_assessment_blueprint_rules_2"),
        sa.CheckConstraint("position > 0", name="ck_assessment_blueprint_rules_3"),
        sa.CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('REMEMBER','UNDERSTAND','APPLY')",
            name="ck_assessment_blueprint_rules_4",
        ),
        sa.CheckConstraint(
            "question_type IS NULL OR "
            "question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE',"
            "'SHORT_ANSWER','ESSAY')",
            name="ck_assessment_blueprint_rules_5",
        ),
        sa.Index(
            "ix_blueprint_rules_filter",
            "blueprint_id",
            "lesson_id",
            "difficulty",
            "question_type",
        ),
    )

    blueprint = relationship("AssessmentBlueprint", back_populates="rules")
    section = relationship("AssessmentSection")
    lesson = relationship("Lesson")


class AssessmentQuestionPool(Base):
    """Materialized candidate pool for assessment mapping to 'assessment_question_pool' table."""

    __tablename__ = "assessment_question_pool"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    assessment_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("assessments.id", name="fk_assessment_question_pool_assessment_id"),
        nullable=False,
    )
    blueprint_rule_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "assessment_blueprint_rules.id",
            name="fk_assessment_question_pool_blueprint_rule_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("questions.id", name="fk_assessment_question_pool_question_id"),
        nullable=False,
    )
    points = db.Column(sa.Numeric(9, 4), nullable=False)
    is_fixed = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    position_hint = db.Column(sa.Integer, nullable=True)
    selection_source = db.Column(
        sa.String(20),
        nullable=False,
        default="BLUEPRINT",
        server_default=sa.text("'BLUEPRINT'"),
    )
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "assessment_id",
            "question_id",
            name="uq_assessment_question_pool_assessment_id_question_id_1",
        ),
        sa.CheckConstraint("points > 0", name="ck_assessment_question_pool_1"),
        sa.CheckConstraint(
            "position_hint IS NULL OR position_hint > 0", name="ck_assessment_question_pool_2"
        ),
        sa.CheckConstraint(
            "selection_source IN ('BLUEPRINT','MANUAL_POOL','IMPORT','AI')",
            name="ck_assessment_question_pool_3",
        ),
        sa.Index(
            "ix_assessment_pool_rule",
            "assessment_id",
            "blueprint_rule_id",
            "is_fixed",
            "question_id",
        ),
    )

    assessment = relationship("Assessment", back_populates="question_pool")
    blueprint_rule = relationship("AssessmentBlueprintRule")
    question = relationship("Question")
