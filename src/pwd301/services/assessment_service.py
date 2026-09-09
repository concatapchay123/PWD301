"""Assessment management service for PWD301.

Implements business logic and invariants for:
- Assessment Lifecycle (DRAFT -> PUBLISHED -> CANCELLED / ARCHIVED -> TRASH)
- Section Management (AssessmentSection)
- Fixed Question Assignments (AssessmentQuestionAssignment)
- Blueprint Configuration & Algorithm 05 Candidate Pool Materialization
  (AssessmentBlueprint, AssessmentQuestionPool)
- Publish Rules Gate (AC-05: >= 1 question, total points > 0)
- Timing & Structure Freeze Invariants (ASSESS-001, ASSESS-002, ASSESS-003)
- ADR-002 BIGINT Primary Key Masking
- Append-Only Audit Logging (ASSESSMENT_CREATED, ASSESSMENT_UPDATED, ASSESSMENT_PUBLISHED,
  ASSESSMENT_CANCELLED, ASSESSMENT_TRASHED)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.assessment import (
    Assessment,
    AssessmentBlueprint,
    AssessmentBlueprintRule,
    AssessmentQuestionAssignment,
    AssessmentQuestionPool,
    AssessmentSection,
)
from pwd301.models.course import Course, Lesson
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.question_bank import Question, QuestionRevision
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    can_manage_course,
    require_course_manager,
)
from pwd301.services.course_service import _resolve_course
from pwd301.services.exceptions import (
    AssessmentLockedError,
    AssessmentNotFoundError,
    AssessmentSectionNotFoundError,
    AssessmentStateViolationError,
    AssessmentValidationError,
    BlueprintValidationError,
    QuestionNotFoundError,
    ResourceNotFoundError,
)
from pwd301.services.question_bank_service import _serialize_question

ALLOWED_ASSESSMENT_TYPES = {"PRACTICE", "QUIZ", "MIDTERM", "FINAL", "PLACEMENT"}
ALLOWED_SCORING_POLICIES = {"FIRST", "LATEST", "HIGHEST", "AVERAGE"}
ALLOWED_SCORE_RELEASE_POLICIES = {"IMMEDIATE", "AFTER_CLOSE", "INSTRUCTOR_RELEASE"}
ALLOWED_ANSWER_VISIBILITY_POLICIES = {
    "IMMEDIATE",
    "AFTER_CLOSE",
    "AFTER_ALL_ATTEMPTS",
    "NEVER",
}
ALLOWED_DIFFICULTIES = {"REMEMBER", "UNDERSTAND", "APPLY"}
ALLOWED_QUESTION_TYPES = {
    "SINGLE_CHOICE",
    "MULTIPLE_CHOICE",
    "TRUE_FALSE",
    "SHORT_ANSWER",
    "ESSAY",
}


# ============================================================================
# AUDIT LOGGING HELPER (Invariant 22)
# ============================================================================


def _record_assessment_audit(
    sess: Session | scoped_session[Any],
    actor: User,
    action: str,
    target_id: int,
    reason: str | None = None,
    before_json: str | None = None,
    after_json: str | None = None,
) -> AuditEvent:
    """Helper to record an append-only AuditEvent for assessment actions."""
    actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "UNKNOWN"
    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot=actor_roles,
        action=action,
        target_type="ASSESSMENT",
        target_id=target_id,
        reason=reason,
        before_json=before_json,
        after_json=after_json,
        performed_as_admin=actor.is_admin,
        created_at=utc_now(),
    )
    sess.add(audit_entry)
    return audit_entry


# ============================================================================
# ENTITY RESOLVERS
# ============================================================================


def _resolve_assessment(
    assessment_or_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any],
    include_deleted: bool = False,
) -> Assessment | None:
    """Resolve an Assessment instance by object, UUID public_id, or internal ID."""
    if isinstance(assessment_or_id, Assessment):
        return assessment_or_id

    query = session.query(Assessment)

    if isinstance(assessment_or_id, uuid.UUID):
        query = query.filter(Assessment.public_id == assessment_or_id)
    elif isinstance(assessment_or_id, int):
        query = query.filter(Assessment.id == assessment_or_id)
    elif isinstance(assessment_or_id, str):
        try:
            val_uuid = uuid.UUID(assessment_or_id)
            query = query.filter(Assessment.public_id == val_uuid)
        except ValueError:
            if assessment_or_id.isdigit():
                query = query.filter(Assessment.id == int(assessment_or_id))
            else:
                return None
    else:
        return None

    if not include_deleted:
        query = query.filter(
            Assessment.status != "TRASH",
            Assessment.deleted_at.is_(None),
        )

    return query.first()


def _resolve_section(
    assessment: Assessment,
    section_or_id: AssessmentSection | int | uuid.UUID | str,
) -> AssessmentSection | None:
    """Resolve a section belonging to this assessment by UUIDv5, int id, or position."""
    if isinstance(section_or_id, AssessmentSection):
        return section_or_id if section_or_id.assessment_id == assessment.id else None

    for s in assessment.sections:
        synthetic_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_section.{s.id}")
        if isinstance(section_or_id, uuid.UUID) and synthetic_uuid == section_or_id:
            return s
        if isinstance(section_or_id, str):
            if str(synthetic_uuid) == section_or_id:
                return s
            if section_or_id.isdigit() and (
                s.id == int(section_or_id) or s.position == int(section_or_id)
            ):
                return s
        elif isinstance(section_or_id, int):
            if s.id == section_or_id or s.position == section_or_id:
                return s

    return None


def _resolve_question(
    question_or_id: Question | int | uuid.UUID | str,
    session: Session | scoped_session[Any],
) -> Question | None:
    """Resolve a Question instance by object, UUID public_id, or internal ID."""
    if isinstance(question_or_id, Question):
        return question_or_id

    query = session.query(Question)
    if isinstance(question_or_id, uuid.UUID):
        return query.filter(Question.public_id == question_or_id).first()
    if isinstance(question_or_id, int):
        return query.filter(Question.id == question_or_id).first()
    if isinstance(question_or_id, str):
        try:
            val_uuid = uuid.UUID(question_or_id)
            return query.filter(Question.public_id == val_uuid).first()
        except ValueError:
            if question_or_id.isdigit():
                return query.filter(Question.id == int(question_or_id)).first()
            return None
    return None


# ============================================================================
# SERIALIZATION HELPERS (ADR-002)
# ============================================================================


def _serialize_section(section: AssessmentSection) -> dict[str, Any]:
    """Serialize an AssessmentSection masking BIGINT PK (ADR-002)."""
    synthetic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_section.{section.id}"))
    return {
        "section_id": synthetic_id,
        "position": section.position,
        "title": section.title,
        "instructions": section.instructions,
    }


def _serialize_assignment(assignment: AssessmentQuestionAssignment) -> dict[str, Any]:
    """Serialize an AssessmentQuestionAssignment masking BIGINT PK (ADR-002)."""
    synthetic_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_assignment.{assignment.id}")
    )
    section_id = (
        str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_section.{assignment.section_id}"))
        if assignment.section_id
        else None
    )
    return {
        "assignment_id": synthetic_id,
        "question_id": str(assignment.question.public_id) if assignment.question else None,
        "section_id": section_id,
        "position": assignment.position,
        "points": float(assignment.points),
        "is_mandatory": assignment.is_mandatory,
        "shuffle_choices_override": assignment.shuffle_choices_override,
        "source_type": assignment.source_type,
        "question": (
            _serialize_question(assignment.question, include_answers=False)
            if assignment.question
            else None
        ),
    }


def _serialize_blueprint_rule(rule: AssessmentBlueprintRule) -> dict[str, Any]:
    """Serialize an AssessmentBlueprintRule masking BIGINT PK (ADR-002)."""
    synthetic_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_blueprint_rule.{rule.id}")
    )
    section_id = (
        str(uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_section.{rule.section_id}"))
        if rule.section_id
        else None
    )
    return {
        "rule_id": synthetic_id,
        "position": rule.position,
        "lesson_id": str(rule.lesson.public_id) if rule.lesson else None,
        "section_id": section_id,
        "difficulty": rule.difficulty,
        "question_type": rule.question_type,
        "question_count": rule.question_count,
        "points_each": float(rule.points_each),
    }


def _serialize_blueprint(blueprint: AssessmentBlueprint) -> dict[str, Any]:
    """Serialize an AssessmentBlueprint masking BIGINT PK (ADR-002)."""
    synthetic_id = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, f"pwd301.assessment_blueprint.{blueprint.id}")
    )
    return {
        "blueprint_id": synthetic_id,
        "name": blueprint.name,
        "status": blueprint.status,
        "rules": [
            _serialize_blueprint_rule(r) for r in sorted(blueprint.rules, key=lambda r: r.position)
        ],
    }


def _calculate_assessment_aggregates(
    assessment: Assessment, session: Session | scoped_session[Any] | None = None
) -> tuple[int, float]:
    """Calculate the total questions count and total points for an assessment."""
    sess = session or db.session
    fixed_assignments = (
        sess.query(AssessmentQuestionAssignment)
        .filter(AssessmentQuestionAssignment.assessment_id == assessment.id)
        .all()
    )
    fixed_count = len(fixed_assignments)
    fixed_points = sum(float(a.points) for a in fixed_assignments)

    pool_items = (
        sess.query(AssessmentQuestionPool)
        .filter(AssessmentQuestionPool.assessment_id == assessment.id)
        .all()
    )
    pool_count = len(pool_items)
    pool_points = sum(float(p.points) for p in pool_items)

    if pool_count > 0:
        total_q = fixed_count + pool_count
        total_pts = fixed_points + pool_points
    else:
        blueprints = (
            sess.query(AssessmentBlueprint)
            .filter(AssessmentBlueprint.assessment_id == assessment.id)
            .all()
        )
        blueprint_count = sum(r.question_count for b in blueprints for r in b.rules)
        blueprint_points = sum(
            float(r.question_count * r.points_each) for b in blueprints for r in b.rules
        )
        total_q = fixed_count + blueprint_count
        total_pts = fixed_points + blueprint_points

    return total_q, round(total_pts, 4)


def _serialize_assessment(
    assessment: Assessment,
    full: bool = False,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Serialize Assessment conforming to ADR-002 and prompt schema contract."""
    questions_count, total_points = _calculate_assessment_aggregates(assessment, session=session)

    data: dict[str, Any] = {
        "assessment_id": str(assessment.public_id),
        "course_id": str(assessment.course.public_id) if assessment.course else None,
        "title": assessment.title,
        "assessment_type": assessment.assessment_type,
        "status": assessment.status,
        "time_limit_minutes": assessment.time_limit_minutes,
        "attempt_limit": assessment.attempt_limit,
        "scoring_policy": assessment.scoring_policy,
        "passing_percent": (
            float(assessment.passing_percent) if assessment.passing_percent is not None else None
        ),
        "is_locked_structure": assessment.first_attempt_started_at is not None,
        "total_points": total_points,
        "sections_count": len(assessment.sections),
        "questions_count": questions_count,
        "published_at": (assessment.published_at.isoformat() if assessment.published_at else None),
    }

    if full:
        data.update(
            {
                "description": assessment.description,
                "open_at": assessment.open_at.isoformat() if assessment.open_at else None,
                "close_at": (assessment.close_at.isoformat() if assessment.close_at else None),
                "is_required_for_completion": assessment.is_required_for_completion,
                "shuffle_questions": assessment.shuffle_questions,
                "shuffle_choices": assessment.shuffle_choices,
                "score_release_policy": assessment.score_release_policy,
                "answer_visibility_policy": assessment.answer_visibility_policy,
                "random_question_count": assessment.random_question_count,
                "first_attempt_started_at": (
                    assessment.first_attempt_started_at.isoformat()
                    if assessment.first_attempt_started_at
                    else None
                ),
                "cancelled_at": (
                    assessment.cancelled_at.isoformat() if assessment.cancelled_at else None
                ),
                "cancel_reason": assessment.cancel_reason,
                "created_at": (
                    assessment.created_at.isoformat() if assessment.created_at else None
                ),
                "updated_at": (
                    assessment.updated_at.isoformat() if assessment.updated_at else None
                ),
                "sections": [
                    _serialize_section(s)
                    for s in sorted(assessment.sections, key=lambda s: s.position)
                ],
                "questions": [
                    _serialize_assignment(a)
                    for a in sorted(assessment.question_assignments, key=lambda a: a.position)
                ],
                "blueprints": [_serialize_blueprint(b) for b in assessment.blueprints],
                "pool_count": len(assessment.question_pool),
            }
        )

    return data


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def _parse_iso_datetime(val: Any, field_name: str) -> datetime | None:
    """Safely parse an ISO-8601 datetime string to a timezone-aware UTC datetime."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=UTC)
        return val.astimezone(UTC)
    if isinstance(val, str):
        try:
            clean_str = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
        except ValueError as err:
            raise AssessmentValidationError(
                f"Field '{field_name}' must be a valid ISO-8601 datetime string."
            ) from err
    raise AssessmentValidationError(f"Field '{field_name}' must be an ISO datetime string or null.")


def _normalize_dt(val: Any) -> datetime | None:
    """Ensure a datetime is timezone-aware UTC datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=UTC)
        return val.astimezone(UTC)
    return None


