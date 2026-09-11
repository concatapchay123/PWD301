"""REST API blueprint for System Administration."""

from __future__ import annotations

from flask import Blueprint

api_admin_bp: Blueprint = Blueprint("api_admin", __name__, url_prefix="/api/admin")

from pwd301.blueprints.api_admin import routes as _routes  # noqa: E402, F401
