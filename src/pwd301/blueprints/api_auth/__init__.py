"""API Authentication blueprint for JWT issuance, refresh, and revocation."""

from __future__ import annotations

from flask import Blueprint

api_auth_bp: Blueprint = Blueprint("api_auth", __name__, url_prefix="/api/v1/auth")

from pwd301.blueprints.api_auth import routes as _routes  # noqa: E402, F401
