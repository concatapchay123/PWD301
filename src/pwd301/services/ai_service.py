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
from pwd301.models.question_bank import Question
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import can_manage_course
from pwd301.services.exceptions import (
    AIConversationExpiredError,
    AIConversationNotFoundError,
    AIOutOfScopeError,
    AIPromptInjectionError,
    AIValidationError,
    ForbiddenError,
    ResourceNotFoundError,
)
from pwd301.services.gemini_service import (
    get_gemini_client,
    record_ai_telemetry,
    sanitize_prompt,
    validate_and_sanitize_prompt,
)
from pwd301.services.scope_classifier import classify_query_scope_hybrid

logger = logging.getLogger(__name__)


def _get_inactivity_seconds() -> int:
    """Retrieve configured chat inactivity timeout (default 300s = 5 min)."""
    try:
        return int(current_app.config.get("AI_CHAT_INACTIVITY_SECONDS", 300))
    except RuntimeError:
        return 300


# ---------------------------------------------------------------------------
# Question Drafting & Bloom Taxonomy Engine
# ---------------------------------------------------------------------------

BLOOM_TAXONOMY_LEVELS: tuple[str, ...] = (
    "REMEMBER",
    "UNDERSTAND",
    "APPLY",
    "ANALYZE",
    "EVALUATE",
    "CREATE",
)


def _map_bloom_to_db_difficulty(bloom_level: str) -> str:
    """Map Bloom taxonomy levels to database difficulty ('REMEMBER', 'UNDERSTAND', 'APPLY')."""
    level = bloom_level.strip().upper() if bloom_level else "UNDERSTAND"
    if level in ("REMEMBER", "UNDERSTAND", "APPLY"):
        return level
    if level in ("ANALYZE", "EVALUATE", "CREATE"):
        return "APPLY"
    return "UNDERSTAND"


