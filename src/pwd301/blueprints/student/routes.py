"""Route handlers for the student role blueprint."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, render_template, request

from pwd301.blueprints.student import student_bp
from pwd301.extensions import db
from pwd301.models.course import Enrollment, Lesson, LessonProgress
from pwd301.services.analytics_service import get_student_learning_overview
from pwd301.services.authorization_service import (
    _resolve_course,
    require_authenticated_actor,
    student_required,
)
from pwd301.services.completion_service import get_course_completion_summary
from pwd301.services.enrollment_service import (
    enroll_student,
    get_student_enrollments,
    leave_course,
    re_enroll_student,
)
from pwd301.services.exceptions import LessonValidationError, ResourceNotFoundError
from pwd301.services.lesson_service import (
    get_lesson_detail,
    get_lesson_progress,
    record_lesson_progress,
)


@student_bp.route("/dashboard", methods=["GET"])
@student_required
def dashboard() -> Any:
    """Student dashboard displaying learning overview and enrolled courses."""
    actor = require_authenticated_actor()
    overview = get_student_learning_overview(actor, session=db.session)
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("student/dashboard.html", overview=overview)
    return jsonify(overview), 200


@student_bp.route("/attempt/<attempt_id>", methods=["GET"])
@student_required
def attempt_view(attempt_id: str) -> Any:
    """Render the student exam taking view with server timer and question palette."""
    actor = require_authenticated_actor()
    from pwd301.services.attempt_service import get_attempt_delivery

    delivery = get_attempt_delivery(
        student_actor=actor,
        attempt_id=attempt_id,
        session=db.session,
    )
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template("student/attempt.html", delivery=delivery)
    return jsonify(delivery)


@student_bp.route("/courses/<course_id>/progress", methods=["GET"])
@student_required
def course_progress(course_id: str) -> tuple[Response, int] | Response:
    """Get the authenticated student's progress in a specific course."""
    actor = require_authenticated_actor()

    sess = db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    # Scoped strictly to current actor (IDOR prevention)
    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )
    if enrollment is None:
        raise ResourceNotFoundError("Enrollment record not found for this student.")

    data = {
        "course_id": str(course.public_id),
        "course_title": course.title,
        "student_id": str(actor.public_id),
        "progress_percent": float(enrollment.current_progress_percent),
        "status": enrollment.status,
        "enrolled_at": enrollment.enrolled_at.isoformat(),
    }
    return jsonify(data), 200


def _serialize_student_lesson(les: Lesson, p: LessonProgress | None) -> dict[str, Any]:
    return {
        "lesson_id": str(les.public_id),
        "course_id": str(les.course.public_id) if les.course else None,
        "title": les.title,
        "summary": les.summary,
        "markdown_content": les.markdown_content,
        "position": les.position,
        "estimated_duration_minutes": les.estimated_duration_minutes,
        "minimum_completion_seconds": les.minimum_completion_seconds,
        "viewed_fraction_required": float(les.viewed_fraction_required),
        "progress": {
            "seconds_spent": p.seconds_spent if p else 0,
            "max_view_fraction": float(p.max_view_fraction) if p else 0.0,
            "is_completed": p.completed_at is not None if p else False,
            "completed_at": p.completed_at.isoformat() if p and p.completed_at else None,
        },
    }


@student_bp.route("/courses/<course_id>/lessons/<lesson_id>", methods=["GET"])
@student_required
def get_student_lesson_route(course_id: str, lesson_id: str) -> tuple[Response, int] | Response:
    """Access lesson content for learning, protected by active enrollment check."""
    actor = require_authenticated_actor()

    sess = db.session
    course = _resolve_course(course_id, session=sess)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    lesson = get_lesson_detail(actor, lesson_id)
    if lesson.course_id != course.id:
        raise ResourceNotFoundError("Lesson does not belong to this course.")

    progress = get_lesson_progress(actor, lesson_id)
    return jsonify(_serialize_student_lesson(lesson, progress)), 200


