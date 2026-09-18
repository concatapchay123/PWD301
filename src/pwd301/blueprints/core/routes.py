"""Core route handlers for health check and root endpoints."""

from __future__ import annotations

from flask import Response, current_app, jsonify, request

import pwd301
from pwd301.blueprints.core import core_bp
from pwd301.extensions import db


@core_bp.route("/health", methods=["GET"])
def health() -> tuple[Response, int]:
    """Lightweight liveness probe confirming web server process is responsive."""
    return (
        jsonify(
            {
                "status": "ok",
                "probe": "liveness",
                "env": current_app.config.get("ENV", "unknown"),
                "version": pwd301.__version__,
            }
        ),
        200,
    )


@core_bp.route("/health/deep", methods=["GET"])
def health_deep() -> tuple[Response, int]:
    """Deep readiness probe confirming database connectivity and storage health."""
    from pwd301.services.operations_service import check_system_health

    report = check_system_health(include_details=False, session=db.session)
    report["version"] = pwd301.__version__
    report["env"] = current_app.config.get("ENV", "unknown")

    status_code = 200 if report["status"] in ("HEALTHY", "DEGRADED") else 503
    return jsonify(report), status_code


@core_bp.route("/", methods=["GET"])
def index() -> Response:
    """Serve SPA frontend index for browsers, or API info for JSON clients."""
    accept = request.headers.get("Accept", "")
    wants_json = "application/json" in accept and "text/html" not in accept
    if wants_json:
        return jsonify(
            {
                "name": "PWD301 Online Course Management Platform",
                "status": "running",
                "version": pwd301.__version__,
                "web_ui": "/",
                "api_docs": "/api",
            }
        )
    from pwd301.blueprints.frontend.routes import index as frontend_index

    return frontend_index()
