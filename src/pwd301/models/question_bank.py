"""Question bank and revision domain models for PWD301.

Implements canonical schema tables from sql/003_question_bank.sql:
- questions
- question_revisions
- question_revision_choices
- question_revision_accepted_answers
- question_provenance
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


class Question(Base):
    """Question identity model mapping to canonical 'questions' table.

    *Lưu ý kiến trúc: Model này sử dụng cơ chế Soft-delete (deleted_at).
    Do DB áp dụng mặc định NO ACTION cho Foreign Keys, tầng Application Service
    phải tự chịu trách nhiệm xử lý cascade data (ẩn/xóa dữ liệu con) bằng code Python.*
    """

    __tablename__ = "questions"

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
        sa.ForeignKey("courses.id", name="fk_questions_course_id"),
        nullable=False,
    )
    lesson_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("lessons.id", name="fk_questions_lesson_id", ondelete="SET NULL"),
        nullable=True,
    )
    creator_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_questions_creator_user_id"),
        nullable=True,
    )
    difficulty = db.Column(sa.String(20), nullable=False)
    learning_objective = db.Column(sa.Unicode(500), nullable=True)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="DRAFT",
        server_default=sa.text("'DRAFT'"),
    )
    current_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_revisions.id",
            name="fk_questions_current_revision_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    first_used_at = db.Column(UTCDateTime, nullable=True)
    first_answered_at = db.Column(UTCDateTime, nullable=True)
    usage_count = db.Column(
        sa.BigInteger,
        nullable=False,
        default=0,
        server_default=sa.text("0"),
    )
    last_used_at = db.Column(UTCDateTime, nullable=True)
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
        sa.ForeignKey("users.id", name="fk_questions_deleted_by_user_id"),
        nullable=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "difficulty IN ('REMEMBER','UNDERSTAND','APPLY')", name="ck_questions_1"
        ),
        sa.CheckConstraint("status IN ('DRAFT','ACTIVE','RETIRED','TRASH')", name="ck_questions_2"),
        sa.CheckConstraint("usage_count >= 0", name="ck_questions_3"),
        sa.Index(
            "ix_questions_bank_filter",
            "course_id",
            "lesson_id",
            "difficulty",
            "status",
            "id",
        ),
        sa.Index("ix_questions_usage", "course_id", "last_used_at", "usage_count"),
    )

    course = relationship("Course", foreign_keys=[course_id], backref="questions")
    lesson = relationship("Lesson", foreign_keys=[lesson_id])
    creator = relationship("User", foreign_keys=[creator_user_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_user_id])
    revisions = relationship(
        "QuestionRevision",
        foreign_keys="QuestionRevision.question_id",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    current_revision = relationship(
        "QuestionRevision",
        foreign_keys=[current_revision_id],
        post_update=True,
    )


class QuestionRevision(Base):
    """Immutable question revision snapshot mapping to 'question_revisions' table."""

    __tablename__ = "question_revisions"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("questions.id", name="fk_question_revisions_question_id"),
        nullable=False,
    )
    revision_no = db.Column(sa.Integer, nullable=False)
    question_type = db.Column(sa.String(24), nullable=False)
    content = db.Column(NVarCharMax, nullable=False)
    explanation = db.Column(NVarCharMax, nullable=True)
    short_answer_match_mode = db.Column(sa.String(16), nullable=True)
    change_type = db.Column(
        sa.String(24),
        nullable=False,
        default="EDIT",
        server_default=sa.text("'EDIT'"),
    )
    change_reason = db.Column(sa.Unicode(1000), nullable=True)
    created_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_question_revisions_created_by_user_id"),
        nullable=True,
    )
    approved_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_question_revisions_approved_by_user_id"),
        nullable=True,
    )
    approved_at = db.Column(UTCDateTime, nullable=True)
    was_student_exposed = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    was_used_for_grading = db.Column(
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
            "question_id", "revision_no", name="uq_question_revisions_question_id_revision_no_1"
        ),
        sa.CheckConstraint("revision_no > 0", name="ck_question_revisions_1"),
        sa.CheckConstraint(
            "question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE',"
            "'SHORT_ANSWER','ESSAY')",
            name="ck_question_revisions_2",
        ),
        sa.CheckConstraint(
            "short_answer_match_mode IS NULL OR short_answer_match_mode IN ('NORMALIZED','EXACT')",
            name="ck_question_revisions_3",
        ),
        sa.CheckConstraint(
            "change_type IN ("
            "'INITIAL','EDIT','ANSWER_ONLY','CONTENT_OR_CHOICES',"
            "'TYPO_FIX','ANSWER_CHANGE','CONTENT_CHANGE','REVOCATION')",
            name="ck_question_revisions_4",
        ),
        sa.Index("ix_question_revisions_question", "question_id", "revision_no"),
        sa.Index(
            "ix_question_revisions_exposure",
            "was_student_exposed",
            "was_used_for_grading",
        ),
    )

    question = relationship("Question", foreign_keys=[question_id], back_populates="revisions")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    choices = relationship(
        "QuestionRevisionChoice",
        back_populates="question_revision",
        cascade="all, delete-orphan",
        order_by="QuestionRevisionChoice.position",
    )
    accepted_answers = relationship(
        "QuestionRevisionAcceptedAnswer",
        back_populates="question_revision",
        cascade="all, delete-orphan",
        order_by="QuestionRevisionAcceptedAnswer.position",
    )


class QuestionRevisionChoice(Base):
    """Multiple choice options for a revision mapping to 'question_revision_choices' table."""

    __tablename__ = "question_revision_choices"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    question_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_revisions.id",
            name="fk_question_revision_choices_question_revision_id",
        ),
        nullable=False,
    )
    choice_key = db.Column(
        GUID,
        nullable=False,
        default=uuid.uuid4,
        server_default=sa.text("NEWID()"),
    )
    content = db.Column(NVarCharMax, nullable=False)
    is_correct = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )
    position = db.Column(sa.Integer, nullable=False)
    is_fixed_position = db.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("0"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "question_revision_id",
            "choice_key",
            name="uq_question_revision_choices_question_revision_id_choice_key_1",
        ),
        sa.UniqueConstraint(
            "question_revision_id",
            "position",
            name="uq_question_revision_choices_question_revision_id_position_2",
        ),
        sa.CheckConstraint("position > 0", name="ck_question_revision_choices_1"),
        sa.Index("ix_question_choices_revision", "question_revision_id", "position"),
    )

    question_revision = relationship("QuestionRevision", back_populates="choices")


class QuestionRevisionAcceptedAnswer(Base):
    """Accepted short answer patterns mapping to 'question_revision_accepted_answers' table."""

    __tablename__ = "question_revision_accepted_answers"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    question_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_revisions.id",
            name="fk_question_revision_accepted_answers_question_revision_id",
        ),
        nullable=False,
    )
    answer_text = db.Column(sa.Unicode(1000), nullable=False)
    answer_normalized = db.Column(sa.Unicode(1000), nullable=False)
    position = db.Column(
        sa.Integer,
        nullable=False,
        default=1,
        server_default=sa.text("1"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "question_revision_id",
            "answer_normalized",
            name="uq_question_revision_accepted_answers_question_revision_id_answer_normalized_1",
        ),
        sa.CheckConstraint("position > 0", name="ck_question_revision_accepted_answers_1"),
        sa.Index("ix_accepted_answers_revision", "question_revision_id", "position"),
    )

    question_revision = relationship("QuestionRevision", back_populates="accepted_answers")


class QuestionProvenance(Base):
    """Source origin and derivation tracking mapping to 'question_provenance' table."""

    __tablename__ = "question_provenance"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("questions.id", name="fk_question_provenance_question_id"),
        nullable=False,
    )
    question_revision_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "question_revisions.id",
            name="fk_question_provenance_question_revision_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    source_type = db.Column(sa.String(24), nullable=False)
    source_ref_type = db.Column(sa.String(32), nullable=True)
    source_ref_id = db.Column(sa.BigInteger, nullable=True)
    source_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "questions.id",
            name="fk_question_provenance_source_question_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    ai_model = db.Column(sa.Unicode(100), nullable=True)
    generated_at = db.Column(UTCDateTime, nullable=True)
    approved_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_question_provenance_approved_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    approved_at = db.Column(UTCDateTime, nullable=True)
    notes = db.Column(sa.Unicode(1000), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "source_type IN ('MANUAL','IMPORT','AI_GENERATED','DUPLICATED')",
            name="ck_question_provenance_1",
        ),
        sa.Index("ix_question_provenance_question", "question_id", "created_at"),
        sa.Index("ix_question_provenance_source", "source_type", "created_at"),
    )

    question = relationship("Question", foreign_keys=[question_id])
    question_revision = relationship("QuestionRevision", foreign_keys=[question_revision_id])
    source_question = relationship("Question", foreign_keys=[source_question_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
