"""Student portal blueprint."""

from __future__ import annotations

from flask import Blueprint

student_bp = Blueprint("student", __name__, url_prefix="/student")

from pwd301.blueprints.student import routes  # noqa: E402, F401
