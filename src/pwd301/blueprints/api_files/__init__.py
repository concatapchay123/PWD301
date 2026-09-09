"""API blueprint for File storage and asset management per ADR-008 and 09_FILE_IMPORT_API.md."""

from __future__ import annotations

from flask import Blueprint

api_file_bp: Blueprint = Blueprint("api_files", __name__, url_prefix="/api/files")

from pwd301.blueprints.api_files import routes as _routes  # noqa: E402, F401
