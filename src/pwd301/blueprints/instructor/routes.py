"""Route handlers for the instructor role blueprint."""

from __future__ import annotations

from flask import Response, jsonify

from pwd301.blueprints.instructor import instructor_bp
from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment
from pwd301.services.authorization_service import (
    get_authenticated_actor,
    instructor_required,
    require_course_manager,
    require_student_data_access,
)


@instructor_bp.route("/dashboard", methods=["GET"])
@instructor_required
def dashboard() -> tuple[Response, int] | Response:
    """Instructor dashboard displaying courses managed by the actor."""
    actor = get_authenticated_actor()
    assert actor is not None

    sess = db.session
    if actor.is_admin:
        courses = sess.query(Course).filter(Course.deleted_at.is_(None)).all()
    else:
        courses = (
            sess.query(Course)
            .filter(
                Course.owner_instructor_id == actor.id,
                Course.deleted_at.is_(None),
            )
            .all()
        )

    data = {
        "instructor_id": str(actor.public_id),
        "instructor_name": actor.display_name,
        "managed_courses_count": len(courses),
        "courses": [
            {
                "course_id": str(c.public_id),
                "course_code": c.course_code,
                "title": c.title,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
            }
            for c in courses
        ],
    }
    return jsonify(data), 200


@instructor_bp.route("/courses/<course_id>/manage", methods=["GET"])
@instructor_required
def manage_course(course_id: str) -> tuple[Response, int] | Response:
    """Manage course view protected by resource-level ownership check.

    Invariants enforced:
    - Instructor A accessing Instructor B's course is rejected with 403 Forbidden.
    - Admin can access any course.
    """
    actor = get_authenticated_actor()
    assert actor is not None

    sess = db.session
    course = require_course_manager(actor, course_id, session=sess)

    data = {
        "course_id": str(course.public_id),
        "course_code": course.course_code,
        "title": course.title,
        "status": course.status,
        "owner_instructor_id": (
            str(course.owner_instructor.public_id) if course.owner_instructor else None
        ),
        "lessons_count": len(course.lessons),
        "enrollments_count": len(course.enrollments),
    }
    return jsonify(data), 200


@instructor_bp.route("/courses/<course_id>/students/<student_id>", methods=["GET"])
@instructor_required
def get_student_detail(course_id: str, student_id: str) -> tuple[Response, int] | Response:
    """View student detail within a managed course.

    Invariants enforced:
    - Instructor must manage this course.
    - Student must be enrolled in this course.
    - Otherwise raises ForbiddenError (403).
    """
    actor = get_authenticated_actor()
    assert actor is not None

    sess = db.session
    student, course = require_student_data_access(actor, student_id, course_id, session=sess)

    enrollment = (
        sess.query(Enrollment)
        .filter(
            Enrollment.student_user_id == student.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )

    data = {
        "course_id": str(course.public_id),
        "course_title": course.title,
        "student_id": str(student.public_id),
        "student_name": student.display_name,
        "student_email": student.email,
        "progress_percent": float(enrollment.current_progress_percent) if enrollment else 0.0,
        "enrollment_status": enrollment.status if enrollment else None,
    }
    return jsonify(data), 200
