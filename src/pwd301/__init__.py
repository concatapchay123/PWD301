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
from pwd301.blueprints.api_assessments import api_assessment_bp
from pwd301.blueprints.api_attempts import api_attempt_bp
from pwd301.blueprints.api_auth import api_auth_bp
from pwd301.blueprints.api_courses import api_course_bp
from pwd301.blueprints.api_files import api_file_bp
from pwd301.blueprints.api_import import api_import_bp
from pwd301.blueprints.api_lessons import api_lesson_bp
from pwd301.blueprints.api_notifications import api_notification_bp
from pwd301.blueprints.api_questions import api_question_bp
from pwd301.blueprints.api_student import api_student_bp
from pwd301.blueprints.auth import auth_bp
from pwd301.blueprints.core import core_bp
from pwd301.blueprints.instructor import instructor_bp
from pwd301.blueprints.student import student_bp
from pwd301.cli import register_cli_commands
from pwd301.config import config_by_name
from pwd301.extensions import csrf, db, login_manager, migrate
from pwd301.models.identity import AnonymousUser
from pwd301.services.exceptions import (
    ActiveAttemptExistsError,
    AssessmentClosedError,
    AssessmentError,
    AssessmentLockedError,
    AssessmentNotFoundError,
    AssessmentNotOpenError,
    AssessmentSectionNotFoundError,
    AssessmentStateViolationError,
    AssessmentValidationError,
    AttemptAlreadySubmittedError,
    AttemptError,
    AttemptExpiredError,
    AttemptLeaseConflictError,
    AttemptLeaseError,
    AttemptLeaseExpiredError,
    AttemptLimitExceededError,
    AttemptNotFoundError,
    AttemptNotSubmitedError,
    AttemptNotSubmittedError,
    AttemptValidationError,
    BlueprintValidationError,
    CompletionRuleError,
    CompletionRuleNotFoundError,
    CompletionRuleValidationError,
    ConflictError,
    CourseAlreadyExistsError,
    CourseDependencyError,
    CourseNotAvailableError,
    CourseStateViolationError,
    CourseValidationError,
    DocumentImportError,
    DocumentImportJobNotFoundError,
    DocumentImportStateViolationError,
    DocumentParsingError,
    EmailDeliveryError,
    EmailDeliveryNotFoundError,
    EmailRateLimitExceededError,
    EnrollmentCapacityExceededError,
    EnrollmentError,
    EnrollmentNotFoundError,
    EnrollmentPrerequisiteError,
    EnrollmentStateViolationError,
    FileAccessDeniedError,
    FileAssetNotFoundError,
    FileError,
    FileInfectedError,
    FileSecurityQuarantineError,
    FileSizeLimitExceededError,
    FileStorageError,
    FileValidationError,
    ForbiddenError,
    GradingError,
    ImportQuestionNotFoundError,
    LessonNotFoundError,
    LessonPositionConflictError,
    LessonProgressError,
    LessonStateViolationError,
    LessonValidationError,
    MandatoryNotificationOptOutError,
    MaxPointsExceededError,
    NotificationError,
    NotificationNotFoundError,
    NotificationPreferenceError,
    PrerequisiteCycleError,
    QuestionBankError,
    QuestionCorrectionError,
    QuestionCorrectionNotFoundError,
    QuestionImmutableError,
    QuestionNotFoundError,
    QuestionRevisionConflictError,
    QuestionRevisionNotFoundError,
    QuestionStateViolationError,
    QuestionValidationError,
    RegradeError,
    RegradeJobNotFoundError,
    ResourceNotFoundError,
    ScoreReleasePolicyError,
    StaleAnswerSequenceError,
    StaleLeaseEpochError,
    SubmissionIdempotencyConflictError,
    UnauthorizedError,
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


DOMAIN_EXCEPTION_HANDLERS: dict[type[Exception], tuple[str, int]] = {
    # 401 Unauthorized
    UnauthorizedError: ("UNAUTHORIZED", 401),
    # 403 Forbidden
    ForbiddenError: ("FORBIDDEN", 403),
    ScoreReleasePolicyError: ("FORBIDDEN", 403),
    FileAccessDeniedError: ("FORBIDDEN", 403),
    FileInfectedError: ("FILE_INFECTED", 403),
    FileSecurityQuarantineError: ("FILE_QUARANTINED", 403),
    # 404 Not Found
    ResourceNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    LessonNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    EnrollmentNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    CompletionRuleNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    QuestionNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    QuestionRevisionNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    AssessmentNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    AssessmentSectionNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    AttemptNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    RegradeJobNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    QuestionCorrectionNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    FileAssetNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    DocumentImportJobNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    ImportQuestionNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    NotificationNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    EmailDeliveryNotFoundError: ("RESOURCE_NOT_FOUND", 404),
    # 409 Conflict & State Violations
    DocumentImportStateViolationError: ("STATE_VIOLATION", 409),
    RegradeError: ("CONFLICT", 409),
    CourseAlreadyExistsError: ("CONFLICT", 409),
    CourseStateViolationError: ("STATE_VIOLATION", 409),
    CourseDependencyError: ("PREREQUISITE_DEPENDENCY", 409),
    LessonPositionConflictError: ("CONFLICT", 409),
    LessonStateViolationError: ("STATE_VIOLATION", 409),
    EnrollmentCapacityExceededError: ("CAPACITY_EXCEEDED", 409),
    EnrollmentPrerequisiteError: ("PREREQUISITE_NOT_MET", 409),
    EnrollmentStateViolationError: ("STATE_VIOLATION", 409),
    PrerequisiteCycleError: ("CYCLE_DETECTED", 409),
    QuestionStateViolationError: ("STATE_VIOLATION", 409),
    QuestionRevisionConflictError: ("CONFLICT", 409),
    QuestionImmutableError: ("STATE_VIOLATION", 409),
    AssessmentStateViolationError: ("STATE_VIOLATION", 409),
    AssessmentLockedError: ("CONFLICT", 409),
    ConflictError: ("CONFLICT", 409),
    AttemptLimitExceededError: ("ATTEMPT_LIMIT", 409),
    ActiveAttemptExistsError: ("CONFLICT", 409),
    AttemptLeaseError: ("LEASE_CONFLICT", 409),
    AttemptLeaseConflictError: ("LEASE_CONFLICT", 409),
    AttemptLeaseExpiredError: ("LEASE_CONFLICT", 409),
    StaleLeaseEpochError: ("STALE_LEASE_EPOCH", 409),
    StaleAnswerSequenceError: ("STALE_ANSWER", 409),
    AttemptExpiredError: ("DEADLINE_EXPIRED", 409),
    AttemptAlreadySubmittedError: ("STATE_VIOLATION", 409),
    AttemptNotSubmittedError: ("STATE_VIOLATION", 409),
    AttemptNotSubmitedError: ("STATE_VIOLATION", 409),
    SubmissionIdempotencyConflictError: ("SUBMISSION_CONFLICT", 409),
    # 400 Bad Request & Validation Errors
    MaxPointsExceededError: ("VALIDATION_ERROR", 400),
    GradingError: ("VALIDATION_ERROR", 400),
    CourseValidationError: ("VALIDATION_ERROR", 400),
    LessonValidationError: ("VALIDATION_ERROR", 400),
    LessonProgressError: ("VALIDATION_ERROR", 400),
    CourseNotAvailableError: ("COURSE_NOT_AVAILABLE", 400),
    EnrollmentError: ("ENROLLMENT_ERROR", 400),
    CompletionRuleValidationError: ("VALIDATION_ERROR", 400),
    CompletionRuleError: ("COMPLETION_RULE_ERROR", 400),
    QuestionValidationError: ("VALIDATION_ERROR", 400),
    QuestionCorrectionError: ("VALIDATION_ERROR", 400),
    QuestionBankError: ("QUESTION_BANK_ERROR", 400),
    AssessmentValidationError: ("VALIDATION_ERROR", 400),
    BlueprintValidationError: ("VALIDATION_ERROR", 400),
    AssessmentError: ("VALIDATION_ERROR", 400),
    AttemptValidationError: ("VALIDATION_ERROR", 400),
    AssessmentNotOpenError: ("NOT_OPEN", 400),
    AssessmentClosedError: ("CLOSED", 400),
    AttemptError: ("VALIDATION_ERROR", 400),
    FileValidationError: ("VALIDATION_ERROR", 400),
    DocumentParsingError: ("PARSING_ERROR", 400),
    DocumentImportError: ("IMPORT_ERROR", 400),
    NotificationPreferenceError: ("VALIDATION_ERROR", 400),
    MandatoryNotificationOptOutError: ("VALIDATION_ERROR", 400),
    NotificationError: ("NOTIFICATION_ERROR", 400),
    # 413 Payload Too Large
    FileSizeLimitExceededError: ("PAYLOAD_TOO_LARGE", 413),
    # 429 Rate Limit Exceeded
    EmailRateLimitExceededError: ("RATE_LIMIT_EXCEEDED", 429),
    # 500 Internal Error
    FileStorageError: ("INTERNAL_ERROR", 500),
    FileError: ("INTERNAL_ERROR", 500),
    EmailDeliveryError: ("EMAIL_DELIVERY_ERROR", 500),
}


def _register_error_handlers(app: Flask) -> None:
    """Register centralized error handlers conforming to the API error model."""

    @app.errorhandler(400)
    def bad_request_error(error: HTTPException | Exception) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="VALIDATION_ERROR",
            message=getattr(error, "description", "Bad request syntax or parameters."),
            status_code=400,
        )

    @app.errorhandler(401)
    def unauthorized_error(error: HTTPException | Exception) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="UNAUTHORIZED",
            message=getattr(
                error, "description", "Authentication required to access this resource."
            ),
            status_code=401,
        )

    @app.errorhandler(403)
    def forbidden_error(error: HTTPException | Exception) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="FORBIDDEN",
            message=getattr(error, "description", "Access denied: insufficient permissions."),
            status_code=403,
        )

    @app.errorhandler(404)
    def not_found_error(error: HTTPException | Exception) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="RESOURCE_NOT_FOUND",
            message=getattr(error, "description", "The requested resource was not found."),
            status_code=404,
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

    @app.errorhandler(413)
    def request_entity_too_large_error(
        error: HTTPException | Exception,
    ) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="PAYLOAD_TOO_LARGE",
            message=getattr(error, "description", "Request payload exceeds maximum allowed size."),
            status_code=413,
        )

    @app.errorhandler(CSRFError)
    def csrf_error(error: CSRFError) -> Response | tuple[Response, int]:
        return _format_error_response(
            code="CSRF_ERROR",
            message=getattr(error, "description", "CSRF token missing or invalid."),
            status_code=400,
        )

    for exc_cls, (code, status) in DOMAIN_EXCEPTION_HANDLERS.items():

        def _make_handler(c: str, s: int):
            def handler(error: Exception) -> Response | tuple[Response, int]:
                return _format_error_response(
                    code=c,
                    message=str(error),
                    status_code=s,
                )

            return handler

        app.errorhandler(exc_cls)(_make_handler(code, status))

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


