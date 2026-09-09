"""API blueprint for Question Bank endpoints per 06_QUESTION_BANK_API.md."""

from __future__ import annotations

from flask import Blueprint

api_question_bp: Blueprint = Blueprint("api_questions", __name__, url_prefix="/api/questions")

from pwd301.blueprints.api_questions import routes as _routes  # noqa: E402, F401
