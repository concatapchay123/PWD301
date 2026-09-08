from __future__ import annotations

import uuid
from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.instructor import instructor_bp
from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, Lesson
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
from pwd301.services.exceptions import LessonValidationError
from pwd301.services.lesson_service import (
    change_lesson_status,
    create_lesson,
    get_lesson_detail,
    reorder_lessons,
    trash_lesson,
    update_lesson,
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


def _serialize_lesson(les: Lesson) -> dict[str, Any]:
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
        "status": les.status,
        "published_at": les.published_at.isoformat() if les.published_at else None,
        "created_at": les.created_at.isoformat(),
        "updated_at": les.updated_at.isoformat(),
    }


@instructor_bp.route("/courses/<course_id>/lessons", methods=["POST"])
@instructor_required
def create_lesson_route(course_id: str) -> tuple[Response, int] | Response:
    """Create a new lesson in a managed course."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    lesson = create_lesson(actor, course_id, payload)
    return jsonify(_serialize_lesson(lesson)), 201


@instructor_bp.route("/lessons/<lesson_id>", methods=["GET"])
@instructor_required
def get_lesson_route(lesson_id: str) -> tuple[Response, int] | Response:
    """View lesson detail for authoring."""
    actor = get_authenticated_actor()
    assert actor is not None

    lesson = get_lesson_detail(actor, lesson_id)
    return jsonify(_serialize_lesson(lesson)), 200


@instructor_bp.route("/lessons/<lesson_id>", methods=["PATCH", "PUT"])
@instructor_required
def update_lesson_route(lesson_id: str) -> tuple[Response, int] | Response:
    """Update editable lesson fields."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    lesson = update_lesson(actor, lesson_id, payload)
    return jsonify(_serialize_lesson(lesson)), 200


@instructor_bp.route("/courses/<course_id>/lessons/reorder", methods=["POST"])
@instructor_required
def reorder_lessons_route(course_id: str) -> tuple[Response, int] | Response:
    """Reorder lessons within a course."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    raw_ids = payload.get("ordered_lesson_ids")
    if not isinstance(raw_ids, list):
        raise LessonValidationError("ordered_lesson_ids must be a list of lesson IDs.")

    ordered_ids: list[int | uuid.UUID | str] = [
        item for item in raw_ids if isinstance(item, (int, uuid.UUID, str))
    ]
    reordered = reorder_lessons(actor, course_id, ordered_ids)
    return jsonify({"lessons": [_serialize_lesson(les) for les in reordered]}), 200


@instructor_bp.route("/lessons/<lesson_id>/status", methods=["POST"])
@instructor_required
def change_lesson_status_route(lesson_id: str) -> tuple[Response, int] | Response:
    """Change status of a lesson (PUBLISHED, HIDDEN, DRAFT)."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    new_status = payload.get("status")
    if not new_status or not isinstance(new_status, str):
        raise LessonValidationError("status is required and must be a string.")

    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        reason = str(reason)

    lesson = change_lesson_status(actor, lesson_id, new_status, reason=reason)
    return jsonify(_serialize_lesson(lesson)), 200


@instructor_bp.route("/lessons/<lesson_id>/trash", methods=["POST", "DELETE"])
@instructor_required
def trash_lesson_route(lesson_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a lesson to TRASH."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")
    lesson = trash_lesson(actor, lesson_id, reason=reason)
    return jsonify(_serialize_lesson(lesson)), 200