def _validate_assessment_timings_and_limits(
    open_at: datetime | None,
    close_at: datetime | None,
    time_limit_minutes: int | None,
    attempt_limit: int | None,
    passing_percent: Decimal | None,
    random_question_count: int | None,
) -> None:
    """Validate cross-field timing and numeric limits (AC-02, BR-ASM-04)."""
    norm_open = _normalize_dt(open_at)
    norm_close = _normalize_dt(close_at)
    if norm_open is not None and norm_close is not None and norm_open >= norm_close:
        raise AssessmentValidationError("open_at must be strictly earlier than close_at.")

    if time_limit_minutes is not None and time_limit_minutes <= 0:
        raise AssessmentValidationError("time_limit_minutes must be greater than 0.")

    if attempt_limit is not None and attempt_limit <= 0:
        raise AssessmentValidationError("attempt_limit must be greater than 0.")

    if passing_percent is not None and (passing_percent < 0 or passing_percent > 100):
        raise AssessmentValidationError("passing_percent must be between 0 and 100.")

    if random_question_count is not None and random_question_count <= 0:
        raise AssessmentValidationError("random_question_count must be greater than 0.")


# ============================================================================
# SERVICE FUNCTIONS: ASSESSMENT LIFECYCLE
# ============================================================================


def create_assessment(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> Assessment:
    """Create a new Assessment in DRAFT status for a course."""
    sess = session if session is not None else db.session

    course = require_course_manager(actor, course_id, session=sess)

    raw_title = payload.get("title")
    if not raw_title or not str(raw_title).strip():
        raise AssessmentValidationError("Assessment title is required.")
    title = str(raw_title).strip()
    if len(title) > 200:
        raise AssessmentValidationError("Assessment title must not exceed 200 characters.")

    raw_type = str(payload.get("assessment_type", "")).strip().upper()
    if raw_type not in ALLOWED_ASSESSMENT_TYPES:
        types_str = ", ".join(sorted(ALLOWED_ASSESSMENT_TYPES))
        raise AssessmentValidationError(
            f"Invalid assessment_type '{raw_type}'. Allowed types: {types_str}"
        )

    scoring_policy = str(payload.get("scoring_policy", "HIGHEST")).strip().upper()
    if scoring_policy not in ALLOWED_SCORING_POLICIES:
        sp_str = ", ".join(sorted(ALLOWED_SCORING_POLICIES))
        raise AssessmentValidationError(
            f"Invalid scoring_policy '{scoring_policy}'. Allowed: {sp_str}"
        )

    score_release_policy = str(payload.get("score_release_policy", "IMMEDIATE")).strip().upper()
    if score_release_policy not in ALLOWED_SCORE_RELEASE_POLICIES:
        raise AssessmentValidationError(f"Invalid score_release_policy '{score_release_policy}'.")

    answer_visibility_policy = (
        str(payload.get("answer_visibility_policy", "AFTER_CLOSE")).strip().upper()
    )
    if answer_visibility_policy not in ALLOWED_ANSWER_VISIBILITY_POLICIES:
        raise AssessmentValidationError(
            f"Invalid answer_visibility_policy '{answer_visibility_policy}'."
        )

    open_at = _parse_iso_datetime(payload.get("open_at"), "open_at")
    close_at = _parse_iso_datetime(payload.get("close_at"), "close_at")

    def _parse_int_opt(key: str) -> int | None:
        val = payload.get(key)
        if val is None or val == "":
            return None
        try:
            return int(val)
        except (ValueError, TypeError) as err:
            raise AssessmentValidationError(f"Field '{key}' must be an integer.") from err

    time_limit_minutes = _parse_int_opt("time_limit_minutes")
    attempt_limit = _parse_int_opt("attempt_limit")
    random_question_count = _parse_int_opt("random_question_count")

    passing_percent: Decimal | None = None
    raw_pass = payload.get("passing_percent")
    if raw_pass is not None and raw_pass != "":
        try:
            passing_percent = Decimal(str(raw_pass))
        except Exception as err:
            raise AssessmentValidationError("Field 'passing_percent' must be numeric.") from err

    _validate_assessment_timings_and_limits(
        open_at=open_at,
        close_at=close_at,
        time_limit_minutes=time_limit_minutes,
        attempt_limit=attempt_limit,
        passing_percent=passing_percent,
        random_question_count=random_question_count,
    )

    assessment = Assessment(
        course_id=course.id,
        creator_user_id=actor.id,
        title=title,
        description=payload.get("description"),
        assessment_type=raw_type,
        status="DRAFT",
        open_at=open_at,
        close_at=close_at,
        time_limit_minutes=time_limit_minutes,
        attempt_limit=attempt_limit,
        scoring_policy=scoring_policy,
        passing_percent=passing_percent,
        is_required_for_completion=bool(payload.get("is_required_for_completion", False)),
        shuffle_questions=bool(payload.get("shuffle_questions", False)),
        shuffle_choices=bool(payload.get("shuffle_choices", False)),
        score_release_policy=score_release_policy,
        answer_visibility_policy=answer_visibility_policy,
        random_question_count=random_question_count,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    sess.add(assessment)
    sess.flush()

    _record_assessment_audit(
        sess=sess,
        actor=actor,
        action="ASSESSMENT_CREATED",
        target_id=assessment.id,
    )

    return assessment


def update_assessment(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> Assessment:
    """Update an Assessment configuration subject to Timing and Structure freeze rules."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    if assessment.status in ("CANCELLED", "ARCHIVED", "TRASH"):
        raise AssessmentStateViolationError(
            f"Cannot update assessment in terminal status '{assessment.status}'."
        )

    # 1. Structure Freeze Invariant check (AC-06)
    if assessment.first_attempt_started_at is not None:
        if (
            "assessment_type" in payload
            and payload["assessment_type"] != assessment.assessment_type
        ):
            raise AssessmentLockedError(
                "Assessment structure is locked after first student attempt started."
            )
        if (
            "random_question_count" in payload
            and payload["random_question_count"] != assessment.random_question_count
        ):
            raise AssessmentLockedError(
                "Assessment structure is locked after first student attempt started."
            )

    # 2. Timing Freeze Invariant check (ASSESS-001)
    is_published = assessment.status == "PUBLISHED" or assessment.published_at is not None
    if is_published:
        if "open_at" in payload:
            new_open = _parse_iso_datetime(payload.get("open_at"), "open_at")
            if _normalize_dt(new_open) != _normalize_dt(assessment.open_at):
                raise AssessmentLockedError("Assessment timing (open_at) is locked after publish.")

        if "time_limit_minutes" in payload:
            raw_tl = payload.get("time_limit_minutes")
            new_tl = int(raw_tl) if raw_tl is not None and raw_tl != "" else None
            if new_tl != assessment.time_limit_minutes:
                raise AssessmentLockedError(
                    "Assessment timing (time_limit_minutes) is locked after publish."
                )

        if "attempt_limit" in payload:
            raw_al = payload.get("attempt_limit")
            new_al = int(raw_al) if raw_al is not None and raw_al != "" else None
            if new_al != assessment.attempt_limit:
                raise AssessmentLockedError(
                    "Assessment timing (attempt_limit) is locked after publish."
                )

        if "close_at" in payload:
            new_close = _parse_iso_datetime(payload.get("close_at"), "close_at")
            cur_close = _normalize_dt(assessment.close_at)
            norm_new_close = _normalize_dt(new_close)
            if cur_close is not None and norm_new_close is not None and norm_new_close <= cur_close:
                raise AssessmentLockedError("close_at can only be extended forward after publish.")

    # Apply updates
    if "title" in payload:
        raw_title = str(payload["title"]).strip()
        if not raw_title:
            raise AssessmentValidationError("Assessment title cannot be empty.")
        if len(raw_title) > 200:
            raise AssessmentValidationError("Assessment title must not exceed 200 characters.")
        assessment.title = raw_title

    if "description" in payload:
        assessment.description = payload["description"]

    if "assessment_type" in payload and assessment.first_attempt_started_at is None:
        raw_type = str(payload["assessment_type"]).strip().upper()
        if raw_type not in ALLOWED_ASSESSMENT_TYPES:
            raise AssessmentValidationError(f"Invalid assessment_type '{raw_type}'.")
        assessment.assessment_type = raw_type

    if "scoring_policy" in payload:
        sp = str(payload["scoring_policy"]).strip().upper()
        if sp not in ALLOWED_SCORING_POLICIES:
            raise AssessmentValidationError(f"Invalid scoring_policy '{sp}'.")
        assessment.scoring_policy = sp

    if "score_release_policy" in payload:
        srp = str(payload["score_release_policy"]).strip().upper()
        if srp not in ALLOWED_SCORE_RELEASE_POLICIES:
            raise AssessmentValidationError(f"Invalid score_release_policy '{srp}'.")
        assessment.score_release_policy = srp

    if "answer_visibility_policy" in payload:
        avp = str(payload["answer_visibility_policy"]).strip().upper()
        if avp not in ALLOWED_ANSWER_VISIBILITY_POLICIES:
            raise AssessmentValidationError(f"Invalid answer_visibility_policy '{avp}'.")
        assessment.answer_visibility_policy = avp

    if "open_at" in payload and not is_published:
        assessment.open_at = _parse_iso_datetime(payload.get("open_at"), "open_at")

    if "close_at" in payload:
        assessment.close_at = _parse_iso_datetime(payload.get("close_at"), "close_at")

    if "time_limit_minutes" in payload and not is_published:
        raw_tl = payload.get("time_limit_minutes")
        assessment.time_limit_minutes = int(raw_tl) if raw_tl is not None and raw_tl != "" else None

    if "attempt_limit" in payload and not is_published:
        raw_al = payload.get("attempt_limit")
        assessment.attempt_limit = int(raw_al) if raw_al is not None and raw_al != "" else None

    if "passing_percent" in payload:
        raw_pass = payload.get("passing_percent")
        if raw_pass is not None and raw_pass != "":
            try:
                assessment.passing_percent = Decimal(str(raw_pass))
            except Exception as err:
                raise AssessmentValidationError("Field 'passing_percent' must be numeric.") from err
        else:
            assessment.passing_percent = None

    if "is_required_for_completion" in payload:
        assessment.is_required_for_completion = bool(payload["is_required_for_completion"])

    if "shuffle_questions" in payload:
        assessment.shuffle_questions = bool(payload["shuffle_questions"])

    if "shuffle_choices" in payload:
        assessment.shuffle_choices = bool(payload["shuffle_choices"])

    if "random_question_count" in payload and assessment.first_attempt_started_at is None:
        raw_rq = payload.get("random_question_count")
        assessment.random_question_count = (
            int(raw_rq) if raw_rq is not None and raw_rq != "" else None
        )

    _validate_assessment_timings_and_limits(
        open_at=assessment.open_at,
        close_at=assessment.close_at,
        time_limit_minutes=assessment.time_limit_minutes,
        attempt_limit=assessment.attempt_limit,
        passing_percent=assessment.passing_percent,
        random_question_count=assessment.random_question_count,
    )

    assessment.updated_at = utc_now()
    sess.flush()

    _record_assessment_audit(
        sess=sess,
        actor=actor,
        action="ASSESSMENT_UPDATED",
        target_id=assessment.id,
    )

    return assessment


def get_assessment_detail(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> dict[str, Any]:
    """Retrieve detailed assessment configuration with role-based visibility."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=True)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    is_manager = can_manage_course(actor, assessment.course_id, session=sess)

    if not is_manager and (
        assessment.status in ("DRAFT", "TRASH") or assessment.deleted_at is not None
    ):
        raise AssessmentNotFoundError("Assessment not found.")

    return _serialize_assessment(assessment, full=True)


def list_course_assessments(
    actor: User,
    course_id: Course | int | uuid.UUID | str,
    filters: dict[str, Any] | None = None,
    page: int = 1,
    per_page: int = 20,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[list[dict[str, Any]], int, int, int, int]:
    """List assessments for a course with pagination and role-based filtering."""
    sess = session if session is not None else db.session

    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    is_manager = can_manage_course(actor, course, session=sess)

    query = sess.query(Assessment).filter(Assessment.course_id == course.id)

    filters = filters or {}
    if not is_manager:
        query = query.filter(
            Assessment.status.notin_(["DRAFT", "TRASH"]),
            Assessment.deleted_at.is_(None),
        )
    else:
        req_status = filters.get("status")
        if req_status:
            query = query.filter(Assessment.status == req_status.upper())
        else:
            query = query.filter(
                Assessment.status != "TRASH",
                Assessment.deleted_at.is_(None),
            )

    req_type = filters.get("assessment_type") or filters.get("type")
    if req_type:
        query = query.filter(Assessment.assessment_type == req_type.upper())

    total = query.count()

    p = max(1, page)
    pp = min(max(1, per_page), 100)
    total_pages = max(1, (total + pp - 1) // pp) if total > 0 else 1

    assessments = query.order_by(Assessment.created_at.desc()).offset((p - 1) * pp).limit(pp).all()

    items = [_serialize_assessment(a) for a in assessments]
    return items, total, p, pp, total_pages


def publish_assessment(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Assessment:
    """Validate publish gate and transition Assessment from DRAFT to PUBLISHED (AC-05)."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    if assessment.status == "PUBLISHED":
        # State-idempotent per 07_ASSESSMENT_API.md
        return assessment

    if assessment.status in ("CANCELLED", "ARCHIVED", "TRASH"):
        raise AssessmentStateViolationError(
            f"Cannot publish assessment in status '{assessment.status}'."
        )

    # Publish Gate: at least 1 question assigned or materialized in pool (AC-05)
    questions_count, total_points = _calculate_assessment_aggregates(assessment, session=sess)
    if questions_count < 1:
        raise AssessmentValidationError(
            "Assessment must have at least one question assigned or in candidate "
            "pool before publishing."
        )

    if total_points <= 0:
        raise AssessmentValidationError(
            "Assessment total points must be greater than 0 before publishing."
        )

    if (
        assessment.open_at is not None
        and assessment.close_at is not None
        and assessment.open_at >= assessment.close_at
    ):
        raise AssessmentValidationError("open_at must be strictly before close_at.")

    assessment.status = "PUBLISHED"
    assessment.published_at = utc_now()
    assessment.updated_at = utc_now()

    # Freeze all associated blueprints
    for bp in assessment.blueprints:
        bp.status = "FROZEN"

    sess.flush()

    _record_assessment_audit(
        sess=sess,
        actor=actor,
        action="ASSESSMENT_PUBLISHED",
        target_id=assessment.id,
    )

    return assessment


def cancel_assessment(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Assessment:
    """Cancel a published Assessment."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    if assessment.status == "CANCELLED":
        return assessment

    if assessment.status != "PUBLISHED":
        raise AssessmentStateViolationError(
            f"Only PUBLISHED assessments can be cancelled (current status: '{assessment.status}')."
        )

    assessment.status = "CANCELLED"
    assessment.cancelled_at = utc_now()
    assessment.cancel_reason = reason
    assessment.updated_at = utc_now()
    sess.flush()

    _record_assessment_audit(
        sess=sess,
        actor=actor,
        action="ASSESSMENT_CANCELLED",
        target_id=assessment.id,
        reason=reason,
    )

    return assessment


def trash_assessment(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    reason: str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> Assessment:
    """Soft-delete an Assessment into TRASH with a 30-day restore window (AC-07)."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=True)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    if assessment.status == "TRASH":
        raise AssessmentStateViolationError("Assessment is already in trash.")

    now = utc_now()
    assessment.status = "TRASH"
    assessment.deleted_at = now
    assessment.restore_until = now + timedelta(days=30)
    assessment.deleted_by_user_id = actor.id
    assessment.updated_at = now
    sess.flush()

    _record_assessment_audit(
        sess=sess,
        actor=actor,
        action="ASSESSMENT_TRASHED",
        target_id=assessment.id,
        reason=reason,
    )

    return assessment


def restore_assessment(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Assessment:
    """Restore an Assessment from TRASH back to DRAFT within 30 days (AC-07)."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=True)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    if assessment.status != "TRASH":
        raise AssessmentStateViolationError("Assessment is not in trash.")

    if assessment.restore_until is not None:
        restore_dt = assessment.restore_until
        if restore_dt.tzinfo is None:
            restore_dt = restore_dt.replace(tzinfo=UTC)
        current_time = utc_now()
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=UTC)
        if current_time > restore_dt:
            raise AssessmentValidationError(
                "Assessment has passed the 30-day restore window and cannot be restored."
            )

    assessment.status = "DRAFT"
    assessment.deleted_at = None
    assessment.restore_until = None
    assessment.deleted_by_user_id = None
    assessment.updated_at = utc_now()
    sess.flush()

    _record_assessment_audit(
        sess=sess,
        actor=actor,
        action="ASSESSMENT_RESTORED",
        target_id=assessment.id,
    )

    return assessment


# ============================================================================
# SERVICE FUNCTIONS: SECTIONS MANAGEMENT
# ============================================================================


def create_section(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentSection:
    """Create a section container inside an assessment."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    # Structure Freeze Invariant check (AC-06)
    if assessment.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Assessment sections cannot be added after student attempt has started."
        )

    existing_positions = [s.position for s in assessment.sections]
    raw_pos = payload.get("position")
    if raw_pos is not None and raw_pos != "":
        try:
            pos = int(raw_pos)
            if pos <= 0:
                raise AssessmentValidationError("Section position must be > 0.")
        except (ValueError, TypeError) as err:
            raise AssessmentValidationError("Section position must be a positive integer.") from err
        if pos in existing_positions:
            for s in assessment.sections:
                if s.position >= pos:
                    s.position += 1
    else:
        pos = max(existing_positions, default=0) + 1

    section = AssessmentSection(
        assessment_id=assessment.id,
        title=payload.get("title"),
        position=pos,
        instructions=payload.get("instructions"),
    )
    sess.add(section)
    sess.flush()
    return section


def delete_section(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    section_id: AssessmentSection | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Delete a section from an assessment."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    # Structure Freeze Invariant check (AC-06)
    if assessment.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Assessment sections cannot be deleted after student attempt has started."
        )

    section = _resolve_section(assessment, section_id)
    if section is None:
        raise AssessmentSectionNotFoundError("Section not found in assessment.")

    deleted_pos = section.position
    sess.delete(section)
    sess.flush()

    # Re-normalize remaining section positions
    for s in assessment.sections:
        if s.id != section.id and s.position > deleted_pos:
            s.position -= 1

    sess.flush()
    return True


# ============================================================================
# SERVICE FUNCTIONS: FIXED QUESTION ASSIGNMENTS
# ============================================================================


def assign_question(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentQuestionAssignment:
    """Assign a fixed question to an assessment (AC-03, AC-06)."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    # Structure Freeze Invariant check (AC-06)
    if assessment.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Assessment questions cannot be modified after student attempt has started."
        )

    q_val = payload.get("question_id")
    if not q_val:
        raise AssessmentValidationError("question_id is required.")

    question = _resolve_question(q_val, session=sess)
    if question is None:
        raise QuestionNotFoundError("Question not found.")

    # Cross-course check (AC-03)
    if question.course_id != assessment.course_id:
        raise AssessmentValidationError(
            "Cannot assign question from a different course to this assessment."
        )

    # Duplicate check
    existing = (
        sess.query(AssessmentQuestionAssignment)
        .filter(
            AssessmentQuestionAssignment.assessment_id == assessment.id,
            AssessmentQuestionAssignment.question_id == question.id,
        )
        .first()
    )
    if existing is not None:
        raise AssessmentValidationError("Question is already assigned to this assessment.")

    # Section validation
    section_id: int | None = None
    sec_val = payload.get("section_id")
    if sec_val:
        sec = _resolve_section(assessment, sec_val)
        if sec is None:
            raise AssessmentSectionNotFoundError("Section not found in assessment.")
        section_id = sec.id

    # Points validation
    raw_points = payload.get("points", 1.0)
    try:
        pts = Decimal(str(raw_points))
        if pts <= 0:
            raise AssessmentValidationError("Points must be greater than 0.")
    except Exception as err:
        raise AssessmentValidationError("Invalid points value.") from err

    # Position
    existing_positions = [a.position for a in assessment.question_assignments]
    raw_pos = payload.get("position")
    if raw_pos is not None and raw_pos != "":
        try:
            pos = int(raw_pos)
            if pos <= 0:
                raise AssessmentValidationError("Assignment position must be > 0.")
        except (ValueError, TypeError) as err:
            raise AssessmentValidationError("Assignment position must be an integer.") from err
        if pos in existing_positions:
            for a in assessment.question_assignments:
                if a.position >= pos:
                    a.position += 1
    else:
        pos = max(existing_positions, default=0) + 1

    source_type = str(payload.get("source_type", "BANK")).strip().upper()
    if source_type not in {"MANUAL", "BANK", "IMPORT", "AI"}:
        source_type = "BANK"

    assignment = AssessmentQuestionAssignment(
        assessment_id=assessment.id,
        section_id=section_id,
        question_id=question.id,
        position=pos,
        points=pts,
        is_mandatory=bool(payload.get("is_mandatory", True)),
        shuffle_choices_override=payload.get("shuffle_choices_override"),
        source_type=source_type,
        created_at=utc_now(),
    )
    sess.add(assignment)
    sess.flush()
    return assignment


def remove_question_assignment(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    question_id: Question | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> bool:
    """Remove a fixed question assignment from an assessment (AC-06)."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    # Structure Freeze Invariant check (AC-06)
    if assessment.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Assessment questions cannot be removed after student attempt has started."
        )

    question = _resolve_question(question_id, session=sess)
    if question is None:
        raise QuestionNotFoundError("Question not found.")

    assignment = (
        sess.query(AssessmentQuestionAssignment)
        .filter(
            AssessmentQuestionAssignment.assessment_id == assessment.id,
            AssessmentQuestionAssignment.question_id == question.id,
        )
        .first()
    )
    if assignment is None:
        raise AssessmentValidationError("Question is not assigned to this assessment.")

    deleted_pos = assignment.position
    sess.delete(assignment)
    sess.flush()

    for a in assessment.question_assignments:
        if a.id != assignment.id and a.position > deleted_pos:
            a.position -= 1

    sess.flush()
    return True


# ============================================================================
# SERVICE FUNCTIONS: BLUEPRINT & ALGORITHM 05 MATERIALIZATION
# ============================================================================


def configure_blueprint(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> AssessmentBlueprint:
    """Configure an AssessmentBlueprint and its generation rules."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    # Structure Freeze Invariant check (AC-06)
    if assessment.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Assessment blueprint cannot be modified after student attempt has started."
        )

    name = str(payload.get("name", "Default Blueprint")).strip() or "Default Blueprint"
    if len(name) > 200:
        raise BlueprintValidationError("Blueprint name must not exceed 200 characters.")

    blueprint = (
        sess.query(AssessmentBlueprint)
        .filter(
            AssessmentBlueprint.assessment_id == assessment.id,
            AssessmentBlueprint.name == name,
        )
        .first()
    )
    if blueprint is None:
        blueprint = AssessmentBlueprint(
            assessment_id=assessment.id,
            name=name,
            status="DRAFT",
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        sess.add(blueprint)
        sess.flush()
    else:
        for r in list(blueprint.rules):
            sess.delete(r)
        blueprint.status = "DRAFT"
        blueprint.updated_at = utc_now()
        sess.flush()

    rules_data = payload.get("rules", [])
    if not isinstance(rules_data, list):
        raise BlueprintValidationError("Rules must be provided as a list.")

    for idx, rule_dict in enumerate(rules_data, start=1):
        raw_count = rule_dict.get("question_count")
        try:
            q_count = int(raw_count)
            if q_count <= 0:
                raise BlueprintValidationError("question_count must be > 0.")
        except (ValueError, TypeError) as err:
            raise BlueprintValidationError("question_count must be a positive integer.") from err

        raw_points = rule_dict.get("points_each", 1.0)
        try:
            pts_each = Decimal(str(raw_points))
            if pts_each <= 0:
                raise BlueprintValidationError("points_each must be > 0.")
        except Exception as err:
            raise BlueprintValidationError("points_each must be a positive decimal.") from err

        diff = rule_dict.get("difficulty")
        if diff:
            diff = str(diff).strip().upper()
            if diff not in ALLOWED_DIFFICULTIES:
                raise BlueprintValidationError(
                    f"Invalid difficulty '{diff}'. Allowed: {sorted(ALLOWED_DIFFICULTIES)}"
                )

        q_type = rule_dict.get("question_type")
        if q_type:
            q_type = str(q_type).strip().upper()
            if q_type not in ALLOWED_QUESTION_TYPES:
                raise BlueprintValidationError(
                    f"Invalid question_type '{q_type}'. Allowed: {sorted(ALLOWED_QUESTION_TYPES)}"
                )

        lesson_id: int | None = None
        les_val = rule_dict.get("lesson_id")
        if les_val:
            les_query = sess.query(Lesson)
            if isinstance(les_val, uuid.UUID):
                lesson = les_query.filter(Lesson.public_id == les_val).first()
            elif isinstance(les_val, int):
                lesson = les_query.filter(Lesson.id == les_val).first()
            elif isinstance(les_val, str):
                try:
                    lesson = les_query.filter(Lesson.public_id == uuid.UUID(les_val)).first()
                except ValueError:
                    lesson = (
                        les_query.filter(Lesson.id == int(les_val)).first()
                        if les_val.isdigit()
                        else None
                    )
            else:
                lesson = None

            if lesson is None or lesson.course_id != assessment.course_id:
                raise BlueprintValidationError("Rule lesson must belong to the assessment course.")
            lesson_id = lesson.id

        section_id: int | None = None
        sec_val = rule_dict.get("section_id")
        if sec_val:
            sec = _resolve_section(assessment, sec_val)
            if sec is None:
                raise AssessmentSectionNotFoundError("Section not found in assessment.")
            section_id = sec.id

        rule_pos = rule_dict.get("position", idx)
        rule = AssessmentBlueprintRule(
            blueprint_id=blueprint.id,
            section_id=section_id,
            lesson_id=lesson_id,
            difficulty=diff,
            question_type=q_type,
            question_count=q_count,
            points_each=pts_each,
            position=rule_pos,
        )
        sess.add(rule)

    sess.flush()
    return blueprint


def materialize_blueprint_pool(
    actor: User,
    assessment_id: Assessment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> list[AssessmentQuestionPool]:
    """Execute Algorithm 05 — Blueprint Question Pool Materialization (AC-04)."""
    sess = session if session is not None else db.session

    assessment = _resolve_assessment(assessment_id, session=sess, include_deleted=False)
    if assessment is None:
        raise AssessmentNotFoundError("Assessment not found.")

    require_course_manager(actor, assessment.course_id, session=sess)

    # Structure Freeze Invariant check (AC-06)
    if assessment.first_attempt_started_at is not None:
        raise AssessmentLockedError(
            "Assessment question pool cannot be materialized after student attempt has started."
        )

    blueprint = (
        sess.query(AssessmentBlueprint)
        .filter(AssessmentBlueprint.assessment_id == assessment.id)
        .first()
    )
    if blueprint is None or not blueprint.rules:
        raise BlueprintValidationError(
            "No blueprint rules configured for this assessment to materialize."
        )

    # Exclude questions already in fixed assignments (mandatory overlap protection)
    assigned_qids = {a.question_id for a in assessment.question_assignments}
    selected_qids = set(assigned_qids)

    new_pool_entries: list[tuple[AssessmentBlueprintRule, Question]] = []

    for rule in sorted(blueprint.rules, key=lambda r: r.position):
        cand_query = (
            sess.query(Question)
            .join(QuestionRevision, Question.current_revision_id == QuestionRevision.id)
            .filter(
                Question.course_id == assessment.course_id,
                Question.status == "ACTIVE",
                Question.deleted_at.is_(None),
            )
        )
        if rule.lesson_id is not None:
            cand_query = cand_query.filter(Question.lesson_id == rule.lesson_id)
        if rule.difficulty is not None:
            cand_query = cand_query.filter(Question.difficulty == rule.difficulty)
        if rule.question_type is not None:
            cand_query = cand_query.filter(QuestionRevision.question_type == rule.question_type)

        all_matching = cand_query.order_by(Question.id.asc()).all()
        eligible = [q for q in all_matching if q.id not in selected_qids]

        if len(eligible) < rule.question_count:
            rule_desc = f"{rule.difficulty or 'ANY'}/{rule.question_type or 'ANY'}"
            raise BlueprintValidationError(
                f"Insufficient questions for rule position {rule.position} ({rule_desc}): "
                f"required {rule.question_count}, found {len(eligible)} eligible."
            )

        chosen = eligible[: rule.question_count]
        for q in chosen:
            selected_qids.add(q.id)
            new_pool_entries.append((rule, q))

    # Clear previous non-fixed pool items for this assessment
    sess.query(AssessmentQuestionPool).filter(
        AssessmentQuestionPool.assessment_id == assessment.id
    ).delete(synchronize_session=False)

    created_pool: list[AssessmentQuestionPool] = []
    for idx, (rule, q) in enumerate(new_pool_entries, start=1):
        pool_item = AssessmentQuestionPool(
            assessment_id=assessment.id,
            blueprint_rule_id=rule.id,
            question_id=q.id,
            points=rule.points_each,
            is_fixed=False,
            position_hint=idx,
            selection_source="BLUEPRINT",
            created_at=utc_now(),
        )
        sess.add(pool_item)
        created_pool.append(pool_item)

    blueprint.status = "READY"
    blueprint.updated_at = utc_now()
    sess.flush()

    return created_pool
