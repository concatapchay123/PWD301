"""PWD301 application package.

Provides the Flask application factory, extension registration, centralized
error handling, and blueprint registration.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from typing import Any

from dotenv import load_dotenv
from flask import (
    Flask,
    Response,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

import pwd301.models  # noqa: F401
from pwd301.blueprints.admin import admin_bp
from pwd301.blueprints.api_auth import api_auth_bp
from pwd301.blueprints.api_courses import api_course_bp
from pwd301.blueprints.auth import auth_bp
from pwd301.blueprints.core import core_bp
from pwd301.blueprints.instructor import instructor_bp
from pwd301.blueprints.student import student_bp
from pwd301.cli import register_cli_commands
from pwd301.config import config_by_name
from pwd301.extensions import csrf, db, login_manager, migrate
from pwd301.models.identity import AnonymousUser
from pwd301.services.exceptions import (
    CourseAlreadyExistsError,
    CourseDependencyError,
    CourseStateViolationError,
    CourseValidationError,
    ForbiddenError,
    ResourceNotFoundError,
)

__version__ = "0.0.0"


class UTCFormatter(logging.Formatter):
    """Logging formatter converting timestamps to UTC."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        ct = time.gmtime(record.created)
        if datefmt:
            return time.strftime(datefmt, ct)
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", ct)


def _configure_logging(app: Flask) -> None:
    """Configure structured console logging with UTC timestamps."""
    log_level = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    app.logger.setLevel(numeric_level)

    if not app.logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = UTCFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)


def _is_api_or_json_request() -> bool:
    """Determine whether the incoming request expects a JSON/API response."""
    if request.path.startswith("/api/"):
        return True
    if request.is_json:
        return True
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json"


def _format_error_response(
    code: str,
    message: str,
    status_code: int,
    field_errors: dict[str, Any] | None = None,
) -> Response | tuple[Response, int]:
    """Format an error response adhering to the PWD301 error model."""
    correlation_id = getattr(g, "correlation_id", uuid.uuid4().hex)

    if _is_api_or_json_request():
        return (
            jsonify(
                {
                    "error": {
                        "code": code,
                        "message": message,
                        "field_errors": field_errors or {},
                        "correlation_id": correlation_id,
                    }
                }
            ),
            status_code,
        )

    if status_code == 403:
        try:
            rendered = render_template(
                "errors/403.html",
                status_code=403,
                code=code,
                message=message,
                correlation_id=correlation_id,
            )
            response = make_response(rendered, 403)
            response.headers["Content-Type"] = "text/html; charset=utf-8"
            return response
        except Exception:
            pass

    html_content = (
        f"<!DOCTYPE html>\n"
        f'<html lang="en">\n'
        f'<head><meta charset="utf-8"><title>{status_code} {code}</title></head>\n'
        f"<body>\n"
        f"  <h1>{status_code} {code}</h1>\n"
        f"  <p>{message}</p>\n"
        f"  <small>Correlation ID: {correlation_id}</small>\n"
        f"</body>\n"
        f"</html>\n"
    )
    response = make_response(html_content, status_code)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


