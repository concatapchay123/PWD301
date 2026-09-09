"""Question bank management and question authoring engine for PWD301.

Implements business logic for:
- Creating questions across 5 standard types (SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE,
  SHORT_ANSWER, ESSAY).
- Enforcing Bloom taxonomy difficulty (REMEMBER, UNDERSTAND, APPLY).
- Strict course scope and same-course lesson binding validation.
- Question bank search, filtering, and pagination.
- Lifecycle transitions: soft-delete (TRASH with 30-day retention) and restore to ACTIVE.
- Object-level authorization, student denial, and fail-closed security.
- ADR-002 internal BIGINT PK masking (public_id, choice_key UUIDs).
- Append-only AuditEvent logging for sensitive authoring actions.
"""

from __future__ import annotations

import datetime
import json
import math
import uuid
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.course import Lesson
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import (
    Question,
    QuestionProvenance,
    QuestionRevision,
    QuestionRevisionAcceptedAnswer,
    QuestionRevisionChoice,
)
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    _resolve_lesson,
    require_course_manager,
    require_question_manager,
)
from pwd301.services.exceptions import (
    LessonNotFoundError,
    QuestionStateViolationError,
    QuestionValidationError,
)

VALID_QUESTION_TYPES: set[str] = {
    "SINGLE_CHOICE",
    "MULTIPLE_CHOICE",
    "TRUE_FALSE",
    "SHORT_ANSWER",
    "ESSAY",
}

VALID_DIFFICULTIES: set[str] = {
    "REMEMBER",
    "UNDERSTAND",
    "APPLY",
}

VALID_STATUSES: set[str] = {
    "DRAFT",
    "ACTIVE",
    "RETIRED",
    "TRASH",
}

VALID_PROVENANCE_TYPES: set[str] = {
    "MANUAL",
    "IMPORT",
    "AI_GENERATED",
    "DUPLICATED",
}


def _record_question_audit(
    sess: Session | scoped_session[Any],
    actor: User,
    action: str,
    target_id: int,
    reason: str | None = None,
    before_json: str | None = None,
    after_json: str | None = None,
) -> AuditEvent:
    """Helper to record an append-only AuditEvent for question authoring actions."""
    actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "UNKNOWN"
    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot=actor_roles,
        action=action,
        target_type="QUESTION",
        target_id=target_id,
        reason=reason,
        before_json=before_json,
        after_json=after_json,
        performed_as_admin=actor.is_admin,
        created_at=utc_now(),
    )
    sess.add(audit_entry)
    return audit_entry


def _validate_points(default_points: Any) -> Decimal:
    """Validate that points is a positive real number."""
    if default_points is None:
        return Decimal("1.0")

    try:
        val = Decimal(str(default_points))
    except Exception as err:
        raise QuestionValidationError("default_points must be a valid positive number.") from err

    if val <= 0:
        raise QuestionValidationError("default_points must be greater than zero.")

    return val


