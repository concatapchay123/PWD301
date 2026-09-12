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

import contextlib
import datetime
import json
import math
import uuid
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.assessment import (
    Assessment,
    AssessmentQuestionAssignment,
    AssessmentQuestionPool,
)
from pwd301.models.attempt_regrade import (
    AttemptQuestion,
    QuestionCorrection,
)
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
    _resolve_question,
    require_course_manager,
    require_question_manager,
)
from pwd301.services.exceptions import (
    LessonNotFoundError,
    QuestionImmutableError,
    QuestionNotFoundError,
    QuestionRevisionNotFoundError,
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

VALID_REVISION_CHANGE_TYPES: set[str] = {
    "INITIAL",
    "TYPO_FIX",
    "ANSWER_CHANGE",
    "CONTENT_CHANGE",
    "REVOCATION",
    "EDIT",
    "ANSWER_ONLY",
    "CONTENT_OR_CHOICES",
}

VALID_CORRECTION_TYPES: set[str] = {
    "ANSWER_ONLY",
    "CONTENT_OR_CHOICES",
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


def _serialize_question_revision(
    rev: QuestionRevision,
    include_answers: bool = True,
    is_current: bool | None = None,
) -> dict[str, Any]:
    """Serialize a QuestionRevision entity into an API dictionary masking BIGINT PKs (ADR-002)."""
    question = rev.question
    active = rev.is_current if is_current is None else is_current
    status_str = "ACTIVE" if active else "SUPERSEDED"

    choices_data: list[dict[str, Any]] = []
    if rev.choices:
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
    if rev.accepted_answers:
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
        "question_id": str(question.public_id) if question else None,
        "revision_no": rev.revision_no,
        "question_type": rev.question_type,
        "content": rev.content,
        "stem": rev.content,
        "explanation": rev.explanation,
        "short_answer_match_mode": rev.short_answer_match_mode,
        "change_type": rev.change_type,
        "change_reason": rev.change_reason,
        "status": status_str,
        "was_student_exposed": bool(rev.was_student_exposed),
        "was_used_for_grading": bool(rev.was_used_for_grading),
        "choices": choices_data,
        "accepted_answers": accepted_answers_data,
        "created_at": rev.created_at.isoformat() if rev.created_at else None,
        "approved_at": rev.approved_at.isoformat() if rev.approved_at else None,
    }


def _serialize_question_correction(
    correction: QuestionCorrection,
) -> dict[str, Any]:
    """Serialize a QuestionCorrection entity into an API dictionary masking BIGINT PKs (ADR-002)."""
    question = correction.question
    from_rev = correction.from_revision
    to_rev = correction.to_revision
    actor = correction.actor

    synthetic_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.question_correction.{correction.id}")
    )

    return {
        "correction_id": synthetic_id,
        "question_id": str(question.public_id) if question else None,
        "from_revision_no": from_rev.revision_no if from_rev else None,
        "to_revision_no": to_rev.revision_no if to_rev else None,
        "correction_type": correction.correction_type,
        "status": correction.status,
        "reason": correction.reason,
        "effective_at": (correction.effective_at.isoformat() if correction.effective_at else None),
        "created_at": (correction.created_at.isoformat() if correction.created_at else None),
        "actor_id": str(actor.public_id) if actor else None,
    }


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
            _serialize_question_revision(rev, include_answers=include_answers, is_current=True)
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
    content = payload.get("content") or payload.get("content_text") or payload.get("stem")
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
        is_current=True,
    )
    sess.add(revision)
    sess.flush()

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

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

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
        .join(
            QuestionRevision,
            sa.and_(
                Question.id == QuestionRevision.question_id,
                QuestionRevision.is_current == True,
            ),
        )
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
    if question.status in ("TRASH", "RETIRED"):
        return question

    now = utc_now()

    # Check if question has been used for grading (T-QB-05 / QBANK-005)
    was_used_for_grading = (
        sess.query(QuestionRevision.id)
        .filter(
            QuestionRevision.question_id == question.id,
            QuestionRevision.was_used_for_grading == True,
        )
        .first()
        is not None
    )
    if not was_used_for_grading:
        from pwd301.models.attempt_regrade import AttemptQuestion, AttemptQuestionGrade

        was_used_for_grading = (
            sess.query(AttemptQuestion.id)
            .join(
                AttemptQuestionGrade,
                AttemptQuestionGrade.attempt_question_id == AttemptQuestion.id,
            )
            .filter(AttemptQuestion.source_question_id == question.id)
            .first()
            is not None
        )

    if was_used_for_grading:
        old_status = question.status
        question.status = "RETIRED"
        question.deleted_at = now
        question.deleted_by_user_id = actor.id
        question.restore_until = None

        _record_question_audit(
            sess=sess,
            actor=actor,
            action="QUESTION_RETIRED",
            target_id=question.id,
            reason=reason or "Retired because question has historical grading records",
            before_json=json.dumps({"status": old_status}),
            after_json=json.dumps({"status": "RETIRED", "question_id": str(question.public_id)}),
        )
        sess.flush()
        if session is None:
            try:
                sess.commit()
            except Exception:
                sess.rollback()
                raise
        return question

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

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

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

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return question


