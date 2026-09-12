"""Course progress engine, completion rules, and durable completion summaries for PWD301.

Provides business logic for:
- Course progress aggregation adhering to Algorithm 01 (01_COURSE_PROGRESS_ALGORITHM.md).
- Managing CourseCompletionRule (retrieval and updates with AuditEvent logging).
- Evaluating course completion with monotonic, idempotent state transitions.
- Upserting durable CourseCompletionSummary records for permanent prerequisite eligibility.
- Append-only EnrollmentEvent and AuditEvent logging.
- Resource-level authorization and IDOR prevention for students, instructors, and admins.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt, AssessmentResult
from pwd301.models.course import (
    CourseCompletionRule,
    CourseCompletionSummary,
    Enrollment,
    EnrollmentEvent,
    EnrollmentPeriod,
    Lesson,
    LessonProgress,
)
from pwd301.models.identity import User
from pwd301.models.notification_audit import AuditEvent
from pwd301.models.types import utc_now
from pwd301.services.authorization_service import (
    _resolve_course,
    _resolve_user,
    require_course_manager,
)
from pwd301.services.exceptions import (
    CompletionRuleValidationError,
    CourseNotFoundError,
    EnrollmentNotFoundError,
    ForbiddenError,
    ResourceNotFoundError,
)


def _normalize_dt(val: Any) -> datetime | None:
    """Ensure a datetime is timezone-aware UTC datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=UTC)
        return val.astimezone(UTC)
    return None


