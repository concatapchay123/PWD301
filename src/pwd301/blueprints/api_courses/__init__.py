"""API blueprint for Course management endpoints per 04_COURSE_API.md."""

from __future__ import annotations

from flask import Blueprint

api_course_bp: Blueprint = Blueprint("api_courses", __name__, url_prefix="/api/courses")

from pwd301.blueprints.api_courses import routes as _routes  # noqa: E402, F401
