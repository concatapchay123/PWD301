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
        "current_progress_percent": float(e.current_progress_percent),
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
            float(enrollment.current_progress_percent) if enrollment else 0.0
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
