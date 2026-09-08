"""REST API route handlers for Course catalog and lifecycle per 04_COURSE_API.md."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_courses import api_course_bp
from pwd301.extensions import db
from pwd301.models.course import Course, Enrollment, Lesson
from pwd301.services.authorization_service import (
    get_authenticated_actor,
    instructor_required,
)
from pwd301.services.course_service import (
    change_course_status,
    create_course,
    get_course_detail,
    list_courses,
    update_course,
)
from pwd301.services.enrollment_service import (
    add_course_prerequisite,
    enroll_student,
    get_course_enrollments,
    get_course_prerequisites,
    leave_course,
    re_enroll_student,
    remove_course_prerequisite,
)
from pwd301.services.exceptions import CourseValidationError
from pwd301.services.lesson_service import get_course_lessons


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
        "published_at": c.published_at.isoformat() if c.published_at else None,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


@api_course_bp.route("", methods=["GET"])
def list_courses_catalog() -> tuple[Response, int] | Response:
    """Course catalog with pagination and filtering.

    Authentication is optional. Published courses are discoverable by everyone.
    """
    actor = get_authenticated_actor()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    q = request.args.get("q")
    category = request.args.get("category")
    difficulty = request.args.get("difficulty")
    status = request.args.get("status")

    courses, total = list_courses(
        actor=actor,
        status=status,
        category=category,
        difficulty=difficulty,
        search=q,
        page=page,
        per_page=per_page,
    )

    data = {
        "items": [_serialize_course(c) for c in courses],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
        },
    }
    return jsonify(data), 200


@api_course_bp.route("", methods=["POST"])
@instructor_required
def create_course_api() -> tuple[Response, int] | Response:
    """Create a new course (Instructor/Admin required)."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    course = create_course(actor, payload)
    return jsonify(_serialize_course(course)), 201


@api_course_bp.route("/<course_id>", methods=["GET"])
def get_course_detail_api(course_id: str) -> tuple[Response, int] | Response:
    """Read course details adhering to visibility rules."""
    actor = get_authenticated_actor()
    course = get_course_detail(actor, course_id)
    return jsonify(_serialize_course(course)), 200


@api_course_bp.route("/<course_id>", methods=["PATCH"])
@instructor_required
def update_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Update editable course metadata with mass-assignment defense."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    course = update_course(actor, course_id, payload)
    return jsonify(_serialize_course(course)), 200


@api_course_bp.route("/<course_id>/publish-request", methods=["POST"])
@instructor_required
def publish_request_api(course_id: str) -> tuple[Response, int] | Response:
    """Submit course for review."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="SUBMITTED_FOR_REVIEW",
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


@api_course_bp.route("/<course_id>/archive", methods=["POST"])
@instructor_required
def archive_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Archive a course."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="ARCHIVED",
        reason=reason,
    )
    return jsonify(_serialize_course(course)), 200


def _serialize_lesson_summary(les: Lesson) -> dict[str, Any]:
    return {
        "lesson_id": str(les.public_id),
        "title": les.title,
        "summary": les.summary,
        "position": les.position,
        "estimated_duration_minutes": les.estimated_duration_minutes,
        "minimum_completion_seconds": les.minimum_completion_seconds,
        "viewed_fraction_required": float(les.viewed_fraction_required),
        "status": les.status,
    }


@api_course_bp.route("/<course_id>/lessons", methods=["GET"])
def get_course_lessons_api(course_id: str) -> tuple[Response, int] | Response:
    """List lessons belonging to a course scoped by caller permissions."""
    actor = get_authenticated_actor()
    lessons = get_course_lessons(actor, course_id)
    return jsonify({"lessons": [_serialize_lesson_summary(les) for les in lessons]}), 200


def _serialize_enrollment_api(e: Enrollment) -> dict[str, Any]:
    return {
        "enrollment_id": str(e.public_id),
        "course_id": str(e.course.public_id) if e.course else None,
        "course_code": e.course.course_code if e.course else None,
        "course_title": e.course.title if e.course else None,
        "student_id": str(e.student.public_id) if e.student else None,
        "status": e.status,
        "current_period_id": e.current_period_id,
        "current_progress_percent": float(e.current_progress_percent),
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        "left_at": e.left_at.isoformat() if e.left_at else None,
        "detail_retention_due_at": (
            e.detail_retention_due_at.isoformat() if e.detail_retention_due_at else None
        ),
    }


def _serialize_prerequisite_api(c: Course) -> dict[str, Any]:
    return {
        "course_id": str(c.public_id),
        "course_code": c.course_code,
        "title": c.title,
        "category": c.category,
        "difficulty": c.difficulty,
        "status": c.status,
    }


@api_course_bp.route("/<course_id>/enroll", methods=["POST"])
def enroll_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Enroll authenticated student into a course per 05_ENROLLMENT_PROGRESS_API.md."""
    actor = get_authenticated_actor()
    if actor is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required to enroll in course.",
                    }
                }
            ),
            401,
        )

    from pwd301.services.authorization_service import _resolve_course
    from pwd301.services.exceptions import EnrollmentStateViolationError

    try:
        enrollment = enroll_student(actor=actor, course_id=course_id, session=db.session)
        db.session.commit()
        return jsonify(_serialize_enrollment_api(enrollment)), 201
    except EnrollmentStateViolationError as err:
        # Idempotent for already-active enrollment
        c = _resolve_course(course_id, session=db.session)
        if c is not None:
            existing = (
                db.session.query(Enrollment)
                .filter(Enrollment.student_user_id == actor.id, Enrollment.course_id == c.id)
                .first()
            )
            if existing and existing.status == "ACTIVE":
                return jsonify(_serialize_enrollment_api(existing)), 200
        raise err


