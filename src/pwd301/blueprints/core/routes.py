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
    """Informative root endpoint confirming application foundation is operational."""
    # If the client requests HTML (e.g. standard browser), return the canonical course catalog
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    if best == "text/html" and not request.is_json:
        # Query published courses strictly from the database
        stmt = (
            sa.select(Course)
            .where(Course.status == "PUBLISHED", Course.deleted_at.is_(None))
            .order_by(Course.created_at.desc())
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
