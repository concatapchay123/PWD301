"""REST API routes for notifications and preferences per 11_NOTIFICATION_API.md."""

from __future__ import annotations

from typing import Any

from flask import Response, jsonify, request

from pwd301.blueprints.api_notifications import api_notification_bp
from pwd301.extensions import db
from pwd301.services.authorization_service import (
    admin_required,
    require_authenticated_actor,
)
from pwd301.services.email_service import retry_failed_emails
from pwd301.services.exceptions import ForbiddenError, ValidationError
from pwd301.services.jwt_auth_service import jwt_required
from pwd301.services.notification_service import (
    broadcast_system_notification,
    dismiss_notification,
    get_unread_count,
    get_user_preferences,
    list_user_notifications,
    mark_all_as_read,
    mark_notification_as_read,
    update_user_preferences,
)

_NOTIFICATION_TARGET_ROLES = frozenset({"STUDENT", "INSTRUCTOR", "ADMIN"})


def _normalize_notification_target_role(actor: Any, value: Any) -> str | None:
    """Validate a role filter against the authenticated actor's active roles."""
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValidationError("target_role must be a string.")

    normalized = value.strip().upper()
    if normalized not in _NOTIFICATION_TARGET_ROLES:
        allowed = ", ".join(sorted(_NOTIFICATION_TARGET_ROLES))
        raise ValidationError(f"target_role must be one of: {allowed}.")
    if not actor.has_role(normalized):
        raise ValidationError("target_role is not assigned to the authenticated account.")
    return normalized


@api_notification_bp.route("", methods=["GET"])
@jwt_required
def list_notifications_api() -> tuple[Response, int] | Response:
    """List paginated notifications for authenticated actor."""
    actor = require_authenticated_actor()

    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(request.args.get("per_page", 20))
    except (ValueError, TypeError):
        per_page = 20

    status = request.args.get("status")
    unread_only_arg = request.args.get("unread_only", "").strip().lower()
    unread_only = unread_only_arg in ("true", "1", "yes")
    category = request.args.get("category")
    target_role = _normalize_notification_target_role(
        actor, request.args.get("role") or request.args.get("target_role")
    )

    items, total = list_user_notifications(
        actor=actor,
        target_role=target_role,
        status=status,
        unread_only=unread_only,
        category=category,
        page=page,
        per_page=per_page,
        session=db.session,
    )
    unread = get_unread_count(actor=actor, target_role=target_role, session=db.session)

    response_data = {
        "items": items,
        "total": total,
        "unread_count": unread,
        "page": max(1, page),
        "per_page": min(max(1, per_page), 100),
    }
    return jsonify({"success": True, "data": response_data, **response_data}), 200


@api_notification_bp.route("/unread-count", methods=["GET"])
@jwt_required
def unread_count_api() -> tuple[Response, int] | Response:
    """Get fast count of unread notifications for badge polling."""
    actor = require_authenticated_actor()
    target_role = _normalize_notification_target_role(
        actor, request.args.get("role") or request.args.get("target_role")
    )
    count = get_unread_count(actor=actor, target_role=target_role, session=db.session)
    response_data = {"unread_count": count}
    return jsonify({"success": True, "data": response_data, **response_data}), 200


@api_notification_bp.route("/<notification_id>/read", methods=["PATCH", "POST"])
@jwt_required
def mark_read_api(notification_id: str) -> tuple[Response, int] | Response:
    """Mark a specific notification as read."""
    actor = require_authenticated_actor()
    result = mark_notification_as_read(
        actor=actor,
        notification_id=notification_id,
        session=db.session,
    )
    return jsonify({"success": True, "data": result, **result}), 200


