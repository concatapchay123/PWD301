"""Services package for PWD301.

Provides business logic services for user lifecycle, authentication tokens,
and domain operations.
"""

from __future__ import annotations

from pwd301.services.auth_token_service import (
    SecurityTokenPurpose,
    apply_email_change_with_token,
    consume_security_token,
    create_security_token,
    hash_token,
    reset_password_with_token,
    verify_email_with_token,
    verify_security_token,
)
from pwd301.services.exceptions import (
    AccountNotActiveError,
    AuthenticationError,
    AuthVersionMismatchError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidPasswordError,
    InvalidTokenError,
    JwtTokenExpiredError,
    JwtTokenInvalidError,
    JwtTokenRevokedError,
    ServiceError,
    SessionExpiredError,
    SessionRevokedError,
    TokenAlreadyConsumedError,
    TokenExpiredError,
    TokenPurposeMismatchError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from pwd301.services.jwt_auth_service import (
    create_token_pair,
    jwt_required,
    refresh_tokens,
    revoke_all_user_tokens,
    revoke_token,
    verify_access_token,
)
from pwd301.services.session_auth_service import (
    create_auth_session,
    hash_session_key,
    revoke_all_user_sessions,
    revoke_auth_session,
    validate_auth_session,
    verify_auth_session_or_raise,
)
from pwd301.services.user_service import (
    change_password,
    get_user_by_email,
    get_user_by_id,
    get_user_by_public_id,
    mark_email_verified,
    normalize_email,
    register_user,
    set_password,
    suspend_user,
    update_profile,
    validate_password,
    verify_password,
)

__all__ = [
    # Exceptions
    "ServiceError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "InvalidEmailError",
    "InvalidPasswordError",
    "AccountNotActiveError",
    "InvalidTokenError",
    "TokenExpiredError",
    "TokenAlreadyConsumedError",
    "TokenPurposeMismatchError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "SessionExpiredError",
    "SessionRevokedError",
    "JwtTokenInvalidError",
    "JwtTokenExpiredError",
    "JwtTokenRevokedError",
    "AuthVersionMismatchError",
    # User Service
    "normalize_email",
    "validate_password",
    "register_user",
    "get_user_by_id",
    "get_user_by_public_id",
    "get_user_by_email",
    "verify_password",
    "change_password",
    "set_password",
    "suspend_user",
    "update_profile",
    "mark_email_verified",
    # Auth Token Service
    "SecurityTokenPurpose",
    "hash_token",
    "create_security_token",
    "verify_security_token",
    "consume_security_token",
    "verify_email_with_token",
    "reset_password_with_token",
    "apply_email_change_with_token",
    # Session Auth Service
    "hash_session_key",
    "create_auth_session",
    "validate_auth_session",
    "verify_auth_session_or_raise",
    "revoke_auth_session",
    "revoke_all_user_sessions",
    # JWT Auth Service
    "create_token_pair",
    "refresh_tokens",
    "verify_access_token",
    "revoke_token",
    "revoke_all_user_tokens",
    "jwt_required",
]
