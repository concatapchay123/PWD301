"""AI Service managing Question Drafting, LMS Conversations, and 5-Minute Lifecycle.

Implements:
- AI-assisted Question Drafting for Course Instructors with course-level authorization.
- 5-Minute Inactivity lifecycle (AI-003): sessions expire 300s after last activity.
- Expiration defense: reject messaging on expired sessions (HTTP 409 CONVERSATION_EXPIRED).
- Minimal metadata preservation: purge raw message content upon inactivity.
- Prompt injection screening and IDOR authorization controls.
- ADR-002 Zero Internal PK Leakage in all operations.
"""

from __future__ import annotations

import contextlib
import json
import logging
import time
import uuid
from datetime import timedelta
from typing import Any

from flask import current_app
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.ai_rag import (
    AIConversation,
    AIGeneratedQuestionDraft,
    AIMessage,
)
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import User
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import can_manage_course
from pwd301.services.exceptions import (
    AIConversationExpiredError,
    AIConversationNotFoundError,
    AIValidationError,
    ForbiddenError,
    ResourceNotFoundError,
)
from pwd301.services.gemini_service import (
    get_gemini_client,
    record_ai_telemetry,
    validate_and_sanitize_prompt,
)

logger = logging.getLogger(__name__)


def _get_inactivity_seconds() -> int:
    """Retrieve configured chat inactivity timeout (default 300s = 5 min)."""
    try:
        return int(current_app.config.get("AI_CHAT_INACTIVITY_SECONDS", 300))
    except RuntimeError:
        return 300


# ---------------------------------------------------------------------------
# Question Drafting Engine
# ---------------------------------------------------------------------------


