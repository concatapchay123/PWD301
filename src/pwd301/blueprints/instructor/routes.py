from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.instructor import instructor_bp
from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment
from pwd301.services.authorization_service import (
    get_authenticated_actor,
    instructor_required,
    require_course_manager,
    require_student_data_access,
)
from pwd301.services.course_service import (
    change_course_status,
    create_course,
    get_course_detail,
    trash_course,
    update_course,
)


def _serialize_course(c: Course) -> dict[str, Any]:
    return {
        "course_id": str(c.public_id),
        "course_code": c.course_code,
        "title": c.title,
        "description": c.description,
        "category": c.category,
        "difficulty": c.difficulty,
        "capacity": c.capacity,
        "status": c.status,
        "owner_instructor_id": (str(c.owner_instructor.public_id) if c.owner_instructor else None),
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


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


@instructor_bp.route("/courses", methods=["POST"])
@instructor_required
def create_course_route() -> tuple[Response, int] | Response:
    """Create a new course in DRAFT status."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    course = create_course(actor, payload)
    return jsonify(_serialize_course(course)), 201


@instructor_bp.route("/courses/<course_id>", methods=["GET"])
@instructor_required
def get_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Get detailed course information for managing."""
    actor = get_authenticated_actor()
    assert actor is not None

    course = get_course_detail(actor, course_id)
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>", methods=["PATCH", "PUT"])
@instructor_required
def update_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Update editable course metadata with mass-assignment defense."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    course = update_course(actor, course_id, payload)
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>/submit", methods=["POST"])
@instructor_required
def submit_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Submit a DRAFT course for admin review."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    course = change_course_status(
        actor,
        course_id,
        "SUBMITTED_FOR_REVIEW",
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


@instructor_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a course to TRASH."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    course = trash_course(actor, course_id, reason=reason)
    return jsonify(_serialize_course(course)), 200