def _register_error_handlers(app: Flask) -> None:
    """Register centralized error handlers conforming to the API error model."""

    @app.errorhandler(400)
    def bad_request_error(error: HTTPException | Exception) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="VALIDATION_ERROR",
            message=getattr(error, "description", "Bad request syntax or parameters."),
            status_code=400,
        )

    @app.errorhandler(403)
    def forbidden_error(error: HTTPException | Exception) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="FORBIDDEN",
            message=getattr(error, "description", "Access denied: insufficient permissions."),
            status_code=403,
        )

    @app.errorhandler(ForbiddenError)
    def domain_forbidden_error(error: ForbiddenError) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="FORBIDDEN",
            message=str(error),
            status_code=403,
        )

    @app.errorhandler(404)
    def not_found_error(error: HTTPException | Exception) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="RESOURCE_NOT_FOUND",
            message=getattr(error, "description", "The requested resource was not found."),
            status_code=404,
        )

    @app.errorhandler(ResourceNotFoundError)
    def domain_not_found_error(error: ResourceNotFoundError) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="RESOURCE_NOT_FOUND",
            message=str(error),
            status_code=404,
        )

    @app.errorhandler(CourseAlreadyExistsError)
    def domain_course_already_exists_error(
        error: CourseAlreadyExistsError,
    ) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="CONFLICT",
            message=str(error),
            status_code=409,
        )

    @app.errorhandler(CourseStateViolationError)
    def domain_course_state_violation_error(
        error: CourseStateViolationError,
    ) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="STATE_VIOLATION",
            message=str(error),
            status_code=409,
        )

    @app.errorhandler(CourseDependencyError)
    def domain_course_dependency_error(
        error: CourseDependencyError,
    ) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="PREREQUISITE_DEPENDENCY",
            message=str(error),
            status_code=409,
        )

    @app.errorhandler(CourseValidationError)
    def domain_course_validation_error(
        error: CourseValidationError,
    ) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="VALIDATION_ERROR",
            message=str(error),
            status_code=400,
        )

    @app.errorhandler(405)
    def method_not_allowed_error(
        error: HTTPException | Exception,
    ) -> Response | tuple[Response, int]:
        msg = getattr(error, "description", "The method is not allowed for the requested URL.")
        return _format_error_response(
            code="METHOD_NOT_ALLOWED",
            message=msg,
            status_code=405,
        )

    @app.errorhandler(CSRFError)
    def csrf_error(error: CSRFError) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="CSRF_ERROR",
            message=getattr(error, "description", "CSRF token missing or invalid."),
            status_code=400,
        )

    @app.errorhandler(500)
    def internal_error(error: HTTPException | Exception) -> Response | tuple[Response, int]:
        app.logger.error("Internal Server Error: %s", error, exc_info=True)
        return _format_error_response(
            code="INTERNAL_ERROR",
            message="An internal server error occurred. Please contact support.",
            status_code=500,
        )

    @app.errorhandler(Exception)
    def unhandled_exception(error: Exception) -> Response | tuple[Response, int]:
        if isinstance(error, HTTPException):
            code_name = error.name.upper().replace(" ", "_")
            return _format_error_response(
                code=code_name,
                message=error.description or "An error occurred.",
                status_code=error.code or 500,
            )
        app.logger.error("Unhandled Exception: %s", error, exc_info=True)
        return _format_error_response(
            code="INTERNAL_ERROR",
            message="An internal server error occurred. Please contact support.",
            status_code=500,
        )


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure an instance of the Flask application.

    Args:
        config_name: The name of the configuration ('development', 'testing', 'production').
                     If None, resolves from the APP_ENV environment variable.
    """
    load_dotenv()

    if config_name is None:
        config_name = os.environ.get("APP_ENV", "development").lower()

    if config_name not in config_by_name:
        raise ValueError(
            f"Unknown configuration '{config_name}'. Available: {list(config_by_name.keys())}"
        )

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.anonymous_user = AnonymousUser

    # Template context processor for auth & role helpers
    @app.context_processor
    def inject_auth_helpers() -> dict[str, Any]:
        actor = None
        if hasattr(g, "current_user") and g.current_user is not None:
            actor = g.current_user
        elif current_user and current_user.is_authenticated:
            actor = current_user

        def has_role(role_code: str) -> bool:
            if actor is None:
                return False
            return actor.has_role(role_code)

        def has_any_role(*role_codes: str) -> bool:
            if actor is None:
                return False
            return actor.has_any_role(*role_codes)

        def is_admin() -> bool:
            return actor.is_admin if actor else False

        def is_instructor() -> bool:
            return actor.is_instructor if actor else False

        def is_student() -> bool:
            return actor.is_student if actor else False

        def check_can_manage_course(course: Any) -> bool:
            from pwd301.services.authorization_service import can_manage_course

            return can_manage_course(actor, course)

        roles_list = sorted(actor.role_codes) if actor else []

        return {
            "has_role": has_role,
            "has_any_role": has_any_role,
            "is_admin": is_admin,
            "is_instructor": is_instructor,
            "is_student": is_student,
            "can_manage_course": check_can_manage_course,
            "user_roles": roles_list,
        }

    @login_manager.user_loader
    def load_user(user_id: str) -> Any:
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None
        from pwd301.models.identity import User
        from pwd301.services.session_auth_service import validate_auth_session

        user = db.session.get(User, uid)
        if user is None or not user.is_active:
            return None

        # Verify session auth_version against current user record
        session_auth_version = session.get("auth_version")
        if session_auth_version is not None and session_auth_version != user.auth_version:
            return None

        # If an auth_session_key exists in session, validate against database record
        raw_key = session.get("auth_session_key")
        if raw_key:
            auth_sess = validate_auth_session(raw_key, session=db.session)
            if auth_sess is None:
                return None

        return user

    @login_manager.unauthorized_handler
    def unauthorized() -> Any:
        if _is_api_or_json_request():
            return _format_error_response(
                code="UNAUTHORIZED",
                message="Authentication required to access this resource.",
                status_code=401,
            )
        return redirect(url_for("auth.login", next=request.url))

    # Logging setup
    _configure_logging(app)

    # Correlation ID middleware
    @app.before_request
    def before_request() -> None:
        g.correlation_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
        g.pop("_login_user", None)

    @app.after_request
    def after_request(response: Response) -> Response:
        response.headers["X-Correlation-ID"] = getattr(g, "correlation_id", "")
        return response

    # Centralized error handlers
    _register_error_handlers(app)

    # Register blueprints
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(instructor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_course_bp)

    # Exempt REST API blueprints from CSRF validation (API clients use Bearer JWT)
    csrf.exempt(api_auth_bp)
    csrf.exempt(api_course_bp)

    # Register CLI commands
    register_cli_commands(app)

    return app
