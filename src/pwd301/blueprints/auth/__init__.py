"""Authentication blueprint for Web UI session-based workflows."""

from __future__ import annotations

from flask import Blueprint

auth_bp: Blueprint = Blueprint("auth", __name__, url_prefix="/auth")

from pwd301.blueprints.auth import routes as _routes  # noqa: E402, F401
