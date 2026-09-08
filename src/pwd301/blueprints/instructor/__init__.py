"""Instructor portal blueprint."""

from __future__ import annotations

from flask import Blueprint

instructor_bp = Blueprint("instructor", __name__, url_prefix="/instructor")

from pwd301.blueprints.instructor import routes  # noqa: E402, F401
