"""One student-facing assessment state across lists, course consoles and waiting rooms."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy.orm import selectinload

from pwd301.extensions import db
from pwd301.models.assessment import Assessment
from pwd301.models.attempt_regrade import AssessmentAttempt
from pwd301.models.course import Enrollment, Lesson, LessonProgress
from pwd301.models.types import utc_now
from pwd301.services.assessment_service import _calculate_assessment_aggregates, _normalize_dt


def student_score_released(attempt: AssessmentAttempt, now: Any = None) -> bool:
    """Score publication is independent of permission to review question details."""
    result = attempt.result
    if attempt.status != "GRADED" or result is None or result.status not in {"FINAL", "RELEASED"}:
        return False
    assessment = attempt.assessment
    if assessment is None or assessment.score_release_policy == "IMMEDIATE":
        return True
    if assessment.score_release_policy == "INSTRUCTOR_RELEASE":
        return result.status == "RELEASED"
    close_at = _normalize_dt(assessment.close_at)
    current = _normalize_dt(now) if now is not None else utc_now()
    return bool(close_at and current and current >= close_at)


def final_assessment_prerequisites(
    assessment: Assessment, period_id: int | None, session: Any
) -> tuple[int, int]:
    """Count actual published lessons; question provenance never exempts a lesson."""
    if assessment.assessment_type not in {"FINAL", "FINAL_EXAM"}:
        return 0, 0
    lessons = (
        session.query(Lesson.id)
        .filter(
            Lesson.course_id == assessment.course_id,
            Lesson.status == "PUBLISHED",
            Lesson.deleted_at.is_(None),
        )
        .all()
    )
    lesson_ids = [row[0] for row in lessons]
    if not lesson_ids or period_id is None:
        return 0, len(lesson_ids)
    completed = (
        session.query(LessonProgress.lesson_id)
        .filter(
            LessonProgress.enrollment_period_id == period_id,
            LessonProgress.lesson_id.in_(lesson_ids),
            LessonProgress.completed_at.isnot(None),
        )
        .distinct()
        .count()
    )
    return completed, len(lesson_ids)


def student_assessment_summary(
    actor: Any,
    assessment: Assessment,
    *,
    session: Any = None,
    attempts: list[AssessmentAttempt] | None = None,
    enrollment: Enrollment | None = None,
) -> dict[str, Any]:
    sess = session if session is not None else db.session
    now = utc_now()
    if enrollment is None:
        enrollment = (
            sess.query(Enrollment)
            .filter(
                Enrollment.student_user_id == actor.id,
                Enrollment.course_id == assessment.course_id,
            )
            .first()
        )
    period_id = enrollment.current_period_id if enrollment else None
    if attempts is None:
        attempts = (
            sess.query(AssessmentAttempt)
            .options(
                selectinload(AssessmentAttempt.result),
                selectinload(AssessmentAttempt.attempt_questions),
            )
            .filter(
                AssessmentAttempt.assessment_id == assessment.id,
                AssessmentAttempt.student_user_id == actor.id,
                AssessmentAttempt.status != "CANCELLED",
            )
            .order_by(AssessmentAttempt.attempt_number)
            .all()
        )
    attempts = sorted(
        (a for a in attempts if a.enrollment_period_id == period_id and a.status != "CANCELLED"),
        key=lambda a: (a.attempt_number, a.id),
    )
    open_at, close_at = _normalize_dt(assessment.open_at), _normalize_dt(assessment.close_at)
    is_open, is_closed = not open_at or now >= open_at, bool(close_at and now >= close_at)
    waiting_at = open_at - timedelta(minutes=30) if open_at else None
    effective_status = {
        attempt.id: (
            "EXPIRED"
            if attempt.status == "IN_PROGRESS"
            and (
                is_closed
                or (
                    (deadline := _normalize_dt(attempt.deadline_at)) is not None and deadline <= now
                )
            )
            else attempt.status
        )
        for attempt in attempts
    }
    active = next(
        (a for a in attempts if effective_status[a.id] == "IN_PROGRESS"),
        None,
    )
    relevant_attempt = active or (attempts[-1] if attempts else None)
    assigned = relevant_attempt.attempt_questions if relevant_attempt else []
    if assigned:
        count, max_points = len(assigned), sum(float(item.points_assigned) for item in assigned)
    else:
        count, max_points = _calculate_assessment_aggregates(assessment, session=sess)
    limit = assessment.attempt_limit
    exhausted = bool(limit and len(attempts) >= limit)
    completed_lessons, total_lessons = final_assessment_prerequisites(assessment, period_id, sess)
    locked = completed_lessons < total_lessons
    lock_reason = (
        (
            f"Bạn cần hoàn thành tất cả các bài học trong khóa học ({completed_lessons}/{total_lessons} bài) "
            "trước khi tham gia bài thi cuối kỳ (Final Exam)."
        )
        if locked
        else None
    )
    finalized = [
        a
        for a in attempts
        if a.status == "GRADED" and a.result and a.result.status in {"FINAL", "RELEASED"}
    ]
    best = max(
        finalized, key=lambda a: (float(a.result.raw_score), -a.attempt_number), default=None
    )
    policy = assessment.scoring_policy
    selected = (finalized[0] if policy == "FIRST" else finalized[-1]) if finalized else None
    if policy == "HIGHEST":
        selected = best
    score = {
        "raw_score": None,
        "max_score": None,
        "percent_score": None,
        "score_out_of_10": None,
        "passed": None,
        "scoring_policy": policy,
        "is_released": False,
    }
    constituents = finalized if policy == "AVERAGE" else ([selected] if selected else [])
    if constituents and all(student_score_released(a, now) for a in constituents):
        raw = sum(float(a.result.raw_score) for a in constituents) / len(constituents)
        maximum = sum(float(a.result.max_score) for a in constituents) / len(constituents)
        percent = raw / maximum * 100 if maximum > 0 else 0.0
        score.update(
            raw_score=raw,
            max_score=maximum,
            percent_score=percent,
            score_out_of_10=percent / 10,
            is_released=True,
            passed=(
                percent
                >= float(
                    assessment.passing_percent if assessment.passing_percent is not None else 50
                )
            ),
        )
    if active:
        completion = "IN_PROGRESS"
    elif attempts and effective_status[attempts[-1].id] in {"SUBMITTED", "PENDING_GRADING"}:
        completion = "PENDING_GRADING"
    elif any(status in {"GRADED", "EXPIRED"} for status in effective_status.values()):
        completion = "COMPLETED"
    else:
        completion = "NOT_STARTED"
    block = None
    if active is None:
        if is_closed:
            block = "CLOSED"
        elif exhausted:
            block = "EXHAUSTED"
        elif locked:
            block = "PREREQUISITE"
        elif not is_open:
            block = "UPCOMING"
        elif enrollment is None or enrollment.status != "ACTIVE":
            block = "ENROLLMENT"
    history = []
    for attempt in attempts:
        released = student_score_released(attempt, now)
        result = attempt.result
        history.append(
            {
                "attempt_id": str(attempt.public_id),
                "attempt_number": attempt.attempt_number,
                "status": effective_status[attempt.id],
                "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
                "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
                "raw_score": float(result.raw_score) if released else None,
                "max_score": float(result.max_score) if released else None,
                "passed": bool(result.passed) if released and result.passed is not None else None,
                "is_score_released": released,
            }
        )
    latest = attempts[-1] if attempts else None
    return {
        "questions_count": count,
        "max_points": max_points,
        "scoring_policy": policy,
        "attempts_count": len(attempts),
        "attempt_limit": limit,
        "remaining_attempts": max(0, limit - len(attempts)) if limit else None,
        "is_attempt_limit_reached": exhausted,
        "active_attempt_id": str(active.public_id) if active else None,
        "latest_attempt_id": str(latest.public_id) if latest else None,
        "attempt_id": str(latest.public_id) if latest else None,
        "attempt_status": effective_status[latest.id] if latest else None,
        "best_attempt_id": str(best.public_id)
        if best and student_score_released(best, now)
        else None,
        "selected_attempt_id": str(selected.public_id)
        if selected and policy != "AVERAGE"
        else None,
        "display_score": score,
        "raw_score": score["raw_score"],
        "is_passed": score["passed"],
        "passed": score["passed"],
        "is_completed": completion == "COMPLETED",
        "completion_status": completion,
        "attempts": history,
        "can_start": active is None and block is None,
        "can_resume": active is not None,
        "is_locked": locked,
        "lock_reason": lock_reason,
        "start_block_reason": block,
        "is_open": is_open,
        "is_closed": is_closed,
        "is_waiting_room_open": not waiting_at or now >= waiting_at,
        "waiting_room_opens_at": waiting_at.isoformat() if waiting_at else None,
        "seconds_until_open": max(0, int((open_at - now).total_seconds())) if open_at else 0,
        "seconds_until_waiting_room_open": max(0, int((waiting_at - now).total_seconds()))
        if waiting_at
        else 0,
        "server_now_iso": now.isoformat(),
    }