def _resolve_draft(
    draft_id: int | str | uuid.UUID,
    session: Session | scoped_session[Any],
) -> AIGeneratedQuestionDraft | None:
    internal_id = (
        AIGeneratedQuestionDraft.resolve_id_from_public_id(draft_id)
        if isinstance(draft_id, (str, uuid.UUID))
        else None
    )
    if internal_id is not None:
        return (
            session.query(AIGeneratedQuestionDraft)
            .filter(AIGeneratedQuestionDraft.id == internal_id)
            .first()
        )
    if isinstance(draft_id, int) or (isinstance(draft_id, str) and draft_id.isdigit()):
        return (
            session.query(AIGeneratedQuestionDraft)
            .filter(AIGeneratedQuestionDraft.id == int(draft_id))
            .first()
        )
    return None


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
    """Generate question drafts for a course using Gemini aligned with Bloom's Taxonomy.

    Strictly requires that the actor is an Instructor managing the course or an Admin.
    Higher-order Bloom levels (ANALYZE, EVALUATE, CREATE) are mapped to 'APPLY' in the
    database check constraint while preserving exact cognitive taxonomy in explanation.
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

    diff_upper = difficulty.upper() if difficulty else "UNDERSTAND"
    if diff_upper not in BLOOM_TAXONOMY_LEVELS:
        levels_str = ", ".join(BLOOM_TAXONOMY_LEVELS)
        raise AIValidationError(
            f"Invalid difficulty '{difficulty}'. Allowed Bloom taxonomy levels: {levels_str}"
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
        prompt=f"Draft {count} questions ({diff_upper}) on '{sanitized_topic}' for {course.title}",
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
        if q_diff not in BLOOM_TAXONOMY_LEVELS:
            q_diff = diff_upper

        db_diff = _map_bloom_to_db_difficulty(q_diff)
        expl = d.get("explanation")
        if q_diff in ("ANALYZE", "EVALUATE", "CREATE"):
            prefix = f"[Bloom: {q_diff}] "
            if expl:
                if prefix not in expl:
                    expl = prefix + expl
            else:
                expl = prefix

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
            difficulty=db_diff,
            content=d.get("content", f"Question on {sanitized_topic}"),
            choices_json=choices_json,
            answer_json=answer_json,
            explanation=expl,
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


def get_question_draft(
    *,
    actor: User,
    draft_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> AIGeneratedQuestionDraft:
    """Retrieve an AI Question Draft by public ID, verifying course management authorization."""
    sess = session or db.session
    draft = _resolve_draft(draft_id, sess)
    if draft is None:
        raise ResourceNotFoundError(f"Question draft '{draft_id}' not found.")

    if not can_manage_course(actor, draft.course):
        raise ForbiddenError(
            "You do not have permission to access question drafts for this course."
        )

    return draft


def approve_question_draft(
    *,
    actor: User,
    draft_id: str | uuid.UUID,
    edits: dict[str, Any] | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[AIGeneratedQuestionDraft, Question]:
    """Approve an AI question draft, creating a formal Question and QuestionRevision.

    Enforces:
    - Actor authorization: managing instructor or admin.
    - Idempotency / state check: cannot approve an already APPROVED draft.
    - Immutable QuestionRevision (Revision 1) created in Question Bank.
    - QuestionProvenance recorded with source_type='AI_GENERATED', ai_model='gemini-3.8-flash'.
    - Append-only AuditEvent persisted.
    - Draft marked review_state='APPROVED', linked to question, with reviewer metadata.
    """
    sess = session or db.session
    draft = get_question_draft(actor=actor, draft_id=draft_id, session=sess)

    if draft.review_state == "APPROVED":
        raise AIValidationError("Question draft has already been approved.")

    edits_dict = edits or {}

    # Extract or override question fields
    q_type = (edits_dict.get("question_type") or draft.question_type).upper()
    diff_val = (edits_dict.get("difficulty") or draft.difficulty).upper()
    db_diff = _map_bloom_to_db_difficulty(diff_val)
    content = edits_dict.get("content") or draft.content
    explanation = edits_dict.get("explanation") or draft.explanation
    points = edits_dict.get("default_points") or edits_dict.get("points") or 1.0
    lesson_id = edits_dict.get("lesson_id") or (draft.lesson.public_id if draft.lesson else None)
    learning_obj = edits_dict.get("learning_objective")

    # Parse and prepare choices / answers
    raw_choices = edits_dict.get("choices")
    if raw_choices is None and draft.choices_json:
        try:
            raw_choices = json.loads(draft.choices_json)
        except Exception:
            raw_choices = None

    raw_answers = edits_dict.get("accepted_answers")
    if raw_answers is None and draft.answer_json:
        try:
            ans_parsed = json.loads(draft.answer_json)
            if isinstance(ans_parsed, dict):
                if "acceptable_answers" in ans_parsed:
                    raw_answers = ans_parsed["acceptable_answers"]
                elif "correct_choice_id" in ans_parsed and raw_choices:
                    c_id = ans_parsed["correct_choice_id"]
                    for c in raw_choices:
                        if c.get("id") == c_id:
                            c["is_correct"] = True
                elif "correct_choice_ids" in ans_parsed and raw_choices:
                    c_ids = set(ans_parsed["correct_choice_ids"])
                    for c in raw_choices:
                        if c.get("id") in c_ids:
                            c["is_correct"] = True
            elif isinstance(ans_parsed, list):
                raw_answers = ans_parsed
        except Exception:
            pass

    # Normalize choices format for create_question
    normalized_choices: list[dict[str, Any]] | None = None
    if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE") and isinstance(
        raw_choices, list
    ):
        normalized_choices = []
        for idx, c in enumerate(raw_choices, start=1):
            if isinstance(c, dict):
                normalized_choices.append(
                    {
                        "content": c.get("content") or c.get("text") or f"Option {idx}",
                        "is_correct": bool(c.get("is_correct", False)),
                        "position": int(c.get("position", idx)),
                        "is_fixed_position": bool(c.get("is_fixed_position", False)),
                    }
                )
            elif isinstance(c, str):
                normalized_choices.append(
                    {
                        "content": c,
                        "is_correct": (idx == 1),
                        "position": idx,
                        "is_fixed_position": False,
                    }
                )
        # Ensure at least 1 correct answer if not already marked
        if normalized_choices and not any(c["is_correct"] for c in normalized_choices):
            normalized_choices[0]["is_correct"] = True

    # Normalize accepted answers for SHORT_ANSWER
    normalized_answers: list[Any] | None = None
    if q_type == "SHORT_ANSWER":
        if isinstance(raw_answers, list):
            normalized_answers = raw_answers
        elif isinstance(raw_answers, str):
            normalized_answers = [raw_answers]
        elif draft.explanation:
            normalized_answers = [draft.explanation.split()[0]]
        else:
            normalized_answers = ["Answer"]

    reason = edits_dict.get("change_reason") or f"Approved from AI Question Draft {draft.public_id}"

    payload: dict[str, Any] = {
        "question_type": q_type,
        "difficulty": db_diff,
        "content": content,
        "explanation": explanation,
        "default_points": points,
        "lesson_id": lesson_id,
        "learning_objective": learning_obj,
        "choices": normalized_choices,
        "accepted_answers": normalized_answers,
        "provenance": {
            "source_type": "AI_GENERATED",
            "ai_model": "gemini-3.8-flash",
            "notes": f"Generated from AI Question Draft {draft.public_id}",
        },
        "change_reason": reason,
    }

    # Import and call create_question from question_bank_service
    from pwd301.services.question_bank_service import create_question

    question = create_question(
        actor=actor,
        course_id=draft.course.public_id,
        payload=payload,
        session=sess,
    )

    # Update draft record
    draft.review_state = "APPROVED"
    draft.approved_question_id = question.id
    draft.reviewed_by_user_id = actor.id
    draft.reviewed_at = utc_now()
    if edits_dict:
        if "content" in edits_dict:
            draft.content = edits_dict["content"]
        if "explanation" in edits_dict:
            draft.explanation = edits_dict["explanation"]
        if normalized_choices is not None:
            draft.choices_json = json.dumps(normalized_choices)

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    logger.info(
        "Successfully approved AI question draft %s into Question %s (Course: %s)",
        draft.public_id,
        question.public_id,
        draft.course.course_code,
    )
    return draft, question


def reject_question_draft(
    *,
    actor: User,
    draft_id: str | uuid.UUID,
    session: Session | scoped_session[Any] | None = None,
) -> AIGeneratedQuestionDraft:
    """Reject an AI question draft, recording review metadata and preventing approval.

    Enforces:
    - Actor authorization: managing instructor or admin.
    - State check: cannot reject an already APPROVED draft.
    - Review state set to 'REJECTED'.
    """
    sess = session or db.session
    draft = get_question_draft(actor=actor, draft_id=draft_id, session=sess)

    if draft.review_state == "APPROVED":
        raise AIValidationError("Cannot reject an already approved question draft.")

    draft.review_state = "REJECTED"
    draft.reviewed_by_user_id = actor.id
    draft.reviewed_at = utc_now()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    logger.info("Rejected AI question draft %s by user %s", draft.public_id, actor.id)
    return draft


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
    raise_out_of_scope: bool = False,
    session: Session | scoped_session[Any] | None = None,
    surface_hint: str | None = None,
) -> tuple[AIMessage, AIMessage]:
    """Send a user message, enforce 5-minute inactivity deadline, and generate AI response.

    Enforces:
    - AI-003: 5-minute inactivity session deadline.
    - Security screening: reject prompt injection / malicious platform attack patterns.
    - LMS Academic Scope: refuse out-of-scope non-academic queries.
    - Telemetry in 'ai_requests' recording correct scope_decision ('IN_SCOPE' vs 'OUT_OF_SCOPE')
      and status ('SUCCEEDED' vs 'REFUSED').
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

    # 2. Input validation
    if not content or not content.strip():
        raise AIValidationError("Message content cannot be empty.")

    sanitized_content = sanitize_prompt(content.strip())
    context_str = f"Context: {conv.context_type}"
    if conv.course:
        context_str += f", Course: {conv.course.title}"
    if surface_hint:
        context_str += f", Surface: {surface_hint}"

    # 3. Security & Scope Evaluation (Hybrid Filter: Pattern + AI Guardrail)
    gemini_client = get_gemini_client()
    scope_eval = classify_query_scope_hybrid(
        sanitized_content, context=context_str, client=gemini_client
    )

    if scope_eval.is_malicious:
        # Threat / Attack / Jailbreak detected: reject immediately and record refusal telemetry
        record_ai_telemetry(
            user_id=actor.id,
            conversation_id=conv.id,
            route_type="CLASSIFIER",
            prompt=sanitized_content[:250],
            status="REFUSED",
            latency_ms=0,
            scope_decision="OUT_OF_SCOPE",
            error_code="PROMPT_INJECTION_DETECTED",
            session=sess,
        )
        try:
            sess.commit()
        except Exception:
            sess.rollback()
        raise AIPromptInjectionError("Prompt contains disallowed instructions or patterns.")

    if not scope_eval.is_in_scope:
        # Out-of-scope query: record refusal telemetry
        record_ai_telemetry(
            user_id=actor.id,
            conversation_id=conv.id,
            route_type="CLASSIFIER",
            prompt=sanitized_content[:250],
            status="REFUSED",
            latency_ms=0,
            scope_decision="OUT_OF_SCOPE",
            error_code="OUT_OF_SCOPE",
            session=sess,
        )
        if raise_out_of_scope:
            try:
                sess.commit()
            except Exception:
                sess.rollback()
            raise AIOutOfScopeError(scope_eval.refusal_message)

        # In conversational UI, record user message and assistant refusal
        existing_seqs = [m.sequence_no for m in conv.messages]
        next_seq = max(existing_seqs, default=0) + 1
        now = utc_now()

        user_msg = AIMessage(
            conversation_id=conv.id,
            sender="USER",
            content=sanitized_content,
            sequence_no=next_seq,
            created_at=now,
        )
        sess.add(user_msg)

        inactivity_secs = _get_inactivity_seconds()
        conv.last_activity_at = now
        conv.expires_at = now + timedelta(seconds=inactivity_secs)

        assistant_msg = AIMessage(
            conversation_id=conv.id,
            sender="ASSISTANT",
            content=scope_eval.refusal_message,
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

    # 4. In-scope query: Calculate sequence numbers & record USER message
    existing_seqs = [m.sequence_no for m in conv.messages]
    next_seq = max(existing_seqs, default=0) + 1
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
