from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.admin import admin_bp
from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import User
from pwd301.services.authorization_service import (
    _resolve_user,
    admin_required,
    require_authenticated_actor,
)
from pwd301.services.course_service import (
    change_course_status,
    reassign_course_owner,
    trash_course,
)
from pwd301.services.exceptions import (
    InvalidRoleAssignmentError,
    ResourceNotFoundError,
)
from pwd301.services.user_service import assign_role_to_user, remove_role_from_user


def _serialize_course(c: Course) -> dict[str, Any]:
    return {
        "course_id": str(c.public_id),
        "course_code": c.course_code,
        "title": c.title,
        "status": c.status,
        "owner_instructor_id": (str(c.owner_instructor.public_id) if c.owner_instructor else None),
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard() -> tuple[Response, int] | Response:
    """Administrator dashboard overview."""
    actor = require_authenticated_actor()

    sess = db.session
    total_users = sess.query(User).count()
    total_courses = sess.query(Course).count()

    data = {
        "admin_id": str(actor.public_id),
        "admin_name": actor.display_name,
        "total_users": total_users,
        "total_courses": total_courses,
    }
    return jsonify(data), 200


@admin_bp.route("/users/<user_id>/roles", methods=["POST"])
@admin_required
def manage_user_roles(user_id: str) -> tuple[Response, int] | Response:
    """Assign or revoke user roles adhering to AUTH-002 cumulative hierarchy."""
    actor = require_authenticated_actor()

    sess = db.session
    target_user = _resolve_user(user_id, session=sess)
    if target_user is None:
        raise ResourceNotFoundError(f"User '{user_id}' not found.")

    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action", "")).strip().lower()
    role_code = str(payload.get("role", "")).strip().upper()
    reason = payload.get("reason")

    if action not in ("assign", "remove"):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Action must be 'assign' or 'remove'.",
                    }
                }
            ),
            400,
        )

    try:
        if action == "assign":
            updated_user = assign_role_to_user(
                user_id=target_user.id,
                role_code=role_code,
                assigned_by_user_id=actor.id,
                reason=reason,
                session=sess,
            )
        else:
            updated_user = remove_role_from_user(
                user_id=target_user.id,
                role_code=role_code,
                removed_by_user_id=actor.id,
                reason=reason,
                session=sess,
            )
        sess.commit()
    except InvalidRoleAssignmentError as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "INVALID_ROLE_ASSIGNMENT",
                        "message": str(exc),
                    }
                }
            ),
            400,
        )

    return (
        jsonify(
            {
                "user_id": str(updated_user.public_id),
                "roles": sorted(updated_user.role_codes),
                "auth_version": updated_user.auth_version,
            }
        ),
        200,
    )


@admin_bp.route("/courses/pending", methods=["GET"])
@admin_required
def list_pending_courses() -> tuple[Response, int] | Response:
    """List all courses currently submitted for review."""
    require_authenticated_actor()

    sess = db.session
    pending_courses = (
        sess.query(Course)
        .filter(
            Course.status == "SUBMITTED_FOR_REVIEW",
            Course.deleted_at.is_(None),
        )
        .order_by(Course.created_at.desc())
        .all()
    )

    data = {
        "pending_count": len(pending_courses),
        "courses": [_serialize_course(c) for c in pending_courses],
    }
    return jsonify(data), 200


@admin_bp.route("/courses/<course_id>/review", methods=["POST"])
@admin_required
def review_course(course_id: str) -> tuple[Response, int] | Response:
    """Approve or reject a submitted course (Admin only)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    action = str(payload.get("action", "")).strip().lower()
    reason = payload.get("reason")

    if action not in ("approve", "reject"):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Action must be 'approve' or 'reject'.",
                    }
                }
            ),
            400,
        )

    target_status = "APPROVED" if action == "approve" else "DRAFT"
    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status=target_status,
        reason=reason,
    )
    db.session.commit()
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/reassign", methods=["POST"])
@admin_required
def reassign_course(course_id: str) -> tuple[Response, int] | Response:
    """Reassign course instructor ownership (Admin only)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    new_instructor_id = payload.get("new_instructor_id")
    reason = payload.get("reason")

    course = reassign_course_owner(
        admin_actor=actor,
        course_id=course_id,
        new_instructor_id=new_instructor_id,
        reason=reason,
    )
    db.session.commit()
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/publish", methods=["POST"])
@admin_required
def publish_course(course_id: str) -> tuple[Response, int] | Response:
    """Publish an approved course (Admin only)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="PUBLISHED",
        reason=reason,
    )
    db.session.commit()
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/trash", methods=["POST", "DELETE"])
@admin_required
def trash_course_route(course_id: str) -> tuple[Response, int] | Response:
    """Soft-delete a course to TRASH (Admin)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    course = trash_course(actor=actor, course_id=course_id, reason=reason)
    db.session.commit()
    return jsonify(_serialize_course(course)), 200


@admin_bp.route("/courses/<course_id>/restore", methods=["POST"])
@admin_required
def restore_course(course_id: str) -> tuple[Response, int] | Response:
    """Restore a course from TRASH back to ARCHIVED (Admin only)."""
    actor = require_authenticated_actor()

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    reason = payload.get("reason")

    course = change_course_status(
        actor=actor,
        course_id=course_id,
        new_status="ARCHIVED",
        reason=reason,
    )
    db.session.commit()
    return jsonify(_serialize_course(course)), 200