def _serialize_question(
    question: Question,
    revision: QuestionRevision | None = None,
    include_answers: bool = True,
) -> dict[str, Any]:
    """Serialize a Question entity into an API dictionary masking BIGINT PKs (ADR-002)."""
    rev = revision or question.current_revision
    sess = sa.inspect(question).session or db.session

    # Fetch provenance if exists
    prov = (
        sess.query(QuestionProvenance)
        .filter(QuestionProvenance.question_id == question.id)
        .order_by(QuestionProvenance.id.desc())
        .first()
    )

    choices_data: list[dict[str, Any]] = []
    if rev and rev.choices:
        sorted_choices = sorted(rev.choices, key=lambda c: c.position)
        choices_data = [
            {
                "choice_id": str(c.choice_key),
                "choice_key": str(c.choice_key),
                "content": c.content,
                "is_correct": c.is_correct if include_answers else None,
                "position": c.position,
                "is_fixed_position": bool(c.is_fixed_position),
            }
            for c in sorted_choices
        ]

    accepted_answers_data: list[dict[str, Any]] = []
    if rev and rev.accepted_answers:
        sorted_answers = sorted(rev.accepted_answers, key=lambda a: a.position)
        accepted_answers_data = [
            {
                "answer_text": a.answer_text if include_answers else None,
                "answer_normalized": a.answer_normalized if include_answers else None,
                "position": a.position,
            }
            for a in sorted_answers
        ]

    return {
        "public_id": str(question.public_id),
        "question_id": str(question.public_id),
        "course_id": str(question.course.public_id) if question.course else None,
        "lesson_id": str(question.lesson.public_id) if question.lesson else None,
        "difficulty": question.difficulty,
        "learning_objective": question.learning_objective,
        "status": question.status,
        "usage_count": question.usage_count,
        "default_points": 1.0,
        "choices": choices_data,
        "accepted_answers": accepted_answers_data,
        "created_at": question.created_at.isoformat() if question.created_at else None,
        "updated_at": question.updated_at.isoformat() if question.updated_at else None,
        "deleted_at": question.deleted_at.isoformat() if question.deleted_at else None,
        "restore_until": question.restore_until.isoformat() if question.restore_until else None,
        "current_revision": (
            {
                "revision_no": rev.revision_no,
                "question_type": rev.question_type,
                "content": rev.content,
                "explanation": rev.explanation,
                "short_answer_match_mode": rev.short_answer_match_mode,
                "change_type": rev.change_type,
                "was_student_exposed": bool(rev.was_student_exposed),
                "was_used_for_grading": bool(rev.was_used_for_grading),
                "choices": choices_data,
                "accepted_answers": accepted_answers_data,
            }
            if rev
            else None
        ),
        "provenance": (
            {
                "source_type": prov.source_type,
                "notes": prov.notes,
                "ai_model": prov.ai_model,
            }
            if prov
            else {"source_type": "MANUAL", "notes": None, "ai_model": None}
        ),
    }


