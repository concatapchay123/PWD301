"""API blueprint for notifications and preferences per 11_NOTIFICATION_API.md."""

from __future__ import annotations

from flask import Blueprint

api_notification_bp: Blueprint = Blueprint(
    "api_notifications", __name__, url_prefix="/api/notifications"
)

from pwd301.blueprints.api_notifications import routes as _routes  # noqa: E402, F401