@api_course_bp.route("/<course_id>/leave", methods=["POST"])
def leave_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Withdraw authenticated student from a course per 05_ENROLLMENT_PROGRESS_API.md."""
    actor = get_authenticated_actor()
    if actor is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required to leave course.",
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    if reason is not None and not isinstance(reason, str):
        reason = str(reason)

    from pwd301.services.authorization_service import _resolve_course
    from pwd301.services.exceptions import EnrollmentStateViolationError

    try:
        enrollment = leave_course(
            actor=actor, course_id=course_id, reason=reason, session=db.session
        )
        db.session.commit()
        return jsonify(_serialize_enrollment_api(enrollment)), 200
    except EnrollmentStateViolationError as err:
        # State-idempotent for already-left enrollment
        c = _resolve_course(course_id, session=db.session)
        if c is not None:
            existing = (
                db.session.query(Enrollment)
                .filter(Enrollment.student_user_id == actor.id, Enrollment.course_id == c.id)
                .first()
            )
            if existing and existing.status == "LEFT":
                return jsonify(_serialize_enrollment_api(existing)), 200
        raise err


@api_course_bp.route("/<course_id>/re-enroll", methods=["POST"])
def re_enroll_course_api(course_id: str) -> tuple[Response, int] | Response:
    """Re-enroll in a previously left course."""
    actor = get_authenticated_actor()
    if actor is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Authentication required to re-enroll.",
                    }
                }
            ),
            401,
        )

    enrollment = re_enroll_student(actor=actor, course_id=course_id, session=db.session)
    db.session.commit()
    return jsonify(_serialize_enrollment_api(enrollment)), 200


@api_course_bp.route("/<course_id>/prerequisites", methods=["GET"])
def get_course_prerequisites_api(course_id: str) -> tuple[Response, int] | Response:
    """Read prerequisite courses for a course."""
    prereqs = get_course_prerequisites(course_id, session=db.session)
    return jsonify({"prerequisites": [_serialize_prerequisite_api(c) for c in prereqs]}), 200


@api_course_bp.route("/<course_id>/prerequisites", methods=["POST"])
@instructor_required
def add_course_prerequisite_api(course_id: str) -> tuple[Response, int] | Response:
    """Add a prerequisite course dependency (Instructor/Admin required)."""
    actor = get_authenticated_actor()
    assert actor is not None

    payload = request.get_json(silent=True) or {}
    prerequisite_course_id = payload.get("prerequisite_course_id")
    if not prerequisite_course_id:
        raise CourseValidationError("prerequisite_course_id is required.")

    link = add_course_prerequisite(
        actor=actor,
        course_id=course_id,
        prerequisite_course_id=prerequisite_course_id,
        session=db.session,
    )
    db.session.commit()
    return (
        jsonify(
            {
                "course_id": str(link.course.public_id) if link.course else str(link.course_id),
                "prerequisite_course_id": (
                    str(link.prerequisite_course.public_id)
                    if link.prerequisite_course
                    else str(link.prerequisite_course_id)
                ),
                "created_at": link.created_at.isoformat(),
            }
        ),
        201,
    )


@api_course_bp.route("/<course_id>/prerequisites/<prereq_id>", methods=["DELETE"])
@instructor_required
def remove_course_prerequisite_api(
    course_id: str, prereq_id: str
) -> tuple[Response, int] | Response:
    """Remove a prerequisite course dependency (Instructor/Admin required)."""
    actor = get_authenticated_actor()
    assert actor is not None

    removed = remove_course_prerequisite(
        actor=actor,
        course_id=course_id,
        prerequisite_course_id=prereq_id,
        session=db.session,
    )
    db.session.commit()
    return jsonify({"removed": removed}), 200


@api_course_bp.route("/<course_id>/enrollments", methods=["GET"])
@instructor_required
def get_course_enrollments_api(course_id: str) -> tuple[Response, int] | Response:
    """List enrolled students for managed course."""
    actor = get_authenticated_actor()
    assert actor is not None

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")

    items, total = get_course_enrollments(
        actor=actor,
        course_id=course_id,
        status=status,
        page=page,
        per_page=per_page,
        session=db.session,
    )
    return (
        jsonify(
            {
                "items": [_serialize_enrollment_api(e) for e in items],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_items": total,
                    "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
                },
            }
        ),
        200,
    )