def is_question_in_use(
    question_or_id: Question | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Determine whether a question is currently in use in assessments or attempts.

    A question is in-use if:
    1. It has appeared in an AttemptQuestion (any student attempt).
    2. It is assigned to a published Assessment (via AssessmentQuestionAssignment).
    3. It is part of an AssessmentQuestionPool for a published Assessment.
    4. Its usage_count > 0 or first_used_at is not None.
    5. Any of its revisions has was_student_exposed=True or was_used_for_grading=True.

    Args:
        question_or_id: Question instance, internal BIGINT id, UUID, or string.
        session: Optional SQLAlchemy session.

    Returns:
        True if the question has been used in assessments or attempts, False otherwise.

    Raises:
        QuestionNotFoundError: If the question does not exist.
    """
    sess = session if session is not None else db.session
    question = _resolve_question(question_or_id, session=sess)
    if question is None:
        raise QuestionNotFoundError("Question not found.")

    # 1. Check if question appeared in any attempt
    has_attempt = (
        sess.query(AttemptQuestion.id)
        .filter(AttemptQuestion.source_question_id == question.id)
        .first()
        is not None
    )
    if has_attempt:
        return True

    # 2. Check if assigned to a published Assessment
    has_published_assignment = (
        sess.query(AssessmentQuestionAssignment.id)
        .join(Assessment, AssessmentQuestionAssignment.assessment_id == Assessment.id)
        .filter(
            AssessmentQuestionAssignment.question_id == question.id,
            Assessment.status == "PUBLISHED",
            Assessment.deleted_at.is_(None),
        )
        .first()
        is not None
    )
    if has_published_assignment:
        return True

    # 3. Check if in question pool for a published Assessment
    has_published_pool = (
        sess.query(AssessmentQuestionPool.id)
        .join(Assessment, AssessmentQuestionPool.assessment_id == Assessment.id)
        .filter(
            AssessmentQuestionPool.question_id == question.id,
            Assessment.status == "PUBLISHED",
            Assessment.deleted_at.is_(None),
        )
        .first()
        is not None
    )
    if has_published_pool:
        return True

    # 4. Check question usage counters and student responses
    if (
        question.usage_count > 0
        or question.first_used_at is not None
        or question.first_answered_at is not None
    ):
        return True

    # 5. Check historical revision exposure flags
    has_exposed_revision = (
        sess.query(QuestionRevision.id)
        .filter(
            QuestionRevision.question_id == question.id,
            sa.or_(
                QuestionRevision.was_student_exposed == True,
                QuestionRevision.was_used_for_grading == True,
            ),
        )
        .first()
        is not None
    )
    return bool(has_exposed_revision)


def create_question_revision(
    actor: User,
    question_id: int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> tuple[QuestionRevision, QuestionCorrection | None]:
    """Create a new incremented revision for a question (ADR-003).

    Enforces:
    - Actor management authorization.
    - Incremented revision_no (latest.revision_no + 1).
    - In-use branching strategy:
      - If in-use: requires non-empty reason, locks question_type,
        and generates a linked QuestionCorrection record (PENDING)
        for ANSWER_CHANGE, CONTENT_CHANGE, or other correction types.
    - Deep cloning of choices and accepted answers when not overridden in payload.
    - Append-only AuditEvent logging (QUESTION_REVISED, QUESTION_CORRECTION_CREATED).

    Args:
        actor: Authenticated instructor or admin user.
        question_id: Question identifier.
        payload: Modification metadata, content, and choices/answers.
        session: Optional SQLAlchemy session.

    Returns:
        Created QuestionRevision instance.

    Raises:
        QuestionNotFoundError: If question does not exist.
        ForbiddenError: If actor lacks permission.
        QuestionStateViolationError: If question status is TRASH or RETIRED.
        QuestionValidationError: If payload fails validation.
        QuestionRevisionConflictError: If attempting to change question_type of an in-use question.
    """
    sess = session if session is not None else db.session
    question = require_question_manager(actor, question_id, session=sess)

    # 1. Lifecycle check
    if question.status in ("TRASH", "RETIRED"):
        raise QuestionStateViolationError(
            f"Cannot create revision for question in '{question.status}' status."
        )

    # 2. Get latest revision
    latest_rev = (
        sess.query(QuestionRevision)
        .filter(QuestionRevision.question_id == question.id)
        .order_by(QuestionRevision.revision_no.desc())
        .first()
    )
    if latest_rev is None:
        raise QuestionRevisionNotFoundError("No baseline revision exists for this question.")

    # 3. Detect in-use status
    in_use = is_question_in_use(question, session=sess)

    # 4. Extract and validate change_type
    raw_change_type = payload.get("change_type")
    if raw_change_type:
        change_type = str(raw_change_type).strip().upper()
    else:
        change_type = "CONTENT_CHANGE" if in_use else "EDIT"

    if change_type not in VALID_REVISION_CHANGE_TYPES:
        valid_types = ", ".join(sorted(VALID_REVISION_CHANGE_TYPES))
        raise QuestionValidationError(
            f"Invalid change_type '{change_type}'. Must be one of {valid_types}."
        )

    if change_type == "INITIAL":
        raise QuestionValidationError(
            "change_type 'INITIAL' is only valid for initial question authoring."
        )

    # 5. Handle reason and type locking when in-use
    # Check question_type immutability lock when student responses exist (T-QB-04 / QBANK-005)
    req_type = payload.get("question_type") or payload.get("type")
    if (
        question.first_answered_at is not None
        and req_type
        and str(req_type).strip().upper() != latest_rev.question_type
    ):
        raise QuestionStateViolationError(
            f"Cannot change question_type of question '{question.public_id}' after it has "
            "been answered by a student (first_answered_at is set). "
            f"Attempted to change from '{latest_rev.question_type}' to "
            f"'{str(req_type).strip().upper()}'."
        )

    raw_reason = payload.get("reason") or payload.get("change_reason")
    if in_use:
        if not raw_reason or not isinstance(raw_reason, str) or not raw_reason.strip():
            raise QuestionValidationError(
                "Reason is required when revising a question that is in use."
            )
        reason: str | None = raw_reason.strip()

        # Check question_type immutability lock for in-use questions
        if req_type and str(req_type).strip().upper() != latest_rev.question_type:
            raise QuestionImmutableError(
                f"Cannot change question_type of an in-use question from "
                f"'{latest_rev.question_type}' to '{str(req_type).strip().upper()}'. "
                "Question type is locked after assessment use."
            )
    else:
        reason = raw_reason.strip() if isinstance(raw_reason, str) and raw_reason.strip() else None

    # 6. Extract question-level metadata updates (difficulty, learning_objective)
    raw_diff = payload.get("difficulty")
    if raw_diff:
        diff_upper = str(raw_diff).strip().upper()
        if diff_upper not in VALID_DIFFICULTIES:
            valid_diffs = ", ".join(sorted(VALID_DIFFICULTIES))
            raise QuestionValidationError(
                f"Invalid difficulty '{diff_upper}'. Must be one of {valid_diffs}."
            )
        question.difficulty = diff_upper

    if "learning_objective" in payload:
        raw_lo = payload.get("learning_objective")
        question.learning_objective = str(raw_lo).strip() if raw_lo else None

    # 7. Extract stem / content
    raw_content = payload.get("content") or payload.get("stem")
    if raw_content is not None:
        if not isinstance(raw_content, str) or not raw_content.strip():
            raise QuestionValidationError("Question content cannot be empty.")
        content = raw_content.strip()
    else:
        content = latest_rev.content

    # 8. Extract explanation
    raw_explanation = payload.get("explanation")
    if raw_explanation is not None:
        explanation = (
            raw_explanation.strip()
            if isinstance(raw_explanation, str) and raw_explanation.strip()
            else None
        )
    else:
        explanation = latest_rev.explanation

    # 9. Question type
    req_type = payload.get("question_type") or payload.get("type")
    if req_type and not in_use:
        q_type = str(req_type).strip().upper()
        if q_type not in VALID_QUESTION_TYPES:
            valid_qtypes = ", ".join(sorted(VALID_QUESTION_TYPES))
            raise QuestionValidationError(
                f"Invalid question type '{q_type}'. Must be one of {valid_qtypes}."
            )
    else:
        q_type = latest_rev.question_type

    # 10. Process Choices and Accepted Answers
    parsed_choices: list[dict[str, Any]] = []
    parsed_answers: list[dict[str, Any]] = []
    short_answer_match_mode = latest_rev.short_answer_match_mode

    if q_type in ("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE"):
        if "choices" in payload:
            raw_choices = payload.get("choices")
            if not isinstance(raw_choices, list):
                raise QuestionValidationError("choices must be a list.")
            if q_type == "TRUE_FALSE" and len(raw_choices) != 2:
                raise QuestionValidationError("TRUE_FALSE questions must have exactly 2 choices.")
            if q_type != "TRUE_FALSE" and len(raw_choices) < 2:
                raise QuestionValidationError(f"{q_type} questions must have at least 2 choices.")

            existing_choices_by_pos = {c.position: c.choice_key for c in latest_rev.choices}
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
                pos = int(c.get("position", idx))
                raw_ck = c.get("choice_key")
                assigned_ck = None
                if raw_ck:
                    with contextlib.suppress(ValueError, AttributeError):
                        assigned_ck = uuid.UUID(str(raw_ck))
                if not assigned_ck:
                    assigned_ck = existing_choices_by_pos.get(pos) or uuid.uuid4()

                parsed_choices.append(
                    {
                        "choice_key": assigned_ck,
                        "content": c_text.strip(),
                        "is_correct": is_corr,
                        "position": pos,
                        "is_fixed_position": bool(c.get("is_fixed_position", False)),
                    }
                )

            if q_type in ("SINGLE_CHOICE", "TRUE_FALSE") and correct_count != 1:
                raise QuestionValidationError(
                    f"{q_type} questions must have exactly 1 correct answer "
                    f"(found {correct_count})."
                )
            if q_type == "MULTIPLE_CHOICE" and correct_count < 1:
                raise QuestionValidationError(
                    "MULTIPLE_CHOICE questions must have at least 1 correct answer."
                )
        else:
            # Clone from latest_rev choices preserving choice_key
            sorted_choices = sorted(latest_rev.choices, key=lambda c: c.position)
            parsed_choices = [
                {
                    "choice_key": c.choice_key,
                    "content": c.content,
                    "is_correct": c.is_correct,
                    "position": c.position,
                    "is_fixed_position": c.is_fixed_position,
                }
                for c in sorted_choices
            ]

    elif q_type == "SHORT_ANSWER":
        if "choices" in payload and payload["choices"]:
            raise QuestionValidationError("SHORT_ANSWER questions cannot have choices.")
        if "accepted_answers" in payload:
            raw_answers = payload.get("accepted_answers")
            if not isinstance(raw_answers, list) or len(raw_answers) < 1:
                raise QuestionValidationError(
                    "SHORT_ANSWER questions must have at least 1 accepted answer."
                )

            match_type = payload.get("match_type") or payload.get("short_answer_match_mode")
            is_case_sensitive = payload.get("is_case_sensitive", False)
            if match_type:
                mt_upper = str(match_type).strip().upper()
                if mt_upper not in {"EXACT", "CONTAINS", "REGEX", "NORMALIZED"}:
                    raise QuestionValidationError(
                        f"Invalid match_type '{match_type}'. "
                        "Must be EXACT, CONTAINS, REGEX, or NORMALIZED."
                    )
                short_answer_match_mode = (
                    "EXACT" if (mt_upper == "EXACT" or is_case_sensitive) else "NORMALIZED"
                )
            elif is_case_sensitive:
                short_answer_match_mode = "EXACT"

            seen_norm: set[str] = set()
            pos = 1
            for idx, ans in enumerate(raw_answers, start=1):
                if isinstance(ans, str):
                    ans_text = ans.strip()
                elif isinstance(ans, dict):
                    ans_text = str(ans.get("answer_text") or ans.get("text") or "").strip()
                else:
                    raise QuestionValidationError(
                        f"Accepted answer {idx} must be a string or object."
                    )
                if not ans_text:
                    raise QuestionValidationError(f"Accepted answer {idx} text cannot be empty.")
                norm = ans_text.lower()
                if norm in seen_norm:
                    continue
                seen_norm.add(norm)
                parsed_answers.append(
                    {
                        "answer_text": ans_text,
                        "answer_normalized": norm,
                        "position": pos,
                    }
                )
                pos += 1
        else:
            # Clone from latest_rev accepted_answers
            sorted_ans = sorted(latest_rev.accepted_answers, key=lambda a: a.position)
            parsed_answers = [
                {
                    "answer_text": a.answer_text,
                    "answer_normalized": a.answer_normalized,
                    "position": a.position,
                }
                for a in sorted_ans
            ]

    elif q_type == "ESSAY":
        if payload.get("choices"):
            raise QuestionValidationError("ESSAY questions cannot have choices.")
        if payload.get("accepted_answers"):
            raise QuestionValidationError(
                "ESSAY questions cannot have predefined accepted answers."
            )

    # 11. Create new QuestionRevision
    # Demote current revision(s)
    sess.query(QuestionRevision).filter(
        QuestionRevision.question_id == question.id,
        QuestionRevision.is_current == True,
    ).update({"is_current": False})

    new_revision_no = latest_rev.revision_no + 1
    new_revision = QuestionRevision(
        question_id=question.id,
        revision_no=new_revision_no,
        question_type=q_type,
        content=content,
        explanation=explanation,
        short_answer_match_mode=short_answer_match_mode,
        change_type=change_type,
        change_reason=reason,
        created_by_user_id=actor.id,
        approved_by_user_id=actor.id,
        approved_at=utc_now(),
        was_student_exposed=False,
        was_used_for_grading=False,
        is_current=True,
    )
    sess.add(new_revision)
    sess.flush()

    # 12. Create Choices
    for c_data in parsed_choices:
        choice = QuestionRevisionChoice(
            question_revision_id=new_revision.id,
            choice_key=c_data.get("choice_key") or uuid.uuid4(),
            content=c_data["content"],
            is_correct=c_data["is_correct"],
            position=c_data["position"],
            is_fixed_position=c_data.get("is_fixed_position", False),
        )
        sess.add(choice)

    # 13. Create Accepted Answers
    for a_data in parsed_answers:
        answer = QuestionRevisionAcceptedAnswer(
            question_revision_id=new_revision.id,
            answer_text=a_data["answer_text"],
            answer_normalized=a_data["answer_normalized"],
            position=a_data["position"],
        )
        sess.add(answer)

    # 14. Update Question timestamp
    question.updated_at = utc_now()

    # 15. Create QuestionCorrection if question was in-use and change requires correction
    correction_record: QuestionCorrection | None = None
    if in_use and change_type in {
        "ANSWER_CHANGE",
        "CONTENT_CHANGE",
        "ANSWER_ONLY",
        "CONTENT_OR_CHOICES",
        "TYPO_FIX",
        "REVOCATION",
    }:
        raw_corr_type = payload.get("correction_type")
        if raw_corr_type:
            corr_upper = str(raw_corr_type).strip().upper()
            if corr_upper not in VALID_CORRECTION_TYPES:
                raise QuestionValidationError(
                    f"correction_type must be one of {sorted(VALID_CORRECTION_TYPES)}."
                )
            correction_type = corr_upper
        else:
            if change_type in ("ANSWER_CHANGE", "ANSWER_ONLY"):
                correction_type = "ANSWER_ONLY"
            else:
                correction_type = "CONTENT_OR_CHOICES"

        correction_record = QuestionCorrection(
            question_id=question.id,
            from_revision_id=latest_rev.id,
            to_revision_id=new_revision.id,
            correction_type=correction_type,
            effective_at=utc_now(),
            reason=reason or "Question correction",
            actor_user_id=actor.id,
            status="PENDING",
        )
        sess.add(correction_record)
        sess.flush()

        # Trigger RegradeJob creation for affected attempts
        from pwd301.services.regrade_worker import create_or_get_regrade_job

        create_or_get_regrade_job(correction_record.id, session=sess)

        # Record AuditEvent QUESTION_CORRECTION_CREATED
        _record_question_audit(
            sess=sess,
            actor=actor,
            action="QUESTION_CORRECTION_CREATED",
            target_id=question.id,
            reason=reason,
            after_json=json.dumps(
                {
                    "question_id": str(question.public_id),
                    "from_revision_no": latest_rev.revision_no,
                    "to_revision_no": new_revision.revision_no,
                    "correction_type": correction_type,
                    "status": "PENDING",
                }
            ),
        )

    # 16. Record AuditEvent QUESTION_REVISED
    _record_question_audit(
        sess=sess,
        actor=actor,
        action="QUESTION_REVISED",
        target_id=question.id,
        reason=reason or "Question revised",
        before_json=json.dumps({"current_revision_no": latest_rev.revision_no}),
        after_json=json.dumps(
            {
                "question_id": str(question.public_id),
                "new_revision_no": new_revision.revision_no,
                "change_type": change_type,
                "in_use": in_use,
                "correction_created": bool(correction_record),
            }
        ),
    )
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return new_revision, correction_record


def update_question(
    actor: User,
    question_id: int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> Question:
    """Update question metadata or edit content adhering to the Freeze Revision Invariant.

    If question is in-use:
    - In-place mutation of content/choices/answers is strictly forbidden
      and raises QuestionImmutableError.
    - If payload explicitly requests a new revision (create_revision=True), creates one.

    If question is unused:
    - Allows in-place editing of current revision content, choices, or answers.
    """
    sess = session if session is not None else db.session
    question = require_question_manager(actor, question_id, session=sess)

    if question.status in ("TRASH", "RETIRED"):
        raise QuestionStateViolationError(f"Cannot update question in '{question.status}' status.")

    in_use = is_question_in_use(question, session=sess)
    has_content_edits = any(
        k in payload
        for k in (
            "content",
            "stem",
            "choices",
            "accepted_answers",
            "question_type",
            "type",
            "explanation",
            "general_feedback",
        )
    )

    req_type = payload.get("question_type") or payload.get("type")
    latest_rev = question.current_revision

    if (
        question.first_answered_at is not None
        and req_type is not None
        and latest_rev
        and str(req_type).strip().upper() != latest_rev.question_type
    ):
        raise QuestionStateViolationError(
            f"Cannot change question_type of question '{question.public_id}' after it has "
            "been answered by a student (first_answered_at is set). "
            f"Attempted to change from '{latest_rev.question_type}' to "
            f"'{str(req_type).strip().upper()}'."
        )

    if in_use and has_content_edits:
        if req_type and latest_rev and str(req_type).strip().upper() != latest_rev.question_type:
            raise QuestionImmutableError(
                f"Cannot change question_type of an in-use question from "
                f"'{latest_rev.question_type}' to '{str(req_type).strip().upper()}'. "
                "Question type is locked after assessment use."
            )

        raw_reason = payload.get("reason") or payload.get("change_reason")
        if not raw_reason or not isinstance(raw_reason, str) or not raw_reason.strip():
            raise QuestionValidationError(
                "change_reason is required when modifying a question that is in use."
            )

        new_rev, _ = create_question_revision(actor, question.id, payload, session=sess)
        sess.flush()
        return question

    # Metadata updates
    if "difficulty" in payload:
        diff_val = str(payload["difficulty"]).strip().upper()
        if diff_val not in VALID_DIFFICULTIES:
            raise QuestionValidationError(f"Invalid difficulty '{diff_val}'.")
        question.difficulty = diff_val

    if "learning_objective" in payload:
        raw_lo = payload.get("learning_objective")
        question.learning_objective = str(raw_lo).strip() if raw_lo else None

    # Handle lesson_id update and scope validation (QBANK-001)
    if "lesson_id" in payload or "primary_lesson_id" in payload:
        raw_lid = payload.get("lesson_id") or payload.get("primary_lesson_id")
        if raw_lid is not None:
            target_les = _resolve_lesson(raw_lid, session=sess)
            if target_les is None:
                raise LessonNotFoundError("Specified lesson not found.")
            if target_les.course_id != question.course_id:
                raise QuestionValidationError("Lesson does not belong to the specified course.")
            question.lesson_id = target_les.id
        else:
            question.lesson_id = None

    # In-place updates for unused question
    rev = question.current_revision
    if rev and has_content_edits:
        new_content = payload.get("content") or payload.get("stem")
        if new_content is not None:
            if not isinstance(new_content, str) or not new_content.strip():
                raise QuestionValidationError("Question content cannot be empty.")
            rev.content = new_content.strip()

        if "explanation" in payload or "general_feedback" in payload:
            raw_exp = payload.get("explanation") or payload.get("general_feedback")
            rev.explanation = str(raw_exp).strip() if raw_exp else None

        if "choices" in payload and rev.question_type in (
            "SINGLE_CHOICE",
            "MULTIPLE_CHOICE",
            "TRUE_FALSE",
        ):
            raw_choices = payload.get("choices")
            if not isinstance(raw_choices, list):
                raise QuestionValidationError("choices must be a list.")
            q_type = rev.question_type
            if q_type == "TRUE_FALSE" and len(raw_choices) != 2:
                raise QuestionValidationError("TRUE_FALSE questions must have exactly 2 choices.")
            if q_type != "TRUE_FALSE" and len(raw_choices) < 2:
                raise QuestionValidationError(f"{q_type} questions must have at least 2 choices.")

            existing_choices_by_pos = {c.position: c.choice_key for c in rev.choices}
            correct_count = 0
            parsed_choices = []
            for idx, c in enumerate(raw_choices, start=1):
                if not isinstance(c, dict):
                    raise QuestionValidationError("Each choice must be an object.")
                c_text = c.get("content") or c.get("text")
                if not c_text or not isinstance(c_text, str) or not c_text.strip():
                    raise QuestionValidationError(f"Choice {idx} content cannot be empty.")
                is_corr = bool(c.get("is_correct", False))
                if is_corr:
                    correct_count += 1
                pos = int(c.get("position", idx))
                raw_ck = c.get("choice_key")
                assigned_ck = None
                if raw_ck:
                    with contextlib.suppress(ValueError, AttributeError):
                        assigned_ck = uuid.UUID(str(raw_ck))
                if not assigned_ck:
                    assigned_ck = existing_choices_by_pos.get(pos) or uuid.uuid4()
                parsed_choices.append(
                    {
                        "choice_key": assigned_ck,
                        "content": c_text.strip(),
                        "is_correct": is_corr,
                        "position": pos,
                        "is_fixed_position": bool(c.get("is_fixed_position", False)),
                    }
                )

            if q_type in ("SINGLE_CHOICE", "TRUE_FALSE") and correct_count != 1:
                raise QuestionValidationError(
                    f"{q_type} questions must have exactly 1 correct answer "
                    f"(found {correct_count})."
                )
            if q_type == "MULTIPLE_CHOICE" and correct_count < 1:
                raise QuestionValidationError(
                    "MULTIPLE_CHOICE questions must have at least 1 correct answer."
                )

            sess.query(QuestionRevisionChoice).filter(
                QuestionRevisionChoice.question_revision_id == rev.id
            ).delete()
            for pc in parsed_choices:
                choice = QuestionRevisionChoice(
                    question_revision_id=rev.id,
                    choice_key=pc["choice_key"],
                    content=pc["content"],
                    is_correct=pc["is_correct"],
                    position=pc["position"],
                    is_fixed_position=pc["is_fixed_position"],
                )
                sess.add(choice)

        elif rev.question_type == "SHORT_ANSWER" and "accepted_answers" in payload:
            raw_answers = payload.get("accepted_answers")
            if not isinstance(raw_answers, list) or len(raw_answers) < 1:
                raise QuestionValidationError(
                    "SHORT_ANSWER questions must have at least 1 accepted answer."
                )
            match_type = payload.get("match_type") or payload.get("short_answer_match_mode")
            is_case_sensitive = payload.get("is_case_sensitive", False)
            if match_type:
                mt_upper = str(match_type).strip().upper()
                if mt_upper not in {"EXACT", "CONTAINS", "REGEX", "NORMALIZED"}:
                    raise QuestionValidationError(
                        f"Invalid match_type '{match_type}'. "
                        "Must be EXACT, CONTAINS, REGEX, or NORMALIZED."
                    )
                rev.short_answer_match_mode = (
                    "EXACT" if (mt_upper == "EXACT" or is_case_sensitive) else "NORMALIZED"
                )
            elif is_case_sensitive:
                rev.short_answer_match_mode = "EXACT"

            sess.query(QuestionRevisionAcceptedAnswer).filter(
                QuestionRevisionAcceptedAnswer.question_revision_id == rev.id
            ).delete()
            seen_norm: set[str] = set()
            pos = 1
            for idx, ans in enumerate(raw_answers, start=1):
                if isinstance(ans, str):
                    ans_text = ans.strip()
                elif isinstance(ans, dict):
                    ans_text = str(ans.get("answer_text") or ans.get("text") or "").strip()
                else:
                    raise QuestionValidationError(
                        f"Accepted answer {idx} must be a string or object."
                    )
                if not ans_text:
                    raise QuestionValidationError(f"Accepted answer {idx} cannot be empty.")

                norm_text = ans_text.lower()
                if norm_text in seen_norm:
                    continue
                seen_norm.add(norm_text)

                ans_record = QuestionRevisionAcceptedAnswer(
                    question_revision_id=rev.id,
                    answer_text=ans_text,
                    answer_normalized=norm_text,
                    position=pos,
                )
                sess.add(ans_record)
                pos += 1

    question.updated_at = utc_now()
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return question


def list_question_revisions(
    actor: User,
    question_id: int | uuid.UUID | str,
    page: int = 1,
    per_page: int = 20,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[list[dict[str, Any]], int, int, int, int]:
    """Retrieve all historical and current revisions for a question, ordered by revision_no DESC."""
    sess = session if session is not None else db.session
    question = require_question_manager(actor, question_id, session=sess)

    query = (
        sess.query(QuestionRevision)
        .filter(QuestionRevision.question_id == question.id)
        .order_by(QuestionRevision.revision_no.desc())
    )
    total_count = query.count()
    p = max(1, page)
    pp = max(1, min(100, per_page))
    total_pages = math.ceil(total_count / pp) if total_count > 0 else 1

    revisions = query.offset((p - 1) * pp).limit(pp).all()
    items = [_serialize_question_revision(r, include_answers=True) for r in revisions]
    return items, total_count, p, pp, total_pages


def get_question_revision_detail(
    actor: User,
    question_id: int | uuid.UUID | str,
    revision_no: int,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve full details of a specific question revision."""
    sess = session if session is not None else db.session
    question = require_question_manager(actor, question_id, session=sess)

    rev = (
        sess.query(QuestionRevision)
        .filter(
            QuestionRevision.question_id == question.id,
            QuestionRevision.revision_no == revision_no,
        )
        .first()
    )
    if rev is None:
        raise QuestionRevisionNotFoundError(
            f"Revision {revision_no} not found for question '{question.public_id}'."
        )

    return _serialize_question_revision(rev, include_answers=True)


def list_question_corrections(
    actor: User,
    question_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve all question correction incidents for a question."""
    sess = session if session is not None else db.session
    question = require_question_manager(actor, question_id, session=sess)

    corrections = (
        sess.query(QuestionCorrection)
        .filter(QuestionCorrection.question_id == question.id)
        .order_by(QuestionCorrection.created_at.desc(), QuestionCorrection.id.desc())
        .all()
    )
    return [_serialize_question_correction(c) for c in corrections]