@api_notification_bp.route("/mark-all-read", methods=["POST"])
@jwt_required
def mark_all_read_api() -> tuple[Response, int] | Response:
    """Mark all unread notifications of the current actor as read."""
    actor = require_authenticated_actor()
    data = request.get_json(silent=True)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValidationError("Notification payload must be a JSON object.")
    category = data.get("category") or request.args.get("category")
    target_role = _normalize_notification_target_role(
        actor,
        data.get("role")
        or data.get("target_role")
        or request.args.get("role")
        or request.args.get("target_role"),
    )

    count = mark_all_as_read(
        actor=actor,
        category=category,
        target_role=target_role,
        session=db.session,
    )
    response_data = {"marked_count": count}
    return jsonify({"success": True, "data": response_data, **response_data}), 200


@api_notification_bp.route("/<notification_id>/dismiss", methods=["PATCH", "POST"])
@api_notification_bp.route("/<notification_id>", methods=["DELETE"])
@jwt_required
def dismiss_notification_api(notification_id: str) -> tuple[Response, int] | Response:
    """Dismiss or delete an in-app notification."""
    actor = require_authenticated_actor()
    result = dismiss_notification(
        actor=actor,
        notification_id=notification_id,
        session=db.session,
    )
    return jsonify({"success": True, "data": result, **result}), 200


@api_notification_bp.route("/preferences", methods=["GET"])
@jwt_required
def get_preferences_api() -> tuple[Response, int] | Response:
    """Get notification preferences matrix for authenticated actor."""
    actor = require_authenticated_actor()
    prefs = get_user_preferences(actor=actor, session=db.session)
    response_data = {"preferences": prefs}
    return jsonify({"success": True, "data": response_data, **response_data}), 200


@api_notification_bp.route("/preferences", methods=["PUT", "PATCH"])
@jwt_required
def update_preferences_api() -> tuple[Response, int] | Response:
    """Update notification preferences, rejecting attempts to disable mandatory security alerts."""
    actor = require_authenticated_actor()
    data: dict[str, Any] | list[dict[str, Any]] | None = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    if not data or not isinstance(data, dict):
        raise ValidationError("Preferences payload is required.")

    updated_prefs = update_user_preferences(
        actor=actor,
        preferences_payload=data,
        session=db.session,
    )
    response_data = {"preferences": updated_prefs}
    return jsonify({"success": True, "data": response_data, **response_data}), 200


@api_notification_bp.route("/broadcast", methods=["POST"])
@jwt_required
@admin_required
def broadcast_notification_api() -> tuple[Response, int] | Response:
    """Admin-only: Broadcast a system notification to all or role-targeted users."""
    actor = require_authenticated_actor()
    if not actor.is_admin:
        raise ForbiddenError("Only administrators can broadcast notifications.")

    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    if not data:
        data = {}
    if not isinstance(data, dict):
        raise ValidationError("Notification payload must be a JSON object.")
    title = data.get("title")
    body = data.get("body")
    target_role = data.get("target_role")
    category = data.get("category", "SYSTEM")

    if not title:
        raise ValidationError("Field 'title' is required.")
    if not body:
        raise ValidationError("Field 'body' is required.")

    count, idempotent_replay = broadcast_system_notification(
        actor=actor,
        title=title,
        body=body,
        target_role=target_role,
        category=category,
        idempotency_key=request.headers.get("X-Idempotency-Key"),
        session=db.session,
    )
    response_data = {"broadcasted_count": count, "idempotent_replay": idempotent_replay}
    return jsonify({"success": True, "data": response_data, **response_data}), 200


@api_notification_bp.route("/emails/retry-failed", methods=["POST"])
@jwt_required
@admin_required
def retry_failed_emails_api() -> tuple[Response, int] | Response:
    """Admin-only: Trigger retrying of failed email deliveries."""
    actor = require_authenticated_actor()
    if not actor.is_admin:
        raise ForbiddenError("Only administrators can retry failed emails.")

    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    if not data:
        data = {}
    if not isinstance(data, dict):
        raise ValidationError("Retry payload must be a JSON object.")
    try:
        max_emails = int(data.get("max_emails", 50))
    except (ValueError, TypeError):
        max_emails = 50

    count = retry_failed_emails(
        actor=actor,
        max_emails=max_emails,
        session=db.session,
    )
    response_data = {"retried_count": count}
    return jsonify({"success": True, "data": response_data, **response_data}), 200