def _resolve_enrollment(
    enrollment_or_id: Enrollment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> Enrollment | None:
    """Resolve an Enrollment instance from model, ID, UUID, or string."""
    if isinstance(enrollment_or_id, Enrollment):
        return enrollment_or_id

    sess = session if session is not None else db.session
    if isinstance(enrollment_or_id, int):
        return sess.get(Enrollment, enrollment_or_id)

    if isinstance(enrollment_or_id, uuid.UUID):
        return sess.query(Enrollment).filter(Enrollment.public_id == enrollment_or_id).first()

    if isinstance(enrollment_or_id, str):
        try:
            val_uuid = uuid.UUID(enrollment_or_id)
            return sess.query(Enrollment).filter(Enrollment.public_id == val_uuid).first()
        except ValueError:
            pass
        if enrollment_or_id.isdigit():
            return sess.get(Enrollment, int(enrollment_or_id))

    return None


def get_or_create_default_completion_rule(
    course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> CourseCompletionRule:
    """Retrieve or create the default CourseCompletionRule for a course.

    Defaults:
    - require_all_required_lessons: True
    - require_required_assessments: True
    - minimum_progress_percent: 100.00

    Args:
        course_id: Internal ID or public UUID of the course.
        session: Optional SQLAlchemy session.

    Returns:
        CourseCompletionRule model instance.

    Raises:
        CourseNotFoundError: If course does not exist.
    """
    sess = session if session is not None else db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise CourseNotFoundError("Course not found.")

    rule = sess.get(CourseCompletionRule, course.id)
    if rule is None:
        rule = CourseCompletionRule(
            course_id=course.id,
            require_all_required_lessons=True,
            require_required_assessments=True,
            minimum_progress_percent=Decimal("100.00"),
            updated_at=utc_now(),
        )
        sess.add(rule)
        sess.flush()

    return rule


def set_course_completion_rule(
    actor: User,
    course_id: int | uuid.UUID | str,
    payload: dict[str, Any],
    session: Session | scoped_session[Any] | None = None,
) -> CourseCompletionRule:
    """Set or update completion rule criteria for a course.

    Invariants enforced:
    - Only managing instructor or administrator can modify completion rules.
    - Course must not be soft-deleted or trashed.
    - minimum_progress_percent must be bounded between 0.00 and 100.00.
    - AuditEvent is recorded append-only on every modification.

    Args:
        actor: Authenticated user.
        course_id: Identifier of the course.
        payload: Dictionary containing configuration fields:
                 require_all_required_lessons (bool),
                 require_required_assessments (bool),
                 minimum_progress_percent (float | Decimal | None),
                 reason (optional str).
        session: Optional SQLAlchemy session.

    Returns:
        The updated CourseCompletionRule.

    Raises:
        ForbiddenError: If actor lacks management permissions.
        CourseNotFoundError: If course does not exist.
        CompletionRuleValidationError: If payload violates domain rules.
    """
    sess = session if session is not None else db.session
    course = require_course_manager(actor, course_id, session=sess)

    if course.deleted_at is not None or course.status in ("TRASH", "ARCHIVED"):
        raise CompletionRuleValidationError(
            f"Cannot configure completion rules for course in '{course.status}' status."
        )

    # Validate minimum_progress_percent
    min_pct: Decimal | None = None
    if "minimum_progress_percent" in payload:
        raw_val = payload["minimum_progress_percent"]
        if raw_val is not None:
            try:
                flt_val = float(raw_val)
            except (ValueError, TypeError):
                raise CompletionRuleValidationError(
                    "minimum_progress_percent must be a valid numeric value."
                ) from None

            if not (0.0 <= flt_val <= 100.0):
                raise CompletionRuleValidationError(
                    "minimum_progress_percent must be between 0.00 and 100.00."
                )
            min_pct = Decimal(str(round(flt_val, 2)))

    rule = get_or_create_default_completion_rule(course.id, session=sess)

    before_json = json.dumps(
        {
            "require_all_required_lessons": rule.require_all_required_lessons,
            "require_required_assessments": rule.require_required_assessments,
            "minimum_progress_percent": (
                float(rule.minimum_progress_percent)
                if rule.minimum_progress_percent is not None
                else None
            ),
        }
    )

    if "require_all_required_lessons" in payload:
        rule.require_all_required_lessons = bool(payload["require_all_required_lessons"])

    if "require_required_assessments" in payload:
        rule.require_required_assessments = bool(payload["require_required_assessments"])

    if "minimum_progress_percent" in payload:
        rule.minimum_progress_percent = min_pct

    now = utc_now()
    rule.updated_by_user_id = actor.id
    rule.updated_at = now

    after_json = json.dumps(
        {
            "require_all_required_lessons": rule.require_all_required_lessons,
            "require_required_assessments": rule.require_required_assessments,
            "minimum_progress_percent": (
                float(rule.minimum_progress_percent)
                if rule.minimum_progress_percent is not None
                else None
            ),
        }
    )

    actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "UNKNOWN"
    reason = (
        str(payload.get("reason"))
        if payload.get("reason")
        else "Updated course completion criteria"
    )
    audit_entry = AuditEvent(
        actor_user_id=actor.id,
        actor_roles_snapshot=actor_roles,
        action="COMPLETION_RULE_UPDATED",
        target_type="COURSE_COMPLETION_RULE",
        target_id=course.id,
        reason=reason,
        before_json=before_json,
        after_json=after_json,
        performed_as_admin=actor.is_admin,
        created_at=now,
    )
    sess.add(audit_entry)
    sess.flush()

    try:
        sess.commit()
    except Exception:
        sess.rollback()
        raise

    return rule


def calculate_course_progress(
    enrollment_id: Enrollment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> float:
    """Calculate and cache overall course progress percentage (Algorithm 01).

    Aggregates completed lessons in the student's current EnrollmentPeriod:
    Progress = (completed_lessons / total_published_lessons) * 100.0

    Invariants:
    - Only counts lessons in the current EnrollmentPeriod.
    - If total published lessons is 0, progress is 0.00%.
    - Result is bounded to [0.00, 100.00] and rounded to 2 decimal places.
    - Updates enrollment.current_progress_percent cache and enrollment.updated_at.

    Args:
        enrollment_id: Identifier or instance of the Enrollment.
        session: Optional SQLAlchemy session.

    Returns:
        float representing the updated progress percentage.

    Raises:
        EnrollmentNotFoundError: If enrollment cannot be found.
    """
    sess = session if session is not None else db.session
    enrollment = _resolve_enrollment(enrollment_id, session=sess)
    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment not found.")

    current_period = enrollment.current_period
    if current_period is None and enrollment.current_period_id:
        current_period = sess.get(EnrollmentPeriod, enrollment.current_period_id)

    if current_period is None:
        enrollment.current_progress_percent = Decimal("0.00")
        sess.flush()
        return 0.0

    total_published_lessons = (
        sess.query(sa.func.count(Lesson.id))
        .filter(
            Lesson.course_id == enrollment.course_id,
            Lesson.status == "PUBLISHED",
            Lesson.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )

    if total_published_lessons == 0:
        enrollment.current_progress_percent = Decimal("0.00")
        enrollment.updated_at = utc_now()
        sess.flush()
        return 0.0

    period_start = current_period.started_at
    required_lesson_filter = [
        Lesson.course_id == enrollment.course_id,
        Lesson.status == "PUBLISHED",
        Lesson.deleted_at.is_(None),
    ]
    if period_start is not None:
        required_lesson_filter.append(
            sa.or_(
                Lesson.required_for_periods_starting_at.is_(None),
                Lesson.required_for_periods_starting_at <= period_start,
            )
        )

    total_required_lessons = (
        sess.query(sa.func.count(Lesson.id)).filter(*required_lesson_filter).scalar() or 0
    )

    if total_required_lessons == 0:
        enrollment.current_progress_percent = Decimal("100.00")
        enrollment.updated_at = utc_now()
        sess.flush()
        return 100.0

    completed_lessons = (
        sess.query(sa.func.count(LessonProgress.id))
        .join(Lesson, Lesson.id == LessonProgress.lesson_id)
        .filter(
            LessonProgress.enrollment_period_id == current_period.id,
            LessonProgress.completed_at.isnot(None),
            *required_lesson_filter,
        )
        .scalar()
        or 0
    )

    raw_pct = (completed_lessons / total_required_lessons) * 100.0
    pct = min(100.0, max(0.0, round(raw_pct, 2)))

    enrollment.current_progress_percent = Decimal(str(pct))
    enrollment.updated_at = utc_now()
    sess.flush()

    return float(pct)


def evaluate_course_completion(
    enrollment_id: Enrollment | int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[bool, CourseCompletionSummary | None]:
    """Evaluate whether an enrolled student has satisfied the course completion criteria.

    Criteria evaluated:
    1. minimum_progress_percent threshold (if configured).
    2. All required published lessons completed (if require_all_required_lessons).
    3. Required assessments completed/passed (require_required_assessments).

    When satisfied:
    - Enrollment.status -> 'COMPLETED', completed_at set to UTC now.
    - EnrollmentPeriod.status -> 'COMPLETED', completed_at set to UTC now.
    - Upsert CourseCompletionSummary with ever_completed=True, prerequisite_eligible=True.
    - Appends EnrollmentEvent('COMPLETED') and AuditEvent('COURSE_COMPLETED').

    Idempotency:
    - If already COMPLETED, returns (True, summary) immediately without duplicate events.

    Args:
        enrollment_id: Identifier or instance of the Enrollment.
        session: Optional SQLAlchemy session.

    Returns:
        tuple of (bool is_completed, CourseCompletionSummary | None).

    Raises:
        EnrollmentNotFoundError: If enrollment cannot be found.
    """
    sess = session if session is not None else db.session
    enrollment = _resolve_enrollment(enrollment_id, session=sess)
    if enrollment is None:
        raise EnrollmentNotFoundError("Enrollment not found.")

    # Idempotent guard: if already marked COMPLETED, return current summary
    if enrollment.status == "COMPLETED":
        summary = (
            sess.query(CourseCompletionSummary)
            .filter(
                CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                CourseCompletionSummary.course_id == enrollment.course_id,
            )
            .first()
        )
        return True, summary

    current_period = enrollment.current_period
    if current_period is None and enrollment.current_period_id:
        current_period = sess.get(EnrollmentPeriod, enrollment.current_period_id)

    if current_period is None or current_period.status != "ACTIVE":
        existing_summary = (
            sess.query(CourseCompletionSummary)
            .filter(
                CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                CourseCompletionSummary.course_id == enrollment.course_id,
            )
            .first()
        )
        return False, existing_summary

    # Recalculate progress baseline
    current_pct = calculate_course_progress(enrollment, session=sess)

    # Load completion rule
    rule = get_or_create_default_completion_rule(enrollment.course_id, session=sess)

    # Criterion 1: Minimum progress percentage
    if rule.minimum_progress_percent is not None and current_pct < float(
        rule.minimum_progress_percent
    ):
        existing_summary = (
            sess.query(CourseCompletionSummary)
            .filter(
                CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                CourseCompletionSummary.course_id == enrollment.course_id,
            )
            .first()
        )
        return False, existing_summary

    # Criterion 2: Required lessons
    if rule.require_all_required_lessons:
        published_lessons = (
            sess.query(Lesson)
            .filter(
                Lesson.course_id == enrollment.course_id,
                Lesson.status == "PUBLISHED",
                Lesson.deleted_at.is_(None),
            )
            .all()
        )

        if not published_lessons:
            # Cannot complete lesson requirement if course has no published lessons
            existing_summary = (
                sess.query(CourseCompletionSummary)
                .filter(
                    CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                    CourseCompletionSummary.course_id == enrollment.course_id,
                )
                .first()
            )
            return False, existing_summary

        # A lesson is required for this period if required_for_periods_starting_at is None
        # or the period started on/after that threshold (Algorithm 01 & 04_LESSON_AND_PROGRESS.md)
        p_start = _normalize_dt(current_period.started_at)

        def _is_lesson_required(les: Lesson) -> bool:
            if les.required_for_periods_starting_at is None:
                return True
            les_req = _normalize_dt(les.required_for_periods_starting_at)
            return p_start is not None and les_req is not None and p_start >= les_req

        required_lessons = [les for les in published_lessons if _is_lesson_required(les)]

        if required_lessons:
            required_ids = [les.id for les in required_lessons]
            completed_count = (
                sess.query(sa.func.count(LessonProgress.id))
                .filter(
                    LessonProgress.enrollment_period_id == current_period.id,
                    LessonProgress.lesson_id.in_(required_ids),
                    LessonProgress.completed_at.isnot(None),
                )
                .scalar()
                or 0
            )
            if completed_count < len(required_lessons):
                existing_summary = (
                    sess.query(CourseCompletionSummary)
                    .filter(
                        CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                        CourseCompletionSummary.course_id == enrollment.course_id,
                    )
                    .first()
                )
                return False, existing_summary

    # Criterion 3: Required assessments
    if rule.require_required_assessments:
        required_assessments = (
            sess.query(Assessment)
            .filter(
                Assessment.course_id == enrollment.course_id,
                Assessment.is_required_for_completion == True,
                Assessment.status == "PUBLISHED",
                Assessment.deleted_at.is_(None),
            )
            .all()
        )
        for req_ass in required_assessments:
            passed_attempt = (
                sess.query(AssessmentAttempt)
                .join(AssessmentResult, AssessmentResult.attempt_id == AssessmentAttempt.id)
                .filter(
                    AssessmentAttempt.assessment_id == req_ass.id,
                    AssessmentAttempt.student_user_id == enrollment.student_user_id,
                    AssessmentAttempt.status == "GRADED",
                    AssessmentResult.passed == True,
                )
                .first()
            )
            if passed_attempt is None:
                existing_summary = (
                    sess.query(CourseCompletionSummary)
                    .filter(
                        CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                        CourseCompletionSummary.course_id == enrollment.course_id,
                    )
                    .first()
                )
                return False, existing_summary

    # === All criteria satisfied -> Mark Completed ===
    now = utc_now()
    enrollment.status = "COMPLETED"
    enrollment.completed_at = now
    enrollment.updated_at = now

    current_period.status = "COMPLETED"
    current_period.completed_at = now

    # Upsert durable CourseCompletionSummary
    summary = (
        sess.query(CourseCompletionSummary)
        .filter(
            CourseCompletionSummary.student_user_id == enrollment.student_user_id,
            CourseCompletionSummary.course_id == enrollment.course_id,
        )
        .first()
    )

    if summary is None:
        summary = CourseCompletionSummary(
            student_user_id=enrollment.student_user_id,
            course_id=enrollment.course_id,
            ever_completed=True,
            first_completed_at=now,
            latest_completed_at=now,
            prerequisite_eligible=True,
            source_period_id=current_period.id,
            updated_at=now,
        )
        sess.add(summary)
    else:
        summary.ever_completed = True
        summary.prerequisite_eligible = True
        summary.latest_completed_at = now
        if summary.first_completed_at is None:
            summary.first_completed_at = now
        summary.source_period_id = current_period.id
        summary.updated_at = now

    # Append-only EnrollmentEvent
    enrollment_event = EnrollmentEvent(
        enrollment_id=enrollment.id,
        period_id=current_period.id,
        event_type="COMPLETED",
        actor_user_id=enrollment.student_user_id,
        reason="Course completion criteria satisfied",
        created_at=now,
    )
    sess.add(enrollment_event)

    # Append-only AuditEvent
    audit_event = AuditEvent(
        actor_user_id=enrollment.student_user_id,
        actor_roles_snapshot="STUDENT",
        action="COURSE_COMPLETED",
        target_type="COURSE",
        target_id=enrollment.course_id,
        reason="Course completion criteria satisfied",
        performed_as_admin=False,
        created_at=now,
    )
    sess.add(audit_event)

    sess.flush()
    if session is None:
        try:
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    return True, summary


def get_course_completion_summary(
    actor: User,
    course_id: int | uuid.UUID | str,
    student_user_id: int | uuid.UUID | str | None = None,
    session: Session | scoped_session[Any] | None = None,
) -> CourseCompletionSummary | None:
    """Retrieve durable CourseCompletionSummary for a student with IDOR guards.

    Rules:
    - Student can only access their own completion summary (actor.id == student_user_id).
    - Managing instructor can view summaries of students in courses they own.
    - Administrator can access summaries platform-wide.

    Args:
        actor: Authenticated user making the request.
        course_id: Identifier of the course.
        student_user_id: Target student identifier. Defaults to actor.id.
        session: Optional SQLAlchemy session.

    Returns:
        CourseCompletionSummary model instance or None.

    Raises:
        ResourceNotFoundError: If course or student not found.
        ForbiddenError: If actor lacks permission to view target summary.
    """
    sess = session if session is not None else db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    if student_user_id is None:
        target_student = actor
    else:
        resolved = _resolve_user(student_user_id, session=sess)
        if resolved is None:
            raise ResourceNotFoundError("Student not found.")
        target_student = resolved

    # IDOR and Authorization check
    is_self = actor.id == target_student.id
    is_admin = actor.is_admin
    is_owner = actor.has_role("INSTRUCTOR") and course.owner_instructor_id == actor.id

    if not (is_self or is_admin or is_owner):
        raise ForbiddenError("You do not have permission to view this completion summary.")

    return (
        sess.query(CourseCompletionSummary)
        .filter(
            CourseCompletionSummary.student_user_id == target_student.id,
            CourseCompletionSummary.course_id == course.id,
        )
        .first()
    )


def recalculate_course_completion(
    student_user_id: int | uuid.UUID | str,
    course_id: int | uuid.UUID | str,
    session: Session | scoped_session[Any] | None = None,
) -> tuple[bool, CourseCompletionSummary | None]:
    """Recalculate course completion status for a student in a course.

    Resolves student, course, and enrollment, and triggers evaluate_course_completion.

    Args:
        student_user_id: Internal ID, UUID, or string of the student.
        course_id: Internal ID, UUID, or string of the course.
        session: Optional SQLAlchemy session.

    Returns:
        tuple of (bool is_completed, CourseCompletionSummary | None).
    """
    sess = session if session is not None else db.session
    student = _resolve_user(student_user_id, session=sess)
    course = _resolve_course(course_id, session=sess)
    if student is None or course is None:
        return False, None

    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == student.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )
    if enrollment is None:
        return False, None

    return evaluate_course_completion(enrollment, session=sess)
