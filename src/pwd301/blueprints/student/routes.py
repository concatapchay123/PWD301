"""Route handlers for the student role blueprint."""

from __future__ import annotations

from flask import Response, jsonify

from pwd301.blueprints.student import student_bp
from pwd301.extensions import db
from pwd301.models.course import Enrollment
from pwd301.services.authorization_service import (
    _resolve_course,
    get_authenticated_actor,
    student_required,
)
from pwd301.services.exceptions import ResourceNotFoundError


@student_bp.route("/dashboard", methods=["GET"])
@student_required
def dashboard() -> tuple[Response, int] | Response:
    """Student dashboard displaying current enrolled courses."""
    actor = get_authenticated_actor()
    assert actor is not None

    sess = db.session
    enrollments = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == actor.id,
            Enrollment.status == "ACTIVE",
        )
        .all()
    )

    data = {
        "student_id": str(actor.public_id),
        "student_name": actor.display_name,
        "enrolled_courses_count": len(enrollments),
        "enrollments": [
            {
                "enrollment_id": str(e.public_id),
                "course_id": str(e.course.public_id) if e.course else None,
                "course_title": e.course.title if e.course else None,
                "progress_percent": float(e.current_progress_percent),
                "status": e.status,
            }
            for e in enrollments
        ],
    }
    return jsonify(data), 200


@student_bp.route("/courses/<course_id>/progress", methods=["GET"])
@student_required
def course_progress(course_id: str) -> tuple[Response, int] | Response:
    """Get the authenticated student's progress in a specific course."""
    actor = get_authenticated_actor()
    assert actor is not None

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
