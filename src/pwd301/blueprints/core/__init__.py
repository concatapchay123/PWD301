"""Core blueprint containing root and health check endpoints."""

from __future__ import annotations

from flask import Blueprint

core_bp: Blueprint = Blueprint("core", __name__)

from pwd301.blueprints.core import routes as _routes  # noqa: E402, F401
