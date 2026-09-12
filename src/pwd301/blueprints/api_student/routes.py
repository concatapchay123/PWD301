"""REST API routes for Student operations per 05_ENROLLMENT_PROGRESS_API.md."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_student import api_student_bp
from pwd301.extensions import db
from pwd301.models.course import Enrollment
from pwd301.services.analytics_service import get_student_learning_overview
from pwd301.services.authorization_service import (
    _resolve_course,
    require_authenticated_actor,
    student_required,
)
from pwd301.services.completion_service import get_course_completion_summary
from pwd301.services.enrollment_service import get_student_enrollments
from pwd301.services.exceptions import ResourceNotFoundError
from pwd301.services.jwt_auth_service import jwt_required


def _serialize_enrollment_api(e: Enrollment) -> dict[str, Any]:
    return {
        "enrollment_id": str(e.public_id),
        "course_id": str(e.course.public_id) if e.course else None,
        "course_code": e.course.course_code if e.course else None,
        "course_title": e.course.title if e.course else None,
        "student_id": str(e.student.public_id) if e.student else None,
        "status": e.status,
        "period_no": e.current_period.period_no if e.current_period else None,
        "current_progress_percent": float(e.current_progress_percent or 0.0),
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        "left_at": e.left_at.isoformat() if e.left_at else None,
        "detail_retention_due_at": (
            e.detail_retention_due_at.isoformat() if e.detail_retention_due_at else None
        ),
    }


@api_student_bp.route("/enrollments", methods=["GET"])
@jwt_required
@student_required
def get_student_enrollments_api() -> tuple[Response, int] | Response:
    """Retrieve enrollments for the authenticated student."""
    actor = require_authenticated_actor()

    status = request.args.get("status")
    enrollments = get_student_enrollments(actor=actor, status=status, session=db.session)
    return jsonify({"enrollments": [_serialize_enrollment_api(e) for e in enrollments]}), 200


@api_student_bp.route("/courses/<course_id>/completion", methods=["GET"])
@jwt_required
@student_required
def get_student_course_completion_api(course_id: str) -> tuple[Response, int] | Response:
    """Retrieve completion summary for the authenticated student (REST API)."""
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
            float(enrollment.current_progress_percent or 0.0) if enrollment else 0.0
        ),
    }
    return jsonify(data), 200


@api_student_bp.route("/analytics/overview", methods=["GET"])
@jwt_required
@student_required
def get_student_analytics_overview_api() -> tuple[Response, int] | Response:
    """Retrieve personalized learning analytics dashboard for student."""
    actor = require_authenticated_actor()
    overview = get_student_learning_overview(actor, session=db.session)
    return jsonify(overview), 200


@api_student_bp.route("/instructor-application", methods=["GET"])
@jwt_required
@student_required
def get_instructor_application_api() -> tuple[Response, int] | Response:
    """Retrieve current user's instructor nomination application status (JWT required)."""
    from pwd301.services.user_service import get_user_active_application

    actor = require_authenticated_actor()
    app_record = get_user_active_application(actor.id, session=db.session)
    return (
        jsonify(
            {
                "is_already_instructor": actor.is_instructor,
                "application": (
                    {
                        "id": app_record.id,
                        "status": app_record.status,
                        "status_label": app_record.status_label_vi,
                        "details": app_record.parsed_details,
                        "review_reason": app_record.review_reason,
                        "created_at": app_record.created_at.isoformat(),
                        "reviewed_at": app_record.reviewed_at.isoformat()
                        if app_record.reviewed_at
                        else None,
                    }
                    if app_record
                    else None
                ),
            }
        ),
        200,
    )


@api_student_bp.route("/instructor-application", methods=["POST"])
@jwt_required
@student_required
def submit_instructor_application_api() -> tuple[Response, int] | Response:
    """Submit an application to become an instructor (JWT required)."""
    from pwd301.services.exceptions import ValidationError
    from pwd301.services.user_service import submit_instructor_application

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}

    try:
        app_record = submit_instructor_application(
            user_id=actor.id,
            application_data=payload,
            session=db.session,
        )
    except ValidationError as exc:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(exc)}}), 400

    return (
        jsonify(
            {
                "message": "Đơn đăng ký đã được gửi thành công.",
                "application_id": app_record.id,
                "status": app_record.status,
            }
        ),
        201,
    )


@api_student_bp.route("/instructor-application/cancel", methods=["POST"])
@jwt_required
@student_required
def cancel_instructor_application_api() -> tuple[Response, int] | Response:
    """Cancel a pending instructor application (JWT required)."""
    from pwd301.services.exceptions import ResourceNotFoundError, ValidationError
    from pwd301.services.user_service import (
        cancel_instructor_application,
        get_user_active_application,
    )

    actor = require_authenticated_actor()
    app_record = get_user_active_application(actor.id, session=db.session)
    if app_record is None or app_record.status != "PENDING":
        return jsonify(
            {"error": {"code": "NOT_FOUND", "message": "Không có đơn đang chờ xét duyệt."}}
        ), 404

    try:
        cancelled = cancel_instructor_application(
            user_id=actor.id,
            application_id=app_record.id,
            session=db.session,
        )
    except (ValidationError, ResourceNotFoundError) as exc:
        return jsonify({"error": {"code": "ERROR", "message": str(exc)}}), 400

    return jsonify({"message": "Đã hủy đơn đăng ký.", "status": cancelled.status}), 200
