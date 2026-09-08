"""REST API blueprint for student actions per 05_ENROLLMENT_PROGRESS_API.md."""

from __future__ import annotations

from flask import Blueprint

api_student_bp = Blueprint("api_student", __name__, url_prefix="/api/student")

from pwd301.blueprints.api_student import routes  # noqa: E402, F401
