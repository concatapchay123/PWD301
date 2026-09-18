"""REST API routes for JWT authentication, refresh, revocation, and introspection."""

from __future__ import annotations

from typing import Any

from flask import Response, g, jsonify, request

from pwd301.blueprints.api_auth import api_auth_bp
from pwd301.services.exceptions import (
    AccountNotActiveError,
    AuthVersionMismatchError,
    JwtTokenExpiredError,
    JwtTokenInvalidError,
    JwtTokenRevokedError,
)
from pwd301.services.jwt_auth_service import (
    create_token_pair,
    jwt_required,
    refresh_tokens,
    revoke_token,
)
from pwd301.services.rate_limit_service import (
    clear_login_attempts,
    is_login_locked,
    record_failed_login,
)
from pwd301.services.user_service import get_user_by_email, verify_password


@api_auth_bp.route("/token", methods=["POST"])
@api_auth_bp.route("/login", methods=["POST"])
def login_for_token() -> tuple[Response, int]:
    """Issue JWT access and refresh token pair for valid credentials."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))

    if not email or not password:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Both email and password are required.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            400,
        )

    remote_ip = request.remote_addr or ""
    is_locked, retry_after = is_login_locked(remote_ip, email)
    if is_locked:
        resp = jsonify(
            {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": (
                        f"Too many failed login attempts. "
                        f"Please try again after {retry_after} seconds."
                    ),
                    "correlation_id": getattr(g, "correlation_id", ""),
                }
            }
        )
        resp.headers["Retry-After"] = str(retry_after)
        return resp, 429

    user = get_user_by_email(email)
    if not verify_password(user, password) or user is None:
        record_failed_login(remote_ip, email)
        return (
            jsonify(
                {
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            401,
        )

    clear_login_attempts(remote_ip, email)

    if not user.is_active:
        return (
            jsonify(
                {
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": "User account is suspended or inactive.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            403,
        )

    tokens = create_token_pair(user)
    return jsonify(tokens), 200


@api_auth_bp.route("/refresh", methods=["POST"])
def refresh() -> tuple[Response, int]:
    """Rotate a refresh token and issue a new token pair."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    raw_refresh = str(data.get("refresh_token", "")).strip()

    if not raw_refresh:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "refresh_token is required.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            400,
        )

    try:
        new_tokens = refresh_tokens(raw_refresh)
    except JwtTokenExpiredError as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "TOKEN_EXPIRED",
                        "message": str(exc),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            401,
        )
    except JwtTokenRevokedError as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "TOKEN_REVOKED",
                        "message": str(exc),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            401,
        )
    except AuthVersionMismatchError as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "AUTH_VERSION_MISMATCH",
                        "message": str(exc),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            401,
        )
    except AccountNotActiveError as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "ACCOUNT_INACTIVE",
                        "message": str(exc),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            403,
        )
    except JwtTokenInvalidError as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": str(exc),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            401,
        )

    return jsonify(new_tokens), 200


@api_auth_bp.route("/revoke", methods=["POST"])
def revoke() -> tuple[Response, int]:
    """Revoke a token grant by token string or Bearer header."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    token = str(data.get("token", "")).strip()

    if not token:
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": (
                            "Token must be provided in request body or Authorization header."
                        ),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            400,
        )

    revoked = revoke_token(token)
    message = (
        "Token grant revoked successfully." if revoked else "Token not found or already revoked."
    )
    return (
        jsonify(
            {
                "status": "ok",
                "revoked": revoked,
                "message": message,
            }
        ),
        200,
    )


@api_auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user() -> tuple[Response, int]:
    """Return profile details for the authenticated API user."""
    user = g.current_user
    return (
        jsonify(
            {
                "user": {
                    "public_id": str(user.public_id),
                    "email": user.email,
                    "display_name": user.display_name,
                    "status": user.status,
                    "auth_version": user.auth_version,
                    "roles": [r.code for r in user.roles],
                }
            }
        ),
        200,
    )


@api_auth_bp.route("/logout", methods=["POST"])
def logout_api() -> tuple[Response, int]:
    """Revoke current API authentication grant (JWT Bearer or body token)."""
    data: dict[str, Any] = request.get_json(silent=True) or {}
    token = str(data.get("token", "")).strip() or str(data.get("refresh_token", "")).strip()

    if not token:
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        return (
            jsonify(
                {
                    "error": {
                        "code": "AUTHENTICATION_REQUIRED",
                        "message": "Authentication token required for logout.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            401,
        )

    revoke_token(token)
    return (
        jsonify(
            {
                "status": "ok",
                "message": "Logged out successfully.",
            }
        ),
        200,
    )


@api_auth_bp.route("/email-change", methods=["POST"])
@jwt_required
def request_email_change_api() -> tuple[Response, int]:
    """Initiate an email change request and issue a verification token (JWT required)."""
    from pwd301.extensions import db
    from pwd301.models.identity import User
    from pwd301.services.auth_token_service import SecurityTokenPurpose, create_security_token
    from pwd301.services.email_service import validate_email_syntax

    user = g.current_user
    data: dict[str, Any] = request.get_json(silent=True) or {}
    new_email = str(data.get("new_email", "")).strip().lower()

    if not new_email:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "new_email is required.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            400,
        )

    try:
        validate_email_syntax(new_email)
    except Exception as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(exc),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            400,
        )

    if new_email == user.email_normalized or new_email == user.email.lower():
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "New email must be different from current email.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            400,
        )

    existing = db.session.query(User).filter(User.email_normalized == new_email).first()
    if existing is not None and existing.id != user.id:
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": f"Email '{new_email}' is already in use.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            409,
        )

    token_record, raw_token = create_security_token(
        user_id=user.id,
        purpose=SecurityTokenPurpose.EMAIL_CHANGE,
        pending_email=new_email,
        session=db.session,
    )

    user.pending_email = new_email
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Verification token issued for email change.",
                "pending_email": new_email,
                "token": raw_token,
            }
        ),
        202,
    )


@api_auth_bp.route("/email-change/verify", methods=["POST"])
def verify_email_change_api() -> tuple[Response, int]:
    """Verify email change token and update user email address."""
    from pwd301.extensions import db
    from pwd301.services.auth_token_service import apply_email_change_with_token
    from pwd301.services.exceptions import (
        InvalidTokenError,
        TokenAlreadyConsumedError,
        TokenExpiredError,
        UserAlreadyExistsError,
    )

    data: dict[str, Any] = request.get_json(silent=True) or {}
    token = str(data.get("token", "")).strip()

    if not token:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Verification token is required.",
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            400,
        )

    try:
        updated_user = apply_email_change_with_token(token, session=db.session)
        updated_user.pending_email = None
        db.session.commit()
    except (TokenExpiredError, InvalidTokenError, TokenAlreadyConsumedError) as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "TOKEN_INVALID",
                        "message": str(exc),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            400,
        )
    except UserAlreadyExistsError as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": str(exc),
                        "correlation_id": getattr(g, "correlation_id", ""),
                    }
                }
            ),
            409,
        )

    return (
        jsonify(
            {
                "message": "Email changed successfully.",
                "email": updated_user.email,
                "auth_version": updated_user.auth_version,
            }
        ),
        200,
    )