def draft_course_questions(
    *,
    actor: User,
    course_id: str | uuid.UUID,
    topic: str,
    difficulty: str = "UNDERSTAND",
    question_types: list[str] | None = None,
    count: int = 3,
    lesson_id: str | uuid.UUID | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> list[AIGeneratedQuestionDraft]:
    """Generate question drafts for a course using Gemini.

    Strictly requires that the actor is an Instructor managing the course or an Admin.
    """
    sess = session or db.session

    # 1. Resolve course by public UUID
    try:
        c_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid course ID format: {course_id}") from exc

    course = sess.query(Course).filter(Course.public_id == c_uuid).first()
    if course is None or course.deleted_at is not None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    # 2. Authorization check: actor must manage this course
    if not can_manage_course(actor, course):
        raise ForbiddenError("You do not have permission to draft questions for this course.")

    # 3. Resolve optional lesson
    target_lesson: Lesson | None = None
    if lesson_id:
        try:
            l_uuid = (
                uuid.UUID(str(lesson_id)) if not isinstance(lesson_id, uuid.UUID) else lesson_id
            )
            target_lesson = sess.query(Lesson).filter(Lesson.public_id == l_uuid).first()
        except (ValueError, TypeError):
            pass

    # 4. Input validation and sanitization
    if not topic or not topic.strip():
        raise AIValidationError("Field 'topic' is required and cannot be empty.")
    sanitized_topic = validate_and_sanitize_prompt(topic.strip())

    if count < 1 or count > 10:
        raise AIValidationError("Question count must be between 1 and 10.")

    valid_difficulties = ("REMEMBER", "UNDERSTAND", "APPLY")
    diff_upper = difficulty.upper() if difficulty else "UNDERSTAND"
    if diff_upper not in valid_difficulties:
        raise AIValidationError(
            f"Invalid difficulty '{difficulty}'. Allowed: {', '.join(valid_difficulties)}"
        )

    allowed_types = (
        "SINGLE_CHOICE",
        "MULTIPLE_CHOICE",
        "TRUE_FALSE",
        "SHORT_ANSWER",
        "ESSAY",
    )
    selected_types = [qt.upper() for qt in (question_types or ["SINGLE_CHOICE"])]
    for qt in selected_types:
        if qt not in allowed_types:
            raise AIValidationError(
                f"Invalid question type '{qt}'. Allowed: {', '.join(allowed_types)}"
            )

    # 5. Invoke Gemini client
    client = get_gemini_client()
    t_start = time.time()
    telemetry_status = "SUCCEEDED"
    telemetry_error = None
    raw_drafts: list[dict[str, Any]] = []

    try:
        raw_drafts = client.draft_questions(
            course_title=course.title,
            topic=sanitized_topic,
            difficulty=diff_upper,
            question_types=selected_types,
            count=count,
        )
    except Exception as exc:
        telemetry_status = "FAILED"
        telemetry_error = type(exc).__name__
        logger.error("Failed to draft questions via Gemini: %s", exc)
        raise

    latency_ms = int((time.time() - t_start) * 1000)

    # 6. Record telemetry in ai_requests
    ai_req = record_ai_telemetry(
        user_id=actor.id,
        route_type="GEMINI",
        prompt=f"Draft {count} questions on '{sanitized_topic}' for {course.title}",
        status=telemetry_status,
        latency_ms=latency_ms,
        scope_decision="IN_SCOPE",
        error_code=telemetry_error,
        session=sess,
    )
    sess.flush()

    # 7. Persist question drafts in ai_generated_question_drafts
    persisted_drafts: list[AIGeneratedQuestionDraft] = []
    for idx, d in enumerate(raw_drafts, start=1):
        q_type = d.get("question_type", selected_types[0])
        if q_type not in allowed_types:
            q_type = selected_types[0]

        q_diff = d.get("difficulty", diff_upper)
        if q_diff not in valid_difficulties:
            q_diff = diff_upper

        choices_data = d.get("choices")
        choices_json = json.dumps(choices_data) if choices_data is not None else None

        answer_data = d.get("answer")
        answer_json = json.dumps(answer_data) if answer_data is not None else None

        draft_record = AIGeneratedQuestionDraft(
            course_id=course.id,
            lesson_id=target_lesson.id if target_lesson else None,
            requested_by_user_id=actor.id,
            ai_request_id=ai_req.id,
            ordinal=idx,
            question_type=q_type,
            difficulty=q_diff,
            content=d.get("content", f"Question on {sanitized_topic}"),
            choices_json=choices_json,
            answer_json=answer_json,
            explanation=d.get("explanation"),
            review_state="PENDING",
        )
        sess.add(draft_record)
        persisted_drafts.append(draft_record)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return persisted_drafts


def get_course_drafts(
    *,
    actor: User,
    course_id: str | uuid.UUID,
    review_state: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> list[AIGeneratedQuestionDraft]:
    """Retrieve question drafts for a course with ownership check."""
    sess = session or db.session
    try:
        c_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
    except (ValueError, TypeError) as exc:
        raise ResourceNotFoundError(f"Invalid course ID format: {course_id}") from exc

    course = sess.query(Course).filter(Course.public_id == c_uuid).first()
    if course is None or course.deleted_at is not None:
        raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    if not can_manage_course(actor, course):
        raise ForbiddenError("You do not have permission to view drafts for this course.")

    query = sess.query(AIGeneratedQuestionDraft).filter(
        AIGeneratedQuestionDraft.course_id == course.id
    )
    if review_state:
        query = query.filter(AIGeneratedQuestionDraft.review_state == review_state.upper())

    return query.order_by(AIGeneratedQuestionDraft.created_at.desc()).all()


# ---------------------------------------------------------------------------
# AI Conversation Lifecycle (AI-003: 5-Minute Inactivity)
# ---------------------------------------------------------------------------


def create_conversation(
    *,
    actor: User,
    context_type: str = "GLOBAL",
    course_id: str | uuid.UUID | None = None,
    lesson_id: str | uuid.UUID | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> AIConversation:
    """Initialize a short-lived AI conversation session with 5-minute inactivity deadline."""
    sess = session or db.session

    c_type = context_type.upper()
    if c_type not in ("GLOBAL", "COURSE", "LESSON"):
        raise AIValidationError(
            f"Invalid context_type '{context_type}'. Allowed: GLOBAL, COURSE, LESSON"
        )

    target_course: Course | None = None
    if course_id:
        try:
            c_uuid = (
                uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
            )
            target_course = sess.query(Course).filter(Course.public_id == c_uuid).first()
        except (ValueError, TypeError):
            pass
        if target_course is None or target_course.deleted_at is not None:
            raise ResourceNotFoundError(f"Course '{course_id}' not found.")

    target_lesson: Lesson | None = None
    if lesson_id:
        try:
            l_uuid = (
                uuid.UUID(str(lesson_id)) if not isinstance(lesson_id, uuid.UUID) else lesson_id
            )
            target_lesson = sess.query(Lesson).filter(Lesson.public_id == l_uuid).first()
        except (ValueError, TypeError):
            pass
        if target_lesson is None or target_lesson.deleted_at is not None:
            raise ResourceNotFoundError(f"Lesson '{lesson_id}' not found.")

    inactivity_secs = _get_inactivity_seconds()
    now = utc_now()
    expires_at = now + timedelta(seconds=inactivity_secs)

    conv = AIConversation(
        public_id=uuid.uuid4(),
        user_id=actor.id,
        context_type=c_type,
        course_id=target_course.id if target_course else None,
        lesson_id=target_lesson.id if target_lesson else None,
        last_activity_at=now,
        expires_at=expires_at,
        status="ACTIVE",
    )
    sess.add(conv)
    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return conv


def get_conversation(
    *,
    actor: User,
    conversation_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> AIConversation:
    """Retrieve an AI conversation by public UUID, verifying ownership and expiry."""
    sess = session or db.session

    try:
        conv_uuid = (
            uuid.UUID(str(conversation_id))
            if not isinstance(conversation_id, uuid.UUID)
            else conversation_id
        )
    except (ValueError, TypeError) as exc:
        raise AIConversationNotFoundError(f"Invalid conversation ID: {conversation_id}") from exc

    conv = sess.query(AIConversation).filter(AIConversation.public_id == conv_uuid).first()
    if conv is None or conv.status == "DELETED":
        raise AIConversationNotFoundError(f"Conversation '{conversation_id}' not found.")

    # IDOR check: conversation belongs to actor or system admin
    if conv.user_id != actor.id and not actor.is_admin:
        raise ForbiddenError("Access denied: You do not own this conversation.")

    # Check 5-minute inactivity rule
    if conv.is_expired and conv.status != "EXPIRED":
        conv.status = "EXPIRED"
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    return conv


def send_chat_message(
    *,
    actor: User,
    conversation_id: str | uuid.UUID,
    content: str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[AIMessage, AIMessage]:
    """Send a user message, enforce 5-minute inactivity deadline, and generate AI response.

    Returns:
        tuple of (user_message, assistant_message)
    """
    sess = session or db.session
    conv = get_conversation(actor=actor, conversation_id=conversation_id, session=sess)

    # 1. Enforce 5-Minute Inactivity Rule (AI-003)
    if conv.is_expired:
        if conv.status != "EXPIRED":
            conv.status = "EXPIRED"
            try:
                sess.commit()
            except Exception:
                sess.rollback()
                raise
        raise AIConversationExpiredError(
            "AI conversation has expired due to 5 minutes of inactivity. "
            "Please start a new session."
        )

    # 2. Input validation & Prompt Injection Screening
    if not content or not content.strip():
        raise AIValidationError("Message content cannot be empty.")

    sanitized_content = validate_and_sanitize_prompt(content.strip())

    # 3. Calculate sequence numbers
    existing_seqs = [m.sequence_no for m in conv.messages]
    next_seq = max(existing_seqs, default=0) + 1

    # 4. Record USER message
    now = utc_now()
    user_msg = AIMessage(
        conversation_id=conv.id,
        sender="USER",
        content=sanitized_content,
        sequence_no=next_seq,
        created_at=now,
    )
    sess.add(user_msg)

    # 5. Reset 5-minute inactivity expiry
    inactivity_secs = _get_inactivity_seconds()
    conv.last_activity_at = now
    conv.expires_at = now + timedelta(seconds=inactivity_secs)

    # 6. Generate ASSISTANT reply via Gemini Client
    client = get_gemini_client()
    context_str = f"Context: {conv.context_type}"
    if conv.course:
        context_str += f", Course: {conv.course.title}"

    history = [
        {"sender": m.sender, "content": m.content}
        for m in sorted(conv.messages, key=lambda x: x.sequence_no)
    ]
    history.append({"sender": "USER", "content": sanitized_content})

    t_start = time.time()
    telemetry_status = "SUCCEEDED"
    telemetry_error = None
    reply_text: str

    try:
        reply_text = client.chat_response(messages=history, context=context_str)
    except Exception as exc:
        latency_ms = int((time.time() - t_start) * 1000)
        telemetry_error = type(exc).__name__
        logger.error("Gemini chat response failed: %s", exc)
        sess.rollback()
        with contextlib.suppress(Exception):
            record_ai_telemetry(
                user_id=actor.id,
                conversation_id=conv.id,
                route_type="GEMINI",
                prompt=sanitized_content[:250],
                status="FAILED",
                latency_ms=latency_ms,
                scope_decision="IN_SCOPE",
                error_code=telemetry_error,
                session=sess,
            )
            try:
                sess.commit()
            except Exception:
                sess.rollback()
        raise

    latency_ms = int((time.time() - t_start) * 1000)

    # 7. Record telemetry in ai_requests
    record_ai_telemetry(
        user_id=actor.id,
        conversation_id=conv.id,
        route_type="GEMINI",
        prompt=sanitized_content[:250],
        status=telemetry_status,
        latency_ms=latency_ms,
        scope_decision="IN_SCOPE",
        error_code=telemetry_error,
        session=sess,
    )
    sess.flush()

    # 8. Record ASSISTANT message
    assistant_msg = AIMessage(
        conversation_id=conv.id,
        sender="ASSISTANT",
        content=reply_text,
        sequence_no=next_seq + 1,
        created_at=utc_now(),
    )
    sess.add(assistant_msg)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return user_msg, assistant_msg


def purge_expired_ai_conversations(
    session: Session | scoped_session[Any] | None = None,
) -> int:
    """Purge raw message content from conversations inactive for > 5 minutes (AI-003).

    Preserves conversation metadata and ai_requests telemetry while wiping message bodies.

    Returns:
        Count of conversations purged.
    """
    sess = session or db.session
    all_convs = sess.query(AIConversation).all()

    count = 0
    for conv in all_convs:
        if conv.is_expired:
            conv.status = "EXPIRED"
            if conv.messages:
                for msg in list(conv.messages):
                    sess.delete(msg)
                count += 1

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    return count
