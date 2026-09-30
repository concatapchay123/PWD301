"""REST API route handlers for Lesson details and progress tracking."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_lessons import api_lesson_bp
from pwd301.extensions import db
from pwd301.models.course import Lesson, LessonProgress
from pwd301.services.authorization_service import (
    get_authenticated_actor,
    instructor_required,
    require_authenticated_actor,
    student_required,
)
from pwd301.services.exceptions import ForbiddenError, LessonValidationError
from pwd301.services.jwt_auth_service import jwt_required
from pwd301.services.lesson_service import (
    change_lesson_status,
    create_lesson,
    get_lesson_detail,
    queue_lesson_resource_change,
    queue_lesson_review,
    record_lesson_progress,
    trash_lesson,
    update_lesson,
)


def _serialize_lesson(les: Lesson, include_content: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "lesson_id": str(les.public_id),
        "learning_unit_id": str(les.learning_unit.public_id) if les.learning_unit else None,
        "learning_unit_title": les.learning_unit.title if les.learning_unit else None,
        "course_id": str(les.course.public_id) if les.course else None,
        "title": les.title,
        "summary": les.summary,
        "position": les.position,
        "estimated_duration_minutes": les.estimated_duration_minutes,
        "minimum_completion_seconds": les.minimum_completion_seconds,
        "viewed_fraction_required": float(les.viewed_fraction_required),
        "status": les.status,
        "revision_no": getattr(les, "revision_no", 1) or 1,
        "previous_lesson_id": getattr(les, "previous_lesson_id", None),
        "material_change_summary": getattr(les, "material_change_summary", None),
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
        "acknowledged_revision_no": getattr(p, "acknowledged_revision_no", None),
        "last_activity_at": p.last_activity_at.isoformat() if p.last_activity_at else None,
        "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        "is_completed": p.completed_at is not None,
    }


@api_lesson_bp.route("/<lesson_id>", methods=["GET"])
@jwt_required
def get_lesson_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Read lesson details with authorization checks.

    Instructor of course / Admin: can read any status and includes working draft if present.
    Student: must have ACTIVE enrollment and lesson must be PUBLISHED (or HISTORICAL for in-flight).
    """
    actor = get_authenticated_actor()
    lesson = get_lesson_detail(actor, lesson_id)
    data = _serialize_lesson(lesson)
    if actor and (actor.is_admin or (actor.has_role("INSTRUCTOR") and lesson.course and lesson.course.owner_instructor_id == actor.id)):
        from pwd301.services.lesson_service import get_lesson_detail_with_draft
        _, working_draft = get_lesson_detail_with_draft(actor, lesson_id, session=db.session)
        data["working_draft"] = working_draft
    return jsonify(data), 200


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

    seconds_increment = (
        payload.get("seconds_increment")
        if payload.get("seconds_increment") is not None
        else (
            payload.get("seconds")
            if payload.get("seconds") is not None
            else (
                payload.get("time_delta")
                if payload.get("time_delta") is not None
                else payload.get("time_delta_seconds")
            )
        )
    )
    view_fraction = (
        payload.get("view_fraction")
        if payload.get("view_fraction") is not None
        else payload.get("observed_view_fraction")
    )
    client_event_id = payload.get("client_event_id")

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
        client_event_id=client_event_id,
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
        _resolve_file_asset,
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

    original = get_lesson_detail(actor, lesson_id)
    if (
        not actor.is_admin
        and original.status != "DRAFT"
        and original.course.status in ("APPROVED", "PUBLISHED", "ARCHIVED")
    ):
        asset = _resolve_file_asset(asset_id, session=db.session)
        review = queue_lesson_resource_change(
            actor, original.course, original, "ATTACH", asset=asset, label=label
        )
        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "change_request_id": review.id,
            }
        ), 202

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
    original = get_lesson_detail(actor, lesson_id)
    if (
        not actor.is_admin
        and original.status != "DRAFT"
        and original.course.status in ("APPROVED", "PUBLISHED", "ARCHIVED")
    ):
        review = queue_lesson_resource_change(
            actor, original.course, original, "DETACH", resource_id=resource_id
        )
        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "change_request_id": review.id,
            }
        ), 202
    detached = detach_resource_from_lesson(
        actor=actor,
        lesson_id=lesson_id,
        resource_id=resource_id,
        session=db.session,
    )
    return jsonify({"detached": detached}), 200


