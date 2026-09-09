"""API blueprint for Assessment endpoints per 07_ASSESSMENT_API.md."""

from __future__ import annotations

from flask import Blueprint

api_assessment_bp: Blueprint = Blueprint("api_assessments", __name__, url_prefix="/api/assessments")

from pwd301.blueprints.api_assessments import routes as _routes  # noqa: E402, F401
