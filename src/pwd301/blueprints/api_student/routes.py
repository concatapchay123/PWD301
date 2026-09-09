"""REST API routes for Student operations per 05_ENROLLMENT_PROGRESS_API.md."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_student import api_student_bp
from pwd301.extensions import db
from pwd301.models.course import Enrollment
from pwd301.services.authorization_service import (
    get_authenticated_actor,
    student_required,
)
from pwd301.services.enrollment_service import get_student_enrollments


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
@student_required
def get_student_enrollments_api() -> tuple[Response, int] | Response:
    """Retrieve enrollments for the authenticated student."""
    actor = get_authenticated_actor()
    assert actor is not None

    status = request.args.get("status")
    enrollments = get_student_enrollments(actor=actor, status=status, session=db.session)
    return jsonify({"enrollments": [_serialize_enrollment_api(e) for e in enrollments]}), 200
