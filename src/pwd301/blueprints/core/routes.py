"""Core route handlers for health check and root endpoints."""

from __future__ import annotations

from flask import Response, current_app, jsonify, make_response, request

import pwd301
from pwd301.blueprints.core import core_bp


@core_bp.route("/health", methods=["GET"])
def health() -> tuple[Response, int]:
    """Health check endpoint for container probes and monitoring."""
    return (
        jsonify(
            {
                "status": "ok",
                "env": current_app.config.get("ENV", "unknown"),
                "version": pwd301.__version__,
            }
        ),
        200,
    )


@core_bp.route("/", methods=["GET"])
def index() -> Response:
    """Informative root endpoint confirming application foundation is operational."""
    # If the client requests HTML (e.g. standard browser), return a minimal safe page
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    if best == "text/html" and not request.is_json:
        response = make_response(
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '  <meta charset="utf-8">\n'
            "  <title>PWD301 Online Course Management Platform</title>\n"
            "</head>\n"
            "<body>\n"
            "  <h1>PWD301 Online Course Management Platform</h1>\n"
            "  <p>Platform bootstrap foundation is active.</p>\n"
            "</body>\n"
            "</html>\n"
        )
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    return jsonify(
        {
            "name": "PWD301 Online Course Management Platform",
            "status": "running",
            "version": pwd301.__version__,
        }
    )
