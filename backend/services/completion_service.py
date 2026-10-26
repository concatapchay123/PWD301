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

import contextlib
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.orm import Session, scoped_session

from backend.extensions import db
from backend.models.assessment import Assessment
from backend.models.attempt_regrade import AssessmentAttempt, AssessmentResult
from backend.models.course import (
    CourseCompletionRule,
    CourseCompletionSummary,
    Enrollment,
    EnrollmentEvent,
    EnrollmentPeriod,
    Lesson,
    LessonProgress,
)
from backend.models.identity import User
from backend.models.notification_audit import AuditEvent
from backend.models.types import utc_now
from backend.services.authorization_service import (
    _resolve_course,
    _resolve_user,
    require_course_manager,
)
from backend.services.exceptions import (
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

    from backend.services.course_workflow_service import ensure_course_authoring, should_stage

    course = ensure_course_authoring(actor, course, session=sess)

    if course.deleted_at is not None or course.status in ("TRASH", "ARCHIVED"):
        raise CompletionRuleValidationError(
            f"Cannot configure completion rules for course in '{course.status}' status."
        )

    if course.status == "SUBMITTED_FOR_REVIEW" and not actor.is_admin:
        raise CompletionRuleValidationError(
            "Khóa học đang chờ Quản trị viên xét duyệt. Không thể sửa đổi quy tắc hoàn thành."
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

    if should_stage(actor, course, sess):
        from backend.services.course_workflow_service import AuthoringProjection, stage_course_fields

        allowed = {
            "require_all_required_lessons",
            "require_required_assessments",
            "minimum_progress_percent",
            "minimum_grade_score",
            "allow_certificate",
            "completion_grace_days",
        }
        proposed = {key: value for key, value in payload.items() if key in allowed}
        for key in (
            "require_all_required_lessons",
            "require_required_assessments",
            "allow_certificate",
        ):
            if key in proposed and not isinstance(proposed[key], bool):
                raise CompletionRuleValidationError(f"{key} must be a boolean.")
        if "minimum_grade_score" in proposed:
            try:
                score_val = float(proposed["minimum_grade_score"])
                if score_val > 10 and score_val <= 100:
                    score_val = score_val / 10.0
                proposed["minimum_grade_score"] = score_val
            except (ValueError, TypeError):
                raise CompletionRuleValidationError(
                    "minimum_grade_score must be numeric."
                ) from None
            if not 0 <= proposed["minimum_grade_score"] <= 10:
                raise CompletionRuleValidationError("minimum_grade_score must be between 0 and 10.")
        stage_course_fields(actor, course, "completion_rules", proposed, session=sess)
        if session is None:
            sess.commit()
        return cast(CourseCompletionRule, AuthoringProjection(rule, proposed))

    # Parse existing course completion requirements JSON
    req_dict: dict[str, Any] = {}
    if course.completion_requirements:
        try:
            parsed_req = json.loads(course.completion_requirements)
            if isinstance(parsed_req, dict):
                req_dict = parsed_req
        except Exception:
            req_dict = {}

    before_json = json.dumps(
        {
            "require_all_required_lessons": rule.require_all_required_lessons,
            "require_required_assessments": rule.require_required_assessments,
            "minimum_progress_percent": (
                float(rule.minimum_progress_percent)
                if rule.minimum_progress_percent is not None
                else None
            ),
            "minimum_grade_score": req_dict.get("minimum_grade_score"),
            "allow_certificate": req_dict.get("allow_certificate"),
        }
    )

    if "require_all_required_lessons" in payload:
        rule.require_all_required_lessons = bool(payload["require_all_required_lessons"])

    if "require_required_assessments" in payload:
        rule.require_required_assessments = bool(payload["require_required_assessments"])

    if "minimum_progress_percent" in payload:
        rule.minimum_progress_percent = min_pct

    if "minimum_grade_score" in payload:
        with contextlib.suppress(ValueError, TypeError):
            req_dict["minimum_grade_score"] = float(payload["minimum_grade_score"])

    if "allow_certificate" in payload:
        req_dict["allow_certificate"] = bool(payload["allow_certificate"])

    if "completion_grace_days" in payload:
        with contextlib.suppress(ValueError, TypeError):
            req_dict["completion_grace_days"] = int(payload["completion_grace_days"])

    course.completion_requirements = json.dumps(req_dict, ensure_ascii=False)

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
            "minimum_grade_score": req_dict.get("minimum_grade_score"),
            "allow_certificate": req_dict.get("allow_certificate"),
        }
    )

    actor_roles = ",".join(sorted(actor.role_codes)) if actor.role_codes else "UNKNOWN"
    reason = (
        str(payload.get("reason"))
        if payload.get("reason")
        else "Cập nhật điều kiện hoàn thành khóa học"
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

    if session is None:
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
        if current_period is not None and current_period.status not in ("ACTIVE", "COMPLETED"):
            current_period = None

    if current_period is None:
        current_period = (
            sess.query(EnrollmentPeriod)
            .filter(
                EnrollmentPeriod.enrollment_id == enrollment.id,
                EnrollmentPeriod.status.in_(["ACTIVE", "COMPLETED"]),
            )
            .order_by(EnrollmentPeriod.period_no.desc())
            .first()
        )

    if current_period is None:
        now_ts = utc_now()
        current_period = EnrollmentPeriod(
            enrollment_id=enrollment.id,
            period_no=1,
            started_at=enrollment.enrolled_at or now_ts,
            status="ACTIVE" if enrollment.status == "ACTIVE" else "COMPLETED",
            created_at=now_ts,
        )
        sess.add(current_period)
        sess.flush()
        enrollment.current_period_id = current_period.id
        sess.flush()
    elif enrollment.current_period_id != current_period.id:
        enrollment.current_period_id = current_period.id
        sess.flush()

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

    required_lessons = sess.query(Lesson.id, Lesson.position).filter(*required_lesson_filter).all()
    total_required_lessons = len(required_lessons)

    if total_required_lessons == 0:
        if total_published_lessons > 0:
            required_lessons = (
                sess.query(Lesson.id, Lesson.position)
                .filter(
                    Lesson.course_id == enrollment.course_id,
                    Lesson.status == "PUBLISHED",
                    Lesson.deleted_at.is_(None),
                )
                .all()
            )
            total_required_lessons = len(required_lessons)
        if total_required_lessons == 0:
            enrollment.current_progress_percent = Decimal("0.00")
            enrollment.updated_at = utc_now()
            sess.flush()
            return 0.0

    completed_lp_records = (
        sess.query(Lesson.id, Lesson.position)
        .join(LessonProgress, Lesson.id == LessonProgress.lesson_id)
        .filter(
            LessonProgress.enrollment_period_id == current_period.id,
            LessonProgress.completed_at.isnot(None),
            Lesson.course_id == enrollment.course_id,
            Lesson.deleted_at.is_(None),
            Lesson.status.in_(["PUBLISHED", "HISTORICAL", "ACTIVE"]),
        )
        .all()
    )

    completed_ids = {r[0] for r in completed_lp_records}
    completed_positions = {r[1] for r in completed_lp_records}

    satisfied_count = sum(
        1
        for (les_id, les_pos) in required_lessons
        if les_id in completed_ids or les_pos in completed_positions
    )

    raw_pct = (satisfied_count / total_required_lessons) * 100.0
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

    # Recalculate progress baseline and auto-heal active EnrollmentPeriod if missing
    current_pct = calculate_course_progress(enrollment, session=sess)

    current_period = enrollment.current_period
    if current_period is None and enrollment.current_period_id:
        current_period = sess.get(EnrollmentPeriod, enrollment.current_period_id)

    if current_period is None:
        current_period = (
            sess.query(EnrollmentPeriod)
            .filter(
                EnrollmentPeriod.enrollment_id == enrollment.id,
                EnrollmentPeriod.status.in_(["ACTIVE", "COMPLETED"]),
            )
            .order_by(EnrollmentPeriod.period_no.desc())
            .first()
        )
        if current_period is not None:
            enrollment.current_period_id = current_period.id

    if current_period is None or current_period.status not in ("ACTIVE", "COMPLETED"):
        existing_summary = (
            sess.query(CourseCompletionSummary)
            .filter(
                CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                CourseCompletionSummary.course_id == enrollment.course_id,
            )
            .first()
        )
        return False, existing_summary

    # Load completion rule
    rule = get_or_create_default_completion_rule(enrollment.course_id, session=sess)

    # Criterion 1: Minimum progress percentage
    if rule.minimum_progress_percent is not None and current_pct < float(
        rule.minimum_progress_percent
    ):
        if enrollment.status == "COMPLETED":
            enrollment.status = "ACTIVE"
            enrollment.completed_at = None
            enrollment.updated_at = utc_now()
            if current_period and current_period.status == "COMPLETED":
                current_period.status = "ACTIVE"
                current_period.completed_at = None
                current_period.updated_at = utc_now()
            sess.flush()
        existing_summary = (
            sess.query(CourseCompletionSummary)
            .filter(
                CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                CourseCompletionSummary.course_id == enrollment.course_id,
            )
            .first()
        )
        return False, existing_summary

    # Criterion 2: Required lessons (All published lessons in the course must be completed)
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
            if enrollment.status == "COMPLETED":
                enrollment.status = "ACTIVE"
                enrollment.completed_at = None
                enrollment.updated_at = utc_now()
                if current_period and current_period.status == "COMPLETED":
                    current_period.status = "ACTIVE"
                    current_period.completed_at = None
                    current_period.updated_at = utc_now()
                sess.flush()
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
                if enrollment.status == "COMPLETED":
                    enrollment.status = "ACTIVE"
                    enrollment.completed_at = None
                    enrollment.updated_at = utc_now()
                    if current_period and current_period.status == "COMPLETED":
                        current_period.status = "ACTIVE"
                        current_period.completed_at = None
                        current_period.updated_at = utc_now()
                    sess.flush()
                existing_summary = (
                    sess.query(CourseCompletionSummary)
                    .filter(
                        CourseCompletionSummary.student_user_id == enrollment.student_user_id,
                        CourseCompletionSummary.course_id == enrollment.course_id,
                    )
                    .first()
                )
                return False, existing_summary

    # Criterion 3: All published assessments in the course must be completed and passed
    published_assessments = (
        sess.query(Assessment)
        .filter(
            Assessment.course_id == enrollment.course_id,
            Assessment.status == "PUBLISHED",
            Assessment.deleted_at.is_(None),
        )
        .all()
    )
    if published_assessments:
        pub_ass_ids = [ass.id for ass in published_assessments]
        passed_assessment_ids = {
            r[0]
            for r in (
                sess.query(AssessmentAttempt.assessment_id)
                .join(AssessmentResult, AssessmentResult.attempt_id == AssessmentAttempt.id)
                .filter(
                    AssessmentAttempt.assessment_id.in_(pub_ass_ids),
                    AssessmentAttempt.student_user_id == enrollment.student_user_id,
                    AssessmentAttempt.status == "GRADED",
                    AssessmentResult.passed == True,
                )
                .all()
            )
        }
        if len(passed_assessment_ids) < len(pub_ass_ids):
            # Not all published assessments in the course have been passed!
            if enrollment.status == "COMPLETED":
                enrollment.status = "ACTIVE"
                enrollment.completed_at = None
                enrollment.updated_at = utc_now()
                if current_period and current_period.status == "COMPLETED":
                    current_period.status = "ACTIVE"
                    current_period.completed_at = None
                    current_period.updated_at = utc_now()
                sess.flush()
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
    was_already_completed = (enrollment.status == "COMPLETED")
    now = utc_now()
    enrollment.status = "COMPLETED"
    enrollment.completed_at = now
    enrollment.updated_at = now

    current_period.status = "COMPLETED"
    current_period.completed_at = now
    current_period.updated_at = now

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

    if not was_already_completed:
        # Append-only EnrollmentEvent
        enrollment_event = EnrollmentEvent(
            enrollment_id=enrollment.id,
            period_id=current_period.id,
            event_type="COMPLETED",
            actor_user_id=enrollment.student_user_id,
            reason="Đã thỏa mãn đầy đủ điều kiện hoàn thành khóa học",
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
            reason="Đã thỏa mãn đầy đủ điều kiện hoàn thành khóa học",
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