@api_lesson_bp.route("", methods=["POST"])
@jwt_required
@instructor_required
def create_lesson_api() -> tuple[Response, int] | Response:
    """Create a new lesson specifying course_id in request body (JWT required)."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    course_id = payload.get("course_id")
    if not course_id:
        raise LessonValidationError("course_id is required in request body.")

    from pwd301.services.authorization_service import _resolve_course
    from pwd301.services.exceptions import ResourceNotFoundError

    course = _resolve_course(course_id, session=db.session)
    if course is None:
        raise ResourceNotFoundError("Course not found.")

    if not actor.is_admin and course.status in ("APPROVED", "PUBLISHED", "ARCHIVED"):
        from pwd301.services.lesson_service import create_lesson_change_request

        payload["change_type"] = "LESSON_STRUCTURE"
        payload["action"] = "CREATE_LESSON"
        req, lesson = create_lesson_change_request(actor, course.id, payload, session=db.session)
        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "change_request_id": req.id,
                "lesson": _serialize_lesson(lesson),
            }
        ), 202

    lesson = create_lesson(actor, course_id, payload, session=db.session)
    return jsonify(_serialize_lesson(lesson)), 201


@api_lesson_bp.route("/<lesson_id>", methods=["PUT", "PATCH"])
@jwt_required
@instructor_required
def update_lesson_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Update editable lesson fields (title, content, duration, etc.) (JWT required)."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    original = get_lesson_detail(actor, lesson_id)
    if (
        not actor.is_admin
        and original.status != "DRAFT"
        and original.course.status in ("APPROVED", "PUBLISHED", "ARCHIVED")
    ):
        review = queue_lesson_review(actor, original.course, original, "LESSON_CONTENT", payload)
        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "change_request_id": review.id,
                "lesson": _serialize_lesson(original),
            }
        ), 202
    lesson = update_lesson(actor, lesson_id, payload, session=db.session)
    return jsonify(_serialize_lesson(lesson)), 200


@api_lesson_bp.route("/<lesson_id>", methods=["DELETE"])
@api_lesson_bp.route("/<lesson_id>/trash", methods=["POST"])
@jwt_required
@instructor_required
def trash_lesson_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a lesson to TRASH (JWT required)."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason")
    original = get_lesson_detail(actor, lesson_id)
    if not actor.is_admin and original.status != "DRAFT" and (
        original.course.status in ("APPROVED", "PUBLISHED", "ARCHIVED")
        or original.status == "PUBLISHED"
    ):
        review = queue_lesson_review(
            actor,
            original.course,
            original,
            "LESSON_STRUCTURE",
            {
                "action": "DELETE",
                "lesson_id": original.id,
                "reason": reason or "Giảng viên yêu cầu xóa bài giảng",
            },
        )
        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "change_request_id": review.id,
            }
        ), 202
    lesson = trash_lesson(actor, lesson_id, reason=reason, session=db.session)
    return (
        jsonify(
            {
                "message": "Lesson moved to TRASH.",
                "lesson": _serialize_lesson(lesson, include_content=False),
            }
        ),
        200,
    )


@api_lesson_bp.route("/<lesson_id>/status", methods=["POST"])
@jwt_required
@instructor_required
def change_lesson_status_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Transition lesson status (DRAFT, PUBLISHED, HIDDEN) (JWT required)."""
    actor = require_authenticated_actor()
    payload = request.get_json(silent=True) or {}
    new_status = str(payload.get("status") or payload.get("new_status") or "").strip().upper()
    reason = payload.get("reason")
    original = get_lesson_detail(actor, lesson_id)
    if (
        not actor.is_admin
        and original.course.status in ("APPROVED", "PUBLISHED", "ARCHIVED")
        and new_status != original.status
    ):
        review = queue_lesson_review(
            actor, original.course, original, "LESSON_CONTENT", {"status": new_status}
        )
        return jsonify(
            {
                "status": "pending_approval",
                "pending_approval": True,
                "change_request_id": review.id,
            }
        ), 202
    lesson = change_lesson_status(actor, lesson_id, new_status, reason=reason, session=db.session)
    return jsonify(_serialize_lesson(lesson)), 200


@api_lesson_bp.route("/<lesson_id>/draft/discard", methods=["POST"])
@jwt_required
@instructor_required
def discard_lesson_draft_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Discard an active working draft for a lesson."""
    actor = require_authenticated_actor()
    from pwd301.services.lesson_service import discard_lesson_working_draft
    discarded = discard_lesson_working_draft(actor, lesson_id, session=db.session)
    return jsonify({"success": True, "discarded": discarded}), 200


@api_lesson_bp.route("/<lesson_id>/opt-in", methods=["POST"])
@jwt_required
@student_required
def opt_in_lesson_revision_api(lesson_id: str) -> tuple[Response, int] | Response:
    """Student opts in to the latest published lesson revision."""
    actor = require_authenticated_actor()
    from pwd301.services.lesson_service import opt_in_newer_lesson_revision
    latest_lesson, progress = opt_in_newer_lesson_revision(actor, lesson_id, session=db.session)
    return jsonify({
        "success": True,
        "lesson": _serialize_lesson(latest_lesson),
        "progress": _serialize_progress(progress),
    }), 200
