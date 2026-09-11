"""REST API route handlers for Lesson details and progress tracking."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_lessons import api_lesson_bp
from pwd301.models.course import Lesson, LessonProgress
from pwd301.services.authorization_service import (
    get_authenticated_actor,
    instructor_required,
    student_required,
)
from pwd301.services.exceptions import ForbiddenError, LessonValidationError
from pwd301.services.jwt_auth_service import jwt_required
from pwd301.services.lesson_service import (
    get_lesson_detail,
    record_lesson_progress,
)


def _serialize_lesson(les: Lesson, include_content: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "lesson_id": str(les.public_id),
        "course_id": str(les.course.public_id) if les.course else None,
        "title": les.title,
        "summary": les.summary,
        "position": les.position,
        "estimated_duration_minutes": les.estimated_duration_minutes,
        "minimum_completion_seconds": les.minimum_completion_seconds,
        "viewed_fraction_required": float(les.viewed_fraction_required),
        "status": les.status,
        "published_at": les.published_at.isoformat() if les.published_at else None,
        "created_at": les.created_at.isoformat(),
        "updated_at": les.updated_at.isoformat(),
    }
    if include_content:
        data["markdown_content"] = les.markdown_content
    return data


def _serialize_progress(p: LessonProgress) -> dict[str, Any]:
    return {
        "lesson_id": str(p.lesson.public_id) if p.lesson else None,
        "seconds_spent": p.seconds_spent,
        "max_view_fraction": float(p.max_view_fraction),
        "last_activity_at": p.last_activity_at.isoformat() if p.last_activity_at else None,
        "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        "is_completed": p.completed_at is not None,
    }


@api_lesson_bp.route("/<lesson_id>", methods=["GET"])
@jwt_required
def get_lesson_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Read lesson details with authorization checks.

    Instructor of course / Admin: can read any status.
    Student: must have ACTIVE enrollment and lesson must be PUBLISHED.
    """
    actor = get_authenticated_actor()
    lesson = get_lesson_detail(actor, lesson_id)
    return jsonify(_serialize_lesson(lesson)), 200


@api_lesson_bp.route("/<lesson_id>/progress", methods=["POST"])
@jwt_required
@student_required
def record_progress_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Record bounded learning progress heartbeat (Algorithm 02)."""
    actor = get_authenticated_actor()
    if actor is None:
        raise ForbiddenError("Authentication required.")

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        raise LessonValidationError("Invalid JSON payload.")

    seconds_increment = payload.get("seconds_increment")
    view_fraction = payload.get("view_fraction")

    if seconds_increment is None:
        raise LessonValidationError("seconds_increment is required.")
    if view_fraction is None:
        raise LessonValidationError("view_fraction is required.")

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
    return jsonify(_serialize_progress(progress)), 200


@api_lesson_bp.route("/<lesson_id>/activity", methods=["POST"])
@jwt_required
@student_required
def record_activity_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Alias for /progress conforming to 04_COURSE_API.md activity endpoint."""
    return record_progress_api(lesson_id)


@api_lesson_bp.route("/<lesson_id>/resources", methods=["POST"])
@jwt_required
@instructor_required
def attach_lesson_resource_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Attach a FileAsset to a Lesson as a learning resource (JWT required)."""
    from pwd301.extensions import db
    from pwd301.services.authorization_service import require_authenticated_actor
    from pwd301.services.exceptions import FileValidationError
    from pwd301.services.file_service import (
        _serialize_lesson_resource,
        attach_resource_to_lesson,
    )

    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    asset_id = payload.get("file_asset_id") or payload.get("asset_id")
    if not asset_id:
        raise FileValidationError("file_asset_id is required.")

    label = payload.get("label") or payload.get("title")
    is_downloadable = payload.get("is_downloadable", True)

    resource = attach_resource_to_lesson(
        actor=actor,
        lesson_id=lesson_id,
        asset_id=asset_id,
        is_downloadable=is_downloadable,
        label=label,
        session=db.session,
    )
    return jsonify(_serialize_lesson_resource(resource)), 201


@api_lesson_bp.route("/<lesson_id>/resources/<resource_id>", methods=["DELETE"])
@jwt_required
@instructor_required
def detach_lesson_resource_api(lesson_id: str, resource_id: str) -> tuple[Response, int] | Response:
    """Detach a learning resource link from a Lesson (JWT required)."""
    from pwd301.extensions import db
    from pwd301.services.authorization_service import require_authenticated_actor
    from pwd301.services.file_service import detach_resource_from_lesson

    actor = require_authenticated_actor()
    detached = detach_resource_from_lesson(
        actor=actor,
        lesson_id=lesson_id,
        resource_id=resource_id,
        session=db.session,
    )
    return jsonify({"detached": detached}), 200