def create_app(
    config_name: str | None = None,
    config_override: dict[str, Any] | None = None,
) -> Flask:
    """Create and configure an instance of the Flask application.

    Args:
        config_name: The name of the configuration ('development', 'testing', 'production').
                     If None, resolves from the APP_ENV environment variable.
        config_override: Optional dictionary of configuration key-value pairs to override defaults.
    """
    load_dotenv()

    if config_name is None:
        config_name = os.environ.get("APP_ENV", "development").lower()

    if config_name not in config_by_name:
        raise ValueError(
            f"Unknown configuration '{config_name}'. Available: {list(config_by_name.keys())}"
        )

    app = Flask(__name__)
    config_cls = config_by_name[config_name]
    config_obj = config_cls() if isinstance(config_cls, type) else config_cls
    app.config.from_object(config_obj)
    if config_override:
        app.config.update(config_override)

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
        if session_auth_version is None or session_auth_version != user.auth_version:
            return None

        # Validate auth_session_key against database record
        raw_key = session.get("auth_session_key")
        if not raw_key:
            return None
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
    app.register_blueprint(api_auth_bp, url_prefix="/api/auth", name="api_auth_unversioned")
    app.register_blueprint(student_bp)
    app.register_blueprint(instructor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_bp, url_prefix="/api/admin", name="api_admin")
    app.register_blueprint(api_course_bp)
    app.register_blueprint(api_lesson_bp)
    app.register_blueprint(api_question_bp)
    app.register_blueprint(api_student_bp)
    app.register_blueprint(api_assessment_bp)
    app.register_blueprint(api_attempt_bp)
    app.register_blueprint(api_file_bp)
    app.register_blueprint(api_import_bp)
    app.register_blueprint(api_notification_bp)

    # Exempt REST API blueprints from CSRF validation (API clients use Bearer JWT)
    csrf.exempt(api_auth_bp)
    unversioned_auth = app.blueprints.get("api_auth_unversioned")
    if unversioned_auth:
        csrf.exempt(unversioned_auth)
    api_admin = app.blueprints.get("api_admin")
    if api_admin:
        csrf.exempt(api_admin)
    csrf.exempt(api_course_bp)
    csrf.exempt(api_lesson_bp)
    csrf.exempt(api_question_bp)
    csrf.exempt(api_student_bp)
    csrf.exempt(api_assessment_bp)
    csrf.exempt(api_attempt_bp)
    csrf.exempt(api_file_bp)
    csrf.exempt(api_import_bp)
    csrf.exempt(api_notification_bp)

    # Register CLI commands
    register_cli_commands(app)

    return app