def create_question(
    actor: User,
    course_id: int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> Question:
    """Create a new Question with Revision 1, choices/accepted answers, and provenance.

    Args:
        actor: Authenticated instructor or admin user.
        course_id: Target Course internal ID, public UUID, or string.
        payload: Question creation metadata and content.
        session: Optional SQLAlchemy session.

    Returns:
        Created Question instance.

    Raises:
        ForbiddenError: If actor cannot manage the course.
        QuestionValidationError: If payload fails validation.
    """
    sess = session if session is not None else db.session

    # 1. Authorize actor
    course = require_course_manager(actor, course_id, session=sess)

    # 2. Extract & Validate Question Type
    raw_type = payload.get("question_type") or payload.get("type")
    if not raw_type or not isinstance(raw_type, str):
        raise QuestionValidationError("Question type is required.")

    question_type = raw_type.strip().upper()
    if question_type not in VALID_QUESTION_TYPES:
        valid_types = ", ".join(sorted(VALID_QUESTION_TYPES))
        raise QuestionValidationError(
            f"Invalid question type '{question_type}'. Must be one of {valid_types}."
        )

    # 3. Extract & Validate Bloom Difficulty
    raw_diff = payload.get("difficulty")
    if not raw_diff or not isinstance(raw_diff, str):
        raise QuestionValidationError("Difficulty is required.")

    difficulty = raw_diff.strip().upper()
    if difficulty not in VALID_DIFFICULTIES:
        valid_diffs = ", ".join(sorted(VALID_DIFFICULTIES))
        raise QuestionValidationError(
            f"Invalid difficulty '{difficulty}'. Must be one of {valid_diffs}."
        )

    # 4. Extract & Validate Content / Stem
    content = payload.get("content") or payload.get("stem")
    if not content or not isinstance(content, str) or not content.strip():
        raise QuestionValidationError("Question content cannot be empty.")
    content = content.strip()

    # 5. Extract & Validate Points
    _validate_points(payload.get("default_points") or payload.get("points"))

    # 6. Extract & Validate Lesson Linkage
    lesson_id_val = payload.get("lesson_id") or payload.get("primary_lesson_id")
    target_lesson: Lesson | None = None
    if lesson_id_val is not None:
        target_lesson = _resolve_lesson(lesson_id_val, session=sess)
        if target_lesson is None:
            raise LessonNotFoundError("Specified lesson not found.")
        if target_lesson.course_id != course.id:
            raise QuestionValidationError("Lesson does not belong to the specified course.")

    # 7. Validate Choices & Accepted Answers per Question Type
    raw_choices = payload.get("choices") or []
    raw_accepted_answers = payload.get("accepted_answers") or []
    raw_explanation = payload.get("explanation")
    explanation = (
        raw_explanation.strip()
        if isinstance(raw_explanation, str) and raw_explanation.strip()
        else None
    )
    learning_objective = payload.get("learning_objective") or payload.get("topic")
    if isinstance(learning_objective, str):
        learning_objective = learning_objective.strip() or None

    parsed_choices: list[dict[str, Any]] = []
    parsed_answers: list[dict[str, Any]] = []
    short_answer_match_mode: str | None = None

    if question_type == "SINGLE_CHOICE":
        if not isinstance(raw_choices, list) or len(raw_choices) < 2:
            raise QuestionValidationError("SINGLE_CHOICE questions must have at least 2 choices.")
        if raw_accepted_answers:
            raise QuestionValidationError("SINGLE_CHOICE questions cannot accept text answers.")

        correct_count = 0
        for idx, c in enumerate(raw_choices, start=1):
            if not isinstance(c, dict):
                raise QuestionValidationError("Each choice must be an object.")
            c_text = c.get("content") or c.get("text")
            if not c_text or not isinstance(c_text, str) or not c_text.strip():
                raise QuestionValidationError(f"Choice {idx} content cannot be empty.")
            is_corr = bool(c.get("is_correct", False))
            if is_corr:
                correct_count += 1
            parsed_choices.append(
                {
                    "content": c_text.strip(),
                    "is_correct": is_corr,
                    "position": int(c.get("position", idx)),
                    "is_fixed_position": bool(c.get("is_fixed_position", False)),
                }
            )

        if correct_count != 1:
            raise QuestionValidationError(
                "SINGLE_CHOICE questions must have exactly 1 correct answer "
                f"(found {correct_count})."
            )

    elif question_type == "MULTIPLE_CHOICE":
        if not isinstance(raw_choices, list) or len(raw_choices) < 2:
            raise QuestionValidationError("MULTIPLE_CHOICE questions must have at least 2 choices.")
        if raw_accepted_answers:
            raise QuestionValidationError("MULTIPLE_CHOICE questions cannot accept text answers.")

        correct_count = 0
        for idx, c in enumerate(raw_choices, start=1):
            if not isinstance(c, dict):
                raise QuestionValidationError("Each choice must be an object.")
            c_text = c.get("content") or c.get("text")
            if not c_text or not isinstance(c_text, str) or not c_text.strip():
                raise QuestionValidationError(f"Choice {idx} content cannot be empty.")
            is_corr = bool(c.get("is_correct", False))
            if is_corr:
                correct_count += 1
            parsed_choices.append(
                {
                    "content": c_text.strip(),
                    "is_correct": is_corr,
                    "position": int(c.get("position", idx)),
                    "is_fixed_position": bool(c.get("is_fixed_position", False)),
                }
            )

        if correct_count < 1:
            raise QuestionValidationError(
                "MULTIPLE_CHOICE questions must have at least 1 correct answer."
            )

    elif question_type == "TRUE_FALSE":
        if not isinstance(raw_choices, list) or len(raw_choices) != 2:
            raise QuestionValidationError("TRUE_FALSE questions must have exactly 2 choices.")
        if raw_accepted_answers:
            raise QuestionValidationError("TRUE_FALSE questions cannot accept text answers.")

        correct_count = 0
        for idx, c in enumerate(raw_choices, start=1):
            if not isinstance(c, dict):
                raise QuestionValidationError("Each choice must be an object.")
            c_text = c.get("content") or c.get("text")
            if not c_text or not isinstance(c_text, str) or not c_text.strip():
                raise QuestionValidationError(f"Choice {idx} content cannot be empty.")
            is_corr = bool(c.get("is_correct", False))
            if is_corr:
                correct_count += 1
            parsed_choices.append(
                {
                    "content": c_text.strip(),
                    "is_correct": is_corr,
                    "position": int(c.get("position", idx)),
                    "is_fixed_position": bool(c.get("is_fixed_position", False)),
                }
            )

        if correct_count != 1:
            raise QuestionValidationError(
                "TRUE_FALSE questions must have exactly 1 correct answer."
            )

    elif question_type == "SHORT_ANSWER":
        if raw_choices:
            raise QuestionValidationError("SHORT_ANSWER questions cannot have choices.")
        if not isinstance(raw_accepted_answers, list) or len(raw_accepted_answers) < 1:
            raise QuestionValidationError(
                "SHORT_ANSWER questions must have at least 1 accepted answer."
            )

        # Determine short_answer_match_mode
        match_type = payload.get("match_type") or payload.get("short_answer_match_mode")
        is_case_sensitive = payload.get("is_case_sensitive", False)
        if match_type:
            mt_upper = str(match_type).strip().upper()
            if mt_upper not in {"EXACT", "CONTAINS", "REGEX", "NORMALIZED"}:
                raise QuestionValidationError(
                    f"Invalid match_type '{match_type}'. "
                    "Must be EXACT, CONTAINS, REGEX, or NORMALIZED."
                )
            if mt_upper == "EXACT" or is_case_sensitive:
                short_answer_match_mode = "EXACT"
            else:
                short_answer_match_mode = "NORMALIZED"
        else:
            short_answer_match_mode = "EXACT" if is_case_sensitive else "NORMALIZED"

        seen_normalized: set[str] = set()
        pos = 1
        for idx, ans in enumerate(raw_accepted_answers, start=1):
            if isinstance(ans, str):
                ans_text = ans.strip()
            elif isinstance(ans, dict):
                ans_text = str(ans.get("answer_text") or ans.get("text") or "").strip()
            else:
                raise QuestionValidationError(f"Accepted answer {idx} must be a string or object.")

            if not ans_text:
                raise QuestionValidationError(f"Accepted answer {idx} text cannot be empty.")

            norm = ans_text.lower()
            if norm in seen_normalized:
                continue
            seen_normalized.add(norm)
            parsed_answers.append(
                {
                    "answer_text": ans_text,
                    "answer_normalized": norm,
                    "position": pos,
                }
            )
            pos += 1

    elif question_type == "ESSAY":
        if raw_choices:
            raise QuestionValidationError("ESSAY questions cannot have choices.")
        if raw_accepted_answers:
            raise QuestionValidationError(
                "ESSAY questions cannot have predefined accepted answers."
            )

    # 8. Extract Provenance Information
    prov_dict = payload.get("provenance") or {}
    source_type = (
        payload.get("provenance_type") or prov_dict.get("source_type") or "MANUAL"
    ).upper()
    if source_type not in VALID_PROVENANCE_TYPES:
        valid_provs = ", ".join(sorted(VALID_PROVENANCE_TYPES))
        raise QuestionValidationError(
            f"Invalid provenance source_type '{source_type}'. Must be one of {valid_provs}."
        )

    # 9. Create Question Record
    status = payload.get("status", "ACTIVE").upper()
    if status not in VALID_STATUSES:
        raise QuestionValidationError(
            f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}."
        )

    question = Question(
        course_id=course.id,
        lesson_id=target_lesson.id if target_lesson else None,
        creator_user_id=actor.id,
        difficulty=difficulty,
        learning_objective=learning_objective,
        status=status,
        usage_count=0,
    )
    sess.add(question)
    sess.flush()

    # 10. Create QuestionRevision Record (Revision 1)
    revision = QuestionRevision(
        question_id=question.id,
        revision_no=1,
        question_type=question_type,
        content=content,
        explanation=explanation,
        short_answer_match_mode=short_answer_match_mode,
        change_type="INITIAL",
        change_reason=payload.get("change_reason", "Initial question authoring"),
        created_by_user_id=actor.id,
        approved_by_user_id=actor.id,
        approved_at=utc_now(),
        was_student_exposed=False,
        was_used_for_grading=False,
    )
    sess.add(revision)
    sess.flush()

    # Point current_revision_id to the created revision
    question.current_revision_id = revision.id

    # 11. Create Choices
    for c_data in parsed_choices:
        choice = QuestionRevisionChoice(
            question_revision_id=revision.id,
            choice_key=uuid.uuid4(),
            content=c_data["content"],
            is_correct=c_data["is_correct"],
            position=c_data["position"],
            is_fixed_position=c_data["is_fixed_position"],
        )
        sess.add(choice)

    # 12. Create Accepted Answers
    for a_data in parsed_answers:
        answer = QuestionRevisionAcceptedAnswer(
            question_revision_id=revision.id,
            answer_text=a_data["answer_text"],
            answer_normalized=a_data["answer_normalized"],
            position=a_data["position"],
        )
        sess.add(answer)

    # 13. Create Provenance Record
    provenance = QuestionProvenance(
        question_id=question.id,
        question_revision_id=revision.id,
        source_type=source_type,
        notes=prov_dict.get("notes") or payload.get("notes"),
        ai_model=prov_dict.get("ai_model"),
        approved_by_user_id=actor.id,
        approved_at=utc_now(),
    )
    sess.add(provenance)

    # 14. Ghi Append-only AuditEvent
    after_data = {
        "course_id": str(course.public_id),
        "question_id": str(question.public_id),
        "revision_no": 1,
        "question_type": question_type,
        "difficulty": difficulty,
    }
    _record_question_audit(
        sess=sess,
        actor=actor,
        action="QUESTION_CREATED",
        target_id=question.id,
        reason=payload.get("change_reason") or "Initial question creation",
        after_json=json.dumps(after_data),
    )
    sess.flush()

    return question


