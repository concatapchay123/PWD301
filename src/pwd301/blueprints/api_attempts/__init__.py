"""API blueprint for Student Assessment Attempts & Delivery per 08_ATTEMPT_API.md."""

from __future__ import annotations

from flask import Blueprint

api_attempt_bp: Blueprint = Blueprint("api_attempts", __name__)

from pwd301.blueprints.api_attempts import routes as _routes  # noqa: E402, F401
