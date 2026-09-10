"""API blueprint for DOCX/PDF assessment and question import per 09_FILE_IMPORT_API.md."""

from __future__ import annotations

from flask import Blueprint

api_import_bp: Blueprint = Blueprint("api_imports", __name__, url_prefix="/api/imports")

from pwd301.blueprints.api_import import routes as _routes  # noqa: E402, F401
