"""Frontend blueprint for serving the PWD301 LMS Web SPA and UI assets."""

from __future__ import annotations

from flask import Blueprint

frontend_bp: Blueprint = Blueprint(
    "frontend",
    __name__,
)

from pwd301.blueprints.frontend import routes  # noqa: E402, F401