@student_bp.route("/lessons/<lesson_id>/progress", methods=["POST"])
@student_required
def record_student_progress_route(lesson_id: str) -> tuple[Response, int] | Response:
    """Heartbeat endpoint to record lesson engagement progress."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    if not isinstance(payload, dict):
        raise LessonValidationError("Invalid JSON payload.")

    seconds_increment = payload.get("seconds_increment")
    view_fraction = payload.get("view_fraction")

    if seconds_increment is None or view_fraction is None:
        raise LessonValidationError("Both seconds_increment and view_fraction are required.")

    try:
        sec_int = int(seconds_increment)
        vf_float = float(view_fraction)
    except (ValueError, TypeError):
        raise LessonValidationError(
            "seconds_increment must be an integer and view_fraction must be a float."
        ) from None

    progress = record_lesson_progress(
        actor=actor,
        lesson_id=lesson_id,
        seconds_increment=sec_int,
        view_fraction=vf_float,
    )

    data = {
        "lesson_id": str(progress.lesson.public_id) if progress.lesson else None,
        "seconds_spent": progress.seconds_spent,
        "max_view_fraction": float(progress.max_view_fraction),
        "is_completed": progress.completed_at is not None,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
    }
    return jsonify(data), 200


def _serialize_enrollment(e: Enrollment) -> dict[str, Any]:
    return {
        "enrollment_id": str(e.public_id),
        "course_id": str(e.course.public_id) if e.course else None,
        "course_code": e.course.course_code if e.course else None,
        "course_title": e.course.title if e.course else None,
        "student_id": str(e.student.public_id) if e.student else None,
        "status": e.status,
        "period_no": e.current_period.period_no if e.current_period else None,
        "current_progress_percent": float(e.current_progress_percent),
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        "left_at": e.left_at.isoformat() if e.left_at else None,
        "detail_retention_due_at": (
            e.detail_retention_due_at.isoformat() if e.detail_retention_due_at else None
        ),
    }


_serialize_enrollment_api = _serialize_enrollment


@student_bp.route("/courses/<course_id>/enroll", methods=["POST"])
@student_required
def student_enroll_course(course_id: str) -> tuple[Response, int] | Response:
    """Self-enroll in a published course."""
    actor = require_authenticated_actor()

    enrollment = enroll_student(actor=actor, course_id=course_id, session=db.session)
    status_code = 201 if getattr(enrollment, "_is_new", False) else 200
    return jsonify(_serialize_enrollment(enrollment)), status_code


@student_bp.route("/courses/<course_id>/leave", methods=["POST"])
@student_required
def student_leave_course(course_id: str) -> tuple[Response, int] | Response:
    """Withdraw from an active course."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        reason = str(reason)

    enrollment = leave_course(actor=actor, course_id=course_id, reason=reason, session=db.session)
    return jsonify(_serialize_enrollment(enrollment)), 200


@student_bp.route("/courses/<course_id>/re-enroll", methods=["POST"])
@student_required
def student_re_enroll_course(course_id: str) -> tuple[Response, int] | Response:
    """Re-enroll in a previously left course."""
    actor = require_authenticated_actor()

    enrollment = re_enroll_student(actor=actor, course_id=course_id, session=db.session)
    return jsonify(_serialize_enrollment(enrollment)), 200


@student_bp.route("/enrollments", methods=["GET"])
@student_required
def student_list_enrollments() -> tuple[Response, int] | Response:
    """List all enrollments belonging to the authenticated student."""
    actor = require_authenticated_actor()

    status = request.args.get("status")
    enrollments = get_student_enrollments(actor=actor, status=status, session=db.session)
    return jsonify({"enrollments": [_serialize_enrollment(e) for e in enrollments]}), 200


@student_bp.route("/courses/<course_id>/completion", methods=["GET"])
@student_required
def get_student_course_completion_route(course_id: str) -> tuple[Response, int] | Response:
    """Get the authenticated student's completion summary for a course."""
    actor = require_authenticated_actor()

    course = _resolve_course(course_id, session=db.session)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    summary = get_course_completion_summary(
        actor=actor,
        course_id=course.id,
        student_user_id=actor.id,
        session=db.session,
    )

    enrollment = (
        db.session.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )

    data = {
        "course_id": str(course.public_id),
        "course_code": course.course_code,
        "course_title": course.title,
        "student_id": str(actor.public_id),
        "ever_completed": summary.ever_completed if summary else False,
        "first_completed_at": (
            summary.first_completed_at.isoformat()
            if summary and summary.first_completed_at
            else None
        ),
        "latest_completed_at": (
            summary.latest_completed_at.isoformat()
            if summary and summary.latest_completed_at
            else None
        ),
        "prerequisite_eligible": summary.prerequisite_eligible if summary else False,
        "current_status": enrollment.status if enrollment else None,
        "current_progress_percent": (
            float(enrollment.current_progress_percent) if enrollment else 0.0
        ),
    }
    return jsonify(data), 200


@student_bp.route("/notifications", methods=["GET"])
@student_required
def notifications_center() -> tuple[Response, int] | Response:
    """Student Web notifications center page and AJAX endpoint."""
    from flask import render_template

    from pwd301.services.authorization_service import _is_api_or_json_request
    from pwd301.services.notification_service import (
        get_unread_count,
        get_user_preferences,
        list_user_notifications,
    )

    actor = require_authenticated_actor()
    items, total = list_user_notifications(actor=actor, session=db.session)
    prefs = get_user_preferences(actor=actor, session=db.session)
    unread = get_unread_count(actor=actor, session=db.session)

    if _is_api_or_json_request():
        return (
            jsonify(
                {
                    "items": items,
                    "total": total,
                    "unread_count": unread,
                    "preferences": prefs,
                }
            ),
            200,
        )

    rendered = render_template(
        "notifications/index.html",
        notifications=items,
        total=total,
        unread_count=unread,
        preferences=prefs,
    )
    from flask import make_response

    return make_response(rendered)
