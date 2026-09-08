"""REST API route handlers for Course catalog and lifecycle per 04_COURSE_API.md."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_courses import api_course_bp
from pwd301.models.course import Course, Lesson
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