def list_course_questions(
    actor: User,
    course_id: int | uuid.UUID | str,
    filters: dict[str, Any] | None = None,
    page: int = 1,
    per_page: int = 20,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[list[dict[str, Any]], int, int, int, int]:
    """List questions in a course with filtering and pagination.

    Args:
        actor: Authenticated instructor or admin user.
        course_id: Course identifier.
        filters: Optional dictionary containing:
            - difficulty: REMEMBER, UNDERSTAND, APPLY
            - question_type: SINGLE_CHOICE, MULTIPLE_CHOICE, ...
            - lesson_id: target lesson identifier
            - status: ACTIVE, TRASH, etc. (default excludes TRASH)
            - search: string to search in content or learning_objective
        page: 1-indexed page number.
        per_page: Number of questions per page (1 to 100).
        session: Optional SQLAlchemy session.

    Returns:
        Tuple of (items, total_count, page, per_page, total_pages).

    Raises:
        ForbiddenError: If actor lacks permission.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    flt = filters or {}
    query = (
        sess.query(Question)
        .join(QuestionRevision, Question.current_revision_id == QuestionRevision.id)
        .filter(Question.course_id == course.id)
    )

    # 1. Filter by Status
    status_filter = flt.get("status")
    if status_filter:
        s_upper = str(status_filter).strip().upper()
        query = query.filter(Question.status == s_upper)
    else:
        # Default: exclude TRASH questions unless explicitly asked
        query = query.filter(Question.status != "TRASH")

    # 2. Filter by Difficulty
    diff_filter = flt.get("difficulty")
    if diff_filter and str(diff_filter).upper() != "ALL":
        d_upper = str(diff_filter).strip().upper()
        query = query.filter(Question.difficulty == d_upper)

    # 3. Filter by Question Type
    type_filter = flt.get("question_type") or flt.get("type")
    if type_filter and str(type_filter).upper() != "ALL":
        t_upper = str(type_filter).strip().upper()
        query = query.filter(QuestionRevision.question_type == t_upper)

    # 4. Filter by Lesson
    lesson_filter = flt.get("lesson_id")
    if lesson_filter:
        les = _resolve_lesson(lesson_filter, session=sess)
        query = query.filter(Question.lesson_id == les.id) if les else query.filter(sa.sql.false())

    # 5. Search keyword in content or learning_objective
    search_term = flt.get("search")
    if search_term and str(search_term).strip():
        term = f"%{str(search_term).strip()}%"
        query = query.filter(
            sa.or_(
                QuestionRevision.content.ilike(term),
                Question.learning_objective.ilike(term),
            )
        )

    # 6. Count total
    total_count = query.count()

    # 7. Pagination
    p = max(1, page)
    pp = max(1, min(100, per_page))
    total_pages = math.ceil(total_count / pp) if total_count > 0 else 1

    questions = (
        query.order_by(Question.created_at.desc(), Question.id.desc())
        .offset((p - 1) * pp)
        .limit(pp)
        .all()
    )

    items = [_serialize_question(q) for q in questions]
    return items, total_count, p, pp, total_pages


def get_question_detail(
    actor: User,
    question_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve full details of a Question including current revision, choices, and answers.

    Args:
        actor: Authenticated instructor or admin user.
        question_id: Question internal ID, public UUID, or string.
        session: Optional SQLAlchemy session.

    Returns:
        Serialized question dictionary adhering to ADR-002.

    Raises:
        QuestionNotFoundError: If question does not exist.
        ForbiddenError: If actor lacks permission.
    """
    sess = session if session is not None else db.session
    question = require_question_manager(actor, question_id, session=sess)
    return _serialize_question(question)


def trash_question(
    actor: User,
    question_id: int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Question:
    """Soft-delete a question by moving it to TRASH with a 30-day restore retention window.

    Args:
        actor: Authenticated instructor or admin user.
        question_id: Question identifier.
        reason: Optional reason for trashing.
        session: Optional SQLAlchemy session.

    Returns:
        Updated Question instance.

    Raises:
        QuestionNotFoundError: If question does not exist.
        ForbiddenError: If actor lacks permission.
    """
    sess = session if session is not None else db.session
    question = require_question_manager(actor, question_id, session=sess)

    # Idempotent check
    if question.status == "TRASH":
        return question

    now = utc_now()
    question.status = "TRASH"
    question.deleted_at = now
    question.deleted_by_user_id = actor.id
    question.restore_until = now + datetime.timedelta(days=30)

    # Ghi Append-only AuditEvent
    _record_question_audit(
        sess=sess,
        actor=actor,
        action="QUESTION_TRASHED",
        target_id=question.id,
        reason=reason or "Moved to trash",
        before_json=json.dumps({"status": "ACTIVE"}),
        after_json=json.dumps({"status": "TRASH", "question_id": str(question.public_id)}),
    )
    sess.flush()

    return question


def restore_question(
    actor: User,
    question_id: int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Question:
    """Restore a question from TRASH back to ACTIVE status.

    Args:
        actor: Authenticated instructor or admin user.
        question_id: Question identifier.
        reason: Optional reason for restoration.
        session: Optional SQLAlchemy session.

    Returns:
        Updated Question instance.

    Raises:
        QuestionNotFoundError: If question does not exist.
        QuestionStateViolationError: If question cannot be restored.
        ForbiddenError: If actor lacks permission.
    """
    sess = session if session is not None else db.session
    question = require_question_manager(actor, question_id, session=sess)

    # Idempotent check
    if question.status == "ACTIVE":
        return question

    if question.status != "TRASH":
        raise QuestionStateViolationError(
            f"Cannot restore question with status '{question.status}'. "
            "Only TRASH questions can be restored."
        )

    question.status = "ACTIVE"
    question.deleted_at = None
    question.deleted_by_user_id = None
    question.restore_until = None

    # Ghi Append-only AuditEvent
    _record_question_audit(
        sess=sess,
        actor=actor,
        action="QUESTION_RESTORED",
        target_id=question.id,
        reason=reason or "Restored from trash",
        before_json=json.dumps({"status": "TRASH"}),
        after_json=json.dumps({"status": "ACTIVE", "question_id": str(question.public_id)}),
    )
    sess.flush()

    return question
