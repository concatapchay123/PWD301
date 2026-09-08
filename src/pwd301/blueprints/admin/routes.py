"""Route handlers for the admin role blueprint."""

from __future__ import annotations

from flask import Response, jsonify, request

from pwd301.blueprints.admin import admin_bp
from pwd301.extensions import db
from pwd301.models.course import Course
from pwd301.models.identity import User
from pwd301.services.authorization_service import (
    _resolve_user,
    admin_required,
    get_authenticated_actor,
)
from pwd301.services.exceptions import (
    InvalidRoleAssignmentError,
    ResourceNotFoundError,
)
from pwd301.services.user_service import assign_role_to_user, remove_role_from_user


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard() -> tuple[Response, int] | Response:
    """Administrator dashboard overview."""
    actor = get_authenticated_actor()
    assert actor is not None

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
    actor = get_authenticated_actor()
    assert actor is not None

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
