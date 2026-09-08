"""API blueprint for Lesson endpoints per 04_COURSE_API.md and 05_ENROLLMENT_PROGRESS_API.md."""

from __future__ import annotations

from flask import Blueprint

api_lesson_bp: Blueprint = Blueprint("api_lessons", __name__, url_prefix="/api/lessons")

from pwd301.blueprints.api_lessons import routes as _routes  # noqa: E402, F401
