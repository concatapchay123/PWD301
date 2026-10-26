"""API Payments blueprint initialization."""

from flask import Blueprint

api_payments_bp = Blueprint("api_payments", __name__, url_prefix="/api/payments")

from backend.blueprints.api_payments import routes  # noqa: E402, F401
