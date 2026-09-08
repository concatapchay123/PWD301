"""Admin portal blueprint."""

from __future__ import annotations

from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from pwd301.blueprints.admin import routes  # noqa: E402, F401
