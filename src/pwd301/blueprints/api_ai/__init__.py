"""API blueprint for AI, Gemini integration, and Course Recommendations per 10_AI_API.md."""

from __future__ import annotations

from flask import Blueprint

api_ai_bp: Blueprint = Blueprint("api_ai", __name__, url_prefix="/api/ai")

from pwd301.blueprints.api_ai import routes as _routes  # noqa: E402, F401
