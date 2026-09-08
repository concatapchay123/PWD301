"""AI and RAG knowledge retrieval models for PWD301.

Implements canonical schema tables from sql/007_ai_rag.sql:
- ai_conversations
- ai_messages
- ai_requests
- ai_generated_question_drafts
- knowledge_documents
- knowledge_versions
- knowledge_chunks
- ai_source_usages
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


class AIConversation(Base):
    """Short-lived AI chat context session mapping to 'ai_conversations' table."""

    __tablename__ = "ai_conversations"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    public_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWSEQUENTIALID()"),
    )
    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_ai_conversations_user_id"),
        nullable=False,
    )
    context_type = db.Column(sa.String(16), nullable=False)
    course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_ai_conversations_course_id", ondelete="SET NULL"),
        nullable=True,
    )
    lesson_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("lessons.id", name="fk_ai_conversations_lesson_id", ondelete="SET NULL"),
        nullable=True,
    )
    last_activity_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    expires_at = db.Column(UTCDateTime, nullable=False)
    status = db.Column(
        sa.String(16),
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
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.CheckConstraint(
            "context_type IN ('GLOBAL','COURSE','LESSON')", name="ck_ai_conversations_1"
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE','EXPIRED','DELETED')", name="ck_ai_conversations_2"
        ),
        sa.CheckConstraint("expires_at > created_at", name="ck_ai_conversations_3"),
        sa.Index("ix_ai_conversations_user_active", "user_id", "status", "last_activity_at"),
        sa.Index(
            "ix_ai_conversations_expiry",
            "expires_at",
            "status",
            mssql_where=sa.text("status='ACTIVE'"),
            sqlite_where=sa.text("status='ACTIVE'"),
        ),
    )

    user = relationship("User", foreign_keys=[user_id])
    course = relationship("Course", foreign_keys=[course_id])
    lesson = relationship("Lesson", foreign_keys=[lesson_id])
    messages = relationship(
        "AIMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessage.sequence_no",
    )


class AIMessage(Base):
    """Chat message inside an AI conversation mapping to 'ai_messages' table."""

    __tablename__ = "ai_messages"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    conversation_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("ai_conversations.id", name="fk_ai_messages_conversation_id"),
        nullable=False,
    )
    sender = db.Column(sa.String(12), nullable=False)
    content = db.Column(NVarCharMax, nullable=False)
    sequence_no = db.Column(sa.Integer, nullable=False)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "conversation_id",
            "sequence_no",
            name="uq_ai_messages_conversation_id_sequence_no_1",
        ),
        sa.CheckConstraint("sender IN ('USER','ASSISTANT')", name="ck_ai_messages_1"),
        sa.CheckConstraint("sequence_no > 0", name="ck_ai_messages_2"),
        sa.Index("ix_ai_messages_conv_seq", "conversation_id", "sequence_no"),
    )

    conversation = relationship("AIConversation", back_populates="messages")


class AIRequest(Base):
    """Audit and telemetry log for AI invocations mapping to 'ai_requests' table."""

    __tablename__ = "ai_requests"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    request_id = db.Column(
        GUID,
        nullable=False,
        unique=True,
        default=uuid.uuid4,
        server_default=sa.text("NEWID()"),
    )
    conversation_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "ai_conversations.id",
            name="fk_ai_requests_conversation_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_ai_requests_user_id"),
        nullable=False,
    )
    route_type = db.Column(sa.String(24), nullable=False)
    model_name = db.Column(sa.Unicode(100), nullable=True)
    prompt_hash = db.Column(Binary32, nullable=True)
    scope_decision = db.Column(sa.String(16), nullable=True)
    authorization_scope_hash = db.Column(Binary32, nullable=True)
    input_token_count = db.Column(sa.Integer, nullable=True)
    output_token_count = db.Column(sa.Integer, nullable=True)
    latency_ms = db.Column(sa.Integer, nullable=True)
    status = db.Column(sa.String(20), nullable=False)
    error_code = db.Column(sa.String(64), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "route_type IN ('BACKEND_ONLY','GEMINI','RAG','CLASSIFIER')",
            name="ck_ai_requests_1",
        ),
        sa.CheckConstraint(
            "scope_decision IS NULL OR "
            "scope_decision IN ('IN_SCOPE','OUT_OF_SCOPE','MIXED','AMBIGUOUS')",
            name="ck_ai_requests_2",
        ),
        sa.CheckConstraint(
            "status IN ('SUCCEEDED','REFUSED','FAILED','TIMEOUT','BYPASSED')",
            name="ck_ai_requests_3",
        ),
        sa.CheckConstraint(
            "input_token_count IS NULL OR input_token_count >= 0",
            name="ck_ai_requests_4",
        ),
        sa.CheckConstraint(
            "output_token_count IS NULL OR output_token_count >= 0",
            name="ck_ai_requests_5",
        ),
        sa.CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_ai_requests_6"),
        sa.Index("ix_ai_requests_user_time", "user_id", "created_at"),
        sa.Index("ix_ai_requests_route_status", "route_type", "status", "created_at"),
    )

    conversation = relationship("AIConversation", foreign_keys=[conversation_id])
    user = relationship("User", foreign_keys=[user_id])


class AIGeneratedQuestionDraft(Base):
    """AI-synthesized question candidate mapping to 'ai_generated_question_drafts'."""

    __tablename__ = "ai_generated_question_drafts"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    course_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("courses.id", name="fk_ai_generated_question_drafts_course_id"),
        nullable=False,
    )
    lesson_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "lessons.id",
            name="fk_ai_generated_question_drafts_lesson_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    requested_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("users.id", name="fk_ai_generated_question_drafts_requested_by_user_id"),
        nullable=False,
    )
    ai_request_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "ai_requests.id",
            name="fk_ai_generated_question_drafts_ai_request_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    ordinal = db.Column(sa.Integer, nullable=False)
    question_type = db.Column(sa.String(24), nullable=False)
    difficulty = db.Column(sa.String(20), nullable=False)
    content = db.Column(NVarCharMax, nullable=False)
    choices_json = db.Column(NVarCharMax, nullable=True)
    answer_json = db.Column(NVarCharMax, nullable=True)
    explanation = db.Column(NVarCharMax, nullable=True)
    review_state = db.Column(
        sa.String(16),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    approved_question_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "questions.id",
            name="fk_ai_generated_question_drafts_approved_question_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    reviewed_by_user_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "users.id",
            name="fk_ai_generated_question_drafts_reviewed_by_user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    reviewed_at = db.Column(UTCDateTime, nullable=True)
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
        sa.CheckConstraint("ordinal > 0", name="ck_ai_generated_question_drafts_1"),
        sa.CheckConstraint(
            "question_type IN ('SINGLE_CHOICE','MULTIPLE_CHOICE','TRUE_FALSE',"
            "'SHORT_ANSWER','ESSAY')",
            name="ck_ai_generated_question_drafts_2",
        ),
        sa.CheckConstraint(
            "difficulty IN ('REMEMBER','UNDERSTAND','APPLY')",
            name="ck_ai_generated_question_drafts_3",
        ),
        sa.CheckConstraint(
            "review_state IN ('PENDING','KEPT','EDITED','REJECTED','APPROVED')",
            name="ck_ai_generated_question_drafts_4",
        ),
        sa.CheckConstraint(
            "choices_json IS NULL OR ISJSON(choices_json)=1",
            name="ck_ai_generated_question_drafts_5",
        ),
        sa.CheckConstraint(
            "answer_json IS NULL OR ISJSON(answer_json)=1",
            name="ck_ai_generated_question_drafts_6",
        ),
        sa.Index("ix_ai_drafts_course_review", "course_id", "review_state"),
    )

    course = relationship("Course", foreign_keys=[course_id])
    lesson = relationship("Lesson", foreign_keys=[lesson_id])
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    ai_request = relationship("AIRequest", foreign_keys=[ai_request_id])
    approved_question = relationship("Question", foreign_keys=[approved_question_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])


class KnowledgeDocument(Base):
    """Authorized RAG document source mapping to 'knowledge_documents' table."""

    __tablename__ = "knowledge_documents"

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
        sa.ForeignKey("courses.id", name="fk_knowledge_documents_course_id"),
        nullable=False,
    )
    lesson_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("lessons.id", name="fk_knowledge_documents_lesson_id", ondelete="SET NULL"),
        nullable=True,
    )
    source_type = db.Column(sa.String(24), nullable=False)
    source_entity_id = db.Column(sa.BigInteger, nullable=False)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="ACTIVE",
        server_default=sa.text("'ACTIVE'"),
    )
    current_version_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "knowledge_versions.id",
            name="fk_knowledge_documents_current_version_id",
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
            "source_type",
            "source_entity_id",
            name="uq_knowledge_documents_source_type_source_entity_id_2",
        ),
        sa.CheckConstraint(
            "source_type IN ('LESSON','FILE','FAQ','POLICY')",
            name="ck_knowledge_documents_1",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE','INVALIDATED','DELETED')", name="ck_knowledge_documents_2"
        ),
        sa.Index("ix_knowledge_docs_course", "course_id", "status"),
    )

    course = relationship("Course", foreign_keys=[course_id])
    lesson = relationship("Lesson", foreign_keys=[lesson_id])
    versions = relationship(
        "KnowledgeVersion",
        foreign_keys="KnowledgeVersion.knowledge_document_id",
        back_populates="knowledge_document",
        cascade="all, delete-orphan",
        order_by="KnowledgeVersion.version_no",
    )
    current_version = relationship(
        "KnowledgeVersion",
        foreign_keys=[current_version_id],
        post_update=True,
    )


class KnowledgeVersion(Base):
    """Indexed content generation version mapping to 'knowledge_versions' table."""

    __tablename__ = "knowledge_versions"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    knowledge_document_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "knowledge_documents.id",
            name="fk_knowledge_versions_knowledge_document_id",
        ),
        nullable=False,
    )
    version_no = db.Column(sa.Integer, nullable=False)
    source_revision_type = db.Column(sa.String(32), nullable=True)
    source_revision_id = db.Column(sa.BigInteger, nullable=True)
    content_hash = db.Column(Binary32, nullable=False)
    status = db.Column(
        sa.String(20),
        nullable=False,
        default="PENDING",
        server_default=sa.text("'PENDING'"),
    )
    vector_namespace = db.Column(sa.Unicode(200), nullable=True)
    background_job_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "background_jobs.id",
            name="fk_knowledge_versions_background_job_id",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    activated_at = db.Column(UTCDateTime, nullable=True)
    invalidated_at = db.Column(UTCDateTime, nullable=True)
    last_error = db.Column(sa.Unicode(2000), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )
    row_version = db.Column(RowVersion, nullable=True)

    __table_args__ = (
        sa.UniqueConstraint(
            "knowledge_document_id",
            "version_no",
            name="uq_knowledge_versions_knowledge_document_id_version_no_1",
        ),
        sa.CheckConstraint("version_no > 0", name="ck_knowledge_versions_1"),
        sa.CheckConstraint(
            "status IN ('PENDING','PROCESSING','ACTIVE','INVALIDATED','FAILED')",
            name="ck_knowledge_versions_2",
        ),
        sa.Index("ix_knowledge_versions_status", "status", "created_at"),
        sa.Index(
            "ux_knowledge_version_active",
            "knowledge_document_id",
            unique=True,
            mssql_where=sa.text("status='ACTIVE'"),
            sqlite_where=sa.text("status='ACTIVE'"),
        ),
    )

    knowledge_document = relationship(
        "KnowledgeDocument",
        foreign_keys=[knowledge_document_id],
        back_populates="versions",
    )
    chunks = relationship(
        "KnowledgeChunk",
        back_populates="knowledge_version",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.chunk_no",
    )


class KnowledgeChunk(Base):
    """Vectorized text slice mapping to 'knowledge_chunks' table."""

    __tablename__ = "knowledge_chunks"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    knowledge_version_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "knowledge_versions.id",
            name="fk_knowledge_chunks_knowledge_version_id",
        ),
        nullable=False,
    )
    chunk_no = db.Column(sa.Integer, nullable=False)
    text_hash = db.Column(Binary32, nullable=False)
    vector_key = db.Column(sa.Unicode(300), nullable=False, unique=True)
    token_count = db.Column(sa.Integer, nullable=True)
    metadata_json = db.Column(NVarCharMax, nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "knowledge_version_id",
            "chunk_no",
            name="uq_knowledge_chunks_knowledge_version_id_chunk_no_1",
        ),
        sa.CheckConstraint("chunk_no > 0", name="ck_knowledge_chunks_1"),
        sa.CheckConstraint("token_count IS NULL OR token_count >= 0", name="ck_knowledge_chunks_2"),
        sa.CheckConstraint(
            "metadata_json IS NULL OR ISJSON(metadata_json)=1",
            name="ck_knowledge_chunks_3",
        ),
        sa.Index("ix_knowledge_chunks_version", "knowledge_version_id", "chunk_no"),
    )

    knowledge_version = relationship("KnowledgeVersion", back_populates="chunks")


class AISourceUsage(Base):
    """RAG source citation and ranking record mapping to 'ai_source_usages' table."""

    __tablename__ = "ai_source_usages"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    ai_request_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey("ai_requests.id", name="fk_ai_source_usages_ai_request_id"),
        nullable=False,
    )
    knowledge_version_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "knowledge_versions.id",
            name="fk_ai_source_usages_knowledge_version_id",
        ),
        nullable=False,
    )
    knowledge_chunk_id = db.Column(
        sa.BigInteger,
        sa.ForeignKey(
            "knowledge_chunks.id",
            name="fk_ai_source_usages_knowledge_chunk_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    rank_no = db.Column(sa.Integer, nullable=True)
    relevance_score = db.Column(sa.Numeric(8, 6), nullable=True)
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=utc_now,
        server_default=sa.text("SYSUTCDATETIME()"),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "ai_request_id",
            "knowledge_version_id",
            "knowledge_chunk_id",
            name="uq_ai_source_usages_ai_request_id_knowledge_version_id_knowledge_chunk_id_1",
        ),
        sa.CheckConstraint("rank_no IS NULL OR rank_no > 0", name="ck_ai_source_usages_1"),
        sa.Index("ix_ai_source_usages_request", "ai_request_id", "rank_no"),
    )

    ai_request = relationship("AIRequest", foreign_keys=[ai_request_id])
    knowledge_version = relationship("KnowledgeVersion", foreign_keys=[knowledge_version_id])
    knowledge_chunk = relationship("KnowledgeChunk", foreign_keys=[knowledge_chunk_id])
