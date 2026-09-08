"""Core route handlers for health check and root endpoints."""

from __future__ import annotations

import sqlalchemy as sa
from flask import Response, current_app, jsonify, make_response, render_template, request

import pwd301
from pwd301.blueprints.core import core_bp
from pwd301.extensions import db
from pwd301.models.course import Course


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
    # If the client requests HTML (e.g. standard browser), return the canonical course catalog
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    if best == "text/html" and not request.is_json:
        # Query published courses strictly from the database
        stmt = (
            sa.select(Course).where(Course.status == "PUBLISHED").order_by(Course.created_at.desc())
        )
        courses = list(db.session.scalars(stmt).all())
        rendered = render_template("public/catalog.html", courses=courses)
        response = make_response(rendered)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    return jsonify(
        {
            "name": "PWD301 Online Course Management Platform",
            "status": "running",
            "version": pwd301.__version__,
        }
    )
